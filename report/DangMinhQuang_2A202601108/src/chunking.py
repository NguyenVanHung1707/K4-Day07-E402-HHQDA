from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if overlap < 0:
            raise ValueError("overlap must be greater than or equal to 0")
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        # TODO: split into sentences, group into chunks
        if not text or not text.strip():
            return []

        sentences = re.split(
            r"(?<=[.!?])(?:\s+|\n+)",
            text.strip()
        )

        sentences = [
            sentence.strip()
            for sentence in sentences
            if sentence.strip()
        ]

        chunks: list[str] = []

        for start in range(
            0,
            len(sentences),
            self.max_sentences_per_chunk
        ):
            group = sentences[
                start:start + self.max_sentences_per_chunk
            ]

            chunks.append(" ".join(group))

        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        return self._split(text.strip(), list(self.separators))

    def _split(self,current_text: str,remaining_separators: list[str]) -> list[str]:
        # Văn bản đã đủ nhỏ
        if len(current_text) <= self.chunk_size:
            return [current_text]

        # Không còn separator: cắt cứng
        if not remaining_separators:
            return [
                current_text[start:start + self.chunk_size]
                for start in range(
                    0,
                    len(current_text),
                    self.chunk_size
                )
            ]

        separator = remaining_separators[0]
        next_separators = remaining_separators[1:]

        if separator == "":
            parts = list(current_text)
        else:
            parts = current_text.split(separator)

        # Separator hiện tại không xuất hiện trong text
        if len(parts) == 1:
            return self._split(
                current_text,
                next_separators
            )

        chunks: list[str] = []
        current_chunk = ""

        for part in parts:
            part = part.strip()

            if not part:
                continue

            if current_chunk:
                candidate = (
                    current_chunk
                    + separator
                    + part
                )
            else:
                candidate = part

            if len(candidate) <= self.chunk_size:
                current_chunk = candidate
                continue

            if current_chunk:
                chunks.append(current_chunk)

            if len(part) > self.chunk_size:
                smaller_chunks = self._split(
                    part,
                    next_separators
                )
                chunks.extend(smaller_chunks)
                current_chunk = ""
            else:
                current_chunk = part

        if current_chunk:
            chunks.append(current_chunk)

        return chunks


class FAQPairChunker:
    """Split Markdown documents into complete FAQ question-answer chunks."""

    FAQ_BOUNDARY = re.compile(
        r"(?=^(?:(?:#{1,6}\s*)?Q\d+\s*:|##\s+))",
        flags=re.MULTILINE | re.IGNORECASE,
    )

    def __init__(self, min_length: int = 1) -> None:
        if min_length < 0:
            raise ValueError("min_length must be greater than or equal to 0")
        self.min_length = min_length

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        cleaned_text = text.strip()
        parts = [part.strip() for part in self.FAQ_BOUNDARY.split(cleaned_text)]
        non_empty_parts = [part for part in parts if part]
        if not non_empty_parts:
            return []

        # Never discard a short FAQ. Attach it to the preceding chunk (or the
        # following chunk when it appears first) so all source text remains
        # searchable even when a custom minimum length is requested.
        chunks: list[str] = []
        pending_prefix = ""
        for part in non_empty_parts:
            if len(part) < self.min_length:
                if chunks:
                    chunks[-1] = f"{chunks[-1]}\n\n{part}"
                else:
                    pending_prefix = f"{pending_prefix}\n\n{part}".strip()
                continue

            if pending_prefix:
                part = f"{pending_prefix}\n\n{part}"
                pending_prefix = ""
            chunks.append(part)

        if pending_prefix:
            chunks.append(pending_prefix)
        return chunks

def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float],vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    if len(vec_a) != len(vec_b):
        raise ValueError(
            "Hai vector phải có cùng số chiều"
        )

    dot_product = _dot(vec_a, vec_b)

    magnitude_a = math.sqrt(
        sum(value * value for value in vec_a)
    )

    magnitude_b = math.sqrt(
        sum(value * value for value in vec_b)
    )

    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0

    return dot_product / (
        magnitude_a * magnitude_b
    )


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self,text: str,chunk_size: int = 200) -> dict:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")

        if not text or not text.strip():
            return {}

        strategies = {
            "fixed_size": FixedSizeChunker(
                chunk_size=chunk_size
            ),
            "by_sentences": SentenceChunker(
                max_sentences_per_chunk=3
            ),
            "recursive": RecursiveChunker(
                chunk_size=chunk_size
            ),
            "faq_pair": FAQPairChunker(),
        }

        comparison: dict = {}

        for strategy_name, chunker in strategies.items():
            chunks = chunker.chunk(text)

            chunk_lengths = [
                len(chunk)
                for chunk in chunks
            ]

            comparison[strategy_name] = {
                "chunks": chunks,
                "count": len(chunks),
                "chunk_lengths": chunk_lengths,
                "min_chunk_length": (
                    min(chunk_lengths)
                    if chunk_lengths
                    else 0
                ),
                "max_chunk_length": (
                    max(chunk_lengths)
                    if chunk_lengths
                    else 0
                ),
                "avg_length": (
                    sum(chunk_lengths) / len(chunk_lengths)
                    if chunk_lengths
                    else 0.0
                ),
            }

        return comparison
