from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot, compute_similarity
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

    def _make_record(self, doc: Document) -> dict[str, Any]:
        self._next_index += 1
        embedding = self._embedding_fn(doc.content)
        metadata = dict(doc.metadata) if doc.metadata else {}
        doc_id = metadata.get("doc_id", doc.id)
        return {
            "id": doc.id,
            "doc_id": doc_id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": embedding,
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if not records:
            return []
        query_vec = self._embedding_fn(query)
        scored_records = []
        for r in records:
            score = compute_similarity(query_vec, r["embedding"])
            record_copy = {
                "id": r["id"],
                "doc_id": r.get("doc_id", r["id"]),
                "content": r["content"],
                "metadata": r.get("metadata", {}),
                "embedding": r["embedding"],
                "score": score,
            }
            scored_records.append(record_copy)

        scored_records.sort(key=lambda x: x["score"], reverse=True)
        return scored_records[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.
        """
        for doc in docs:
            record = self._make_record(doc)
            self._store.append(record)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.
        """
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            return self.search(query, top_k=top_k)

        filtered_records = []
        for record in self._store:
            rec_meta = record.get("metadata", {})
            match = True
            for k, v in metadata_filter.items():
                if rec_meta.get(k) != v:
                    match = False
                    break
            if match:
                filtered_records.append(record)

        return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        initial_count = len(self._store)
        self._store = [
            r for r in self._store
            if r.get("doc_id") != doc_id
            and r.get("id") != doc_id
            and r.get("metadata", {}).get("doc_id") != doc_id
        ]
        return len(self._store) < initial_count

