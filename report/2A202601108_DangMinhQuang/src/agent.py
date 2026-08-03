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

    def __init__(
        self,
        store: EmbeddingStore,
        llm_fn: Callable[[str], str],
    ) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(
        self,
        question: str,
        top_k: int = 3,
    ) -> str:
        if not question or not question.strip():
            raise ValueError("Question must not be empty")

        if top_k <= 0:
            raise ValueError("top_k must be greater than 0")

        results = self.store.search(
            query=question.strip(),
            top_k=top_k,
        )

        if not results:
            return (
                "I could not find relevant information "
                "in the knowledge base."
            )

        context_parts: list[str] = []

        for index, result in enumerate(results, start=1):
            content = result.get("content", "")
            metadata = result.get("metadata", {})
            score = result.get("score")

            context_part = f"[Context {index}]\n{content}"

            if metadata:
                context_part += f"\nMetadata: {metadata}"

            if score is not None:
                context_part += f"\nSimilarity score: {score:.4f}"

            context_parts.append(context_part)

        context = "\n\n".join(context_parts)

        prompt = f"""
You are a knowledge base assistant.

Answer the user's question using only the information provided
in the context below.

If the context does not contain enough information to answer,
say that you do not have enough information.

Do not invent facts that are not present in the context.

Context:
{context}

Question:
{question.strip()}

Answer:
""".strip()

        return self.llm_fn(prompt)