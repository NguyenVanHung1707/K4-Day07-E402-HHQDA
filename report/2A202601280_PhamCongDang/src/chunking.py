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
        if not text:
            return []

        # Split on sentence-ending punctuation while keeping it attached
        # to the sentence that precedes it.
        parts = re.split(r"([.!?])", text)

        sentences: list[str] = []
        current = ""
        for part in parts:
            if part in (".", "!", "?"):
                current += part
                sentence = current.strip()
                if sentence:
                    sentences.append(sentence)
                current = ""
            else:
                current += part
        trailing = current.strip()
        if trailing:
            sentences.append(trailing)

        chunks: list[str] = []
        step = self.max_sentences_per_chunk
        for start in range(0, len(sentences), step):
            group = sentences[start : start + step]
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
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        raw_chunks = self._split(text, self.separators)
        return [c.strip() for c in raw_chunks if c.strip()]

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        # Base case 1: already small enough.
        if len(current_text) <= self.chunk_size:
            return [current_text]

        # Base case 2: no more (or empty) separators left -> fixed-size cut.
        if not remaining_separators or remaining_separators[0] == "":
            return [
                current_text[i : i + self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
            ]

        separator = remaining_separators[0]
        next_separators = remaining_separators[1:]
        parts = current_text.split(separator)

        chunks: list[str] = []
        buffer = ""
        for part in parts:
            candidate = part if not buffer else buffer + separator + part
            if len(candidate) <= self.chunk_size:
                buffer = candidate
                continue

            # Flush whatever fit so far.
            if buffer:
                chunks.append(buffer)
                buffer = ""

            if len(part) <= self.chunk_size:
                buffer = part
            else:
                # This single piece is still too long: recurse with a
                # lower-priority separator instead of the current one.
                chunks.extend(self._split(part, next_separators))

        if buffer:
            chunks.append(buffer)

        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=0).chunk(text),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3).chunk(text),
            "recursive": RecursiveChunker(chunk_size=chunk_size).chunk(text),
        }

        result: dict = {}
        for name, chunks in strategies.items():
            count = len(chunks)
            avg_length = (sum(len(c) for c in chunks) / count) if count else 0.0
            result[name] = {
                "count": count,
                "avg_length": avg_length,
                "chunks": chunks,
            }
        return result
