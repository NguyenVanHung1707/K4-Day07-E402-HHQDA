from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        # 1. Retrieve top-k chunks from the store.
        results = self.store.search(question, top_k=top_k)

        if not results:
            return "Tôi không tìm thấy thông tin phù hợp trong tài liệu để trả lời câu hỏi này."

        # 2. Build numbered context blocks, grounded with doc_id/source.
        context_parts = []
        for idx, res in enumerate(results, 1):
            doc_id = res.get("metadata", {}).get("doc_id", "unknown")
            content = res.get("content", "")
            context_parts.append(f"[{idx}] (Nguồn: {doc_id})\n{content}")
        context_str = "\n\n".join(context_parts)

        # 3. Assemble the RAG prompt.
        prompt = (
            "Hướng dẫn: Chỉ sử dụng thông tin từ ngữ cảnh (Context) bên dưới để trả lời câu hỏi. "
            "Nếu context không đủ thông tin, hãy nói rõ là không thể trả lời dựa trên tài liệu cung cấp.\n\n"
            f"Context:\n{context_str}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )

        # 4. Delegate generation to the injected LLM function.
        return self.llm_fn(prompt)
