"""Embedding providers used by semantic evaluators."""

from __future__ import annotations

import asyncio
import hashlib
import math
from typing import Any, Protocol, cast

import numpy as np


class EmbeddingProvider(Protocol):
    """Protocol for text embedding providers."""

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed each supplied text into a numeric vector."""


class SentenceTransformerEmbeddingProvider:
    """Local sentence-transformers embedding provider."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self._model: Any | None = None

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed texts with sentence-transformers without blocking the event loop."""

        return await asyncio.to_thread(self._embed_sync, texts)

    def _embed_sync(self, texts: list[str]) -> list[list[float]]:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        model = cast(Any, self._model)
        vectors = model.encode(texts, normalize_embeddings=True)
        array = np.asarray(vectors, dtype=float)
        return cast(list[list[float]], array.tolist())


class DeterministicEmbeddingProvider:
    """Fast deterministic embedding provider for unit tests."""

    def __init__(self, dimensions: int = 64) -> None:
        self.dimensions = dimensions

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed text into deterministic hashed bag-of-words vectors."""

        return [self._embed_text(text) for text in texts]

    def _embed_text(self, text: str) -> list[float]:
        vector = [0.0 for _ in range(self.dimensions)]
        for token in self._tokens(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            vector[index] += 1.0
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    def _tokens(self, text: str) -> list[str]:
        return [
            token.strip(".,:;!?()[]{}\"'").lower()
            for token in text.split()
            if token.strip(".,:;!?()[]{}\"'")
        ]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Compute cosine similarity clamped into the canonical score range."""

    if left == right:
        return 1.0
    if not left or not right:
        return 0.0
    numerator = sum(
        left_value * right_value for left_value, right_value in zip(left, right, strict=False)
    )
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return round(max(0.0, min(1.0, numerator / (left_norm * right_norm))), 4)
