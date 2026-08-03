from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb

            self._chroma_client = chromadb.Client()
            try:
                self._chroma_client.delete_collection(name=collection_name)
            except Exception:
                pass
            self._collection = self._chroma_client.get_or_create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        meta = dict(doc.metadata) if doc.metadata is not None else {}
        meta.setdefault("doc_id", doc.id)
        clean_meta = {}
        for k, v in meta.items():
            if v is None:
                continue
            if isinstance(v, (str, int, float, bool)):
                clean_meta[k] = v
            else:
                clean_meta[k] = str(v)
        return {
            "id": doc.id,
            "content": doc.content,
            "embedding": self._embedding_fn(doc.content),
            "metadata": clean_meta
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        from .chunking import compute_similarity
        query_embed = self._embedding_fn(query)
        results = []
        for r in records:
            score = compute_similarity(query_embed, r["embedding"])
            results.append({
                "id": r["id"],
                "content": r["content"],
                "score": score,
                "metadata": r["metadata"]
            })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        if self._use_chroma:
            ids = []
            documents = []
            embeddings = []
            metadatas = []
            for doc in docs:
                self._next_index += 1
                chroma_id = f"{doc.id}##{self._next_index}"
                ids.append(chroma_id)
                documents.append(doc.content)
                embeddings.append(self._embedding_fn(doc.content))
                
                meta = dict(doc.metadata) if doc.metadata is not None else {}
                meta.setdefault("doc_id", doc.id)
                
                clean_meta = {}
                for k, v in meta.items():
                    if v is None:
                        continue
                    if isinstance(v, (str, int, float, bool)):
                        clean_meta[k] = v
                    else:
                        clean_meta[k] = str(v)
                metadatas.append(clean_meta)
                
            self._collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)
        else:
            for doc in docs:
                self._store.append(self._make_record(doc))

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if self._use_chroma:
            from .chunking import compute_similarity
            query_embed = self._embedding_fn(query)
            res = self._collection.query(
                query_embeddings=[query_embed],
                n_results=top_k,
                include=["documents", "metadatas", "embeddings"]
            )
            formatted = []
            if res and "documents" in res and res["documents"]:
                documents = res["documents"][0]
                ids = res["ids"][0]
                metadatas = res["metadatas"][0] if res.get("metadatas") else [{}] * len(documents)
                embeddings = res["embeddings"][0] if res.get("embeddings") else [None] * len(documents)
                for i in range(len(documents)):
                    score = compute_similarity(query_embed, embeddings[i]) if embeddings[i] is not None else 0.0
                    formatted.append({
                        "id": ids[i],
                        "content": documents[i],
                        "score": score,
                        "metadata": metadatas[i] or {}
                    })
                formatted.sort(key=lambda x: x["score"], reverse=True)
            return formatted
        else:
            return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma:
            return self._collection.count()
        else:
            return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            return self.search(query, top_k=top_k)

        if self._use_chroma:
            from .chunking import compute_similarity
            query_embed = self._embedding_fn(query)
            res = self._collection.query(
                query_embeddings=[query_embed],
                n_results=top_k,
                where=metadata_filter,
                include=["documents", "metadatas", "embeddings"]
            )
            formatted = []
            if res and "documents" in res and res["documents"]:
                documents = res["documents"][0]
                ids = res["ids"][0]
                metadatas = res["metadatas"][0] if res.get("metadatas") else [{}] * len(documents)
                embeddings = res["embeddings"][0] if res.get("embeddings") else [None] * len(documents)
                for i in range(len(documents)):
                    score = compute_similarity(query_embed, embeddings[i]) if embeddings[i] is not None else 0.0
                    formatted.append({
                        "id": ids[i],
                        "content": documents[i],
                        "score": score,
                        "metadata": metadatas[i] or {}
                    })
                formatted.sort(key=lambda x: x["score"], reverse=True)
            return formatted
        else:
            filtered_records = []
            for r in self._store:
                meta = r.get("metadata", {})
                match = True
                for k, v in metadata_filter.items():
                    if meta.get(k) != v:
                        match = False
                        break
                if match:
                    filtered_records.append(r)
            return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma:
            count_before = self._collection.count()
            try:
                self._collection.delete(ids=[doc_id])
            except Exception:
                pass
            try:
                self._collection.delete(where={"doc_id": doc_id})
            except Exception:
                pass
            count_after = self._collection.count()
            return count_after < count_before
        else:
            initial_len = len(self._store)
            self._store = [
                r for r in self._store
                if r.get("id") != doc_id and r.get("metadata", {}).get("doc_id") != doc_id
            ]
            return len(self._store) < initial_len
