"""Text embeddings for the fraud-case knowledge base.

Uses fastembed (ONNX MiniLM) when installed; otherwise falls back to a
deterministic hashed bag-of-words + character-trigram embedder that needs
nothing beyond numpy. The fallback keeps the whole pipeline runnable
offline while preserving the same vector-search interface.
"""

from __future__ import annotations

import hashlib
import math
import re

import numpy as np

DIM = 512


class HashedEmbedder:
    """Deterministic local embedder: hashed word + char-trigram features."""

    dim = DIM

    @staticmethod
    def _bucket(token: str) -> int:
        return int(hashlib.md5(token.encode("utf-8")).hexdigest()[:8], 16) % DIM

    def _embed_one(self, text: str) -> np.ndarray:
        vec = np.zeros(DIM, dtype=np.float32)
        words = re.findall(r"[a-z0-9]+", text.lower())
        for w in words:
            vec[self._bucket("w:" + w)] += 1.0
            for i in range(len(w) - 2):
                vec[self._bucket("t:" + w[i:i + 3])] += 0.5
        norm = math.sqrt(float((vec * vec).sum()))
        if norm > 0:
            vec /= norm
        return vec

    def embed(self, texts: list[str]) -> np.ndarray:
        return np.stack([self._embed_one(t) for t in texts])


class FastEmbedEmbedder:
    """Semantic embeddings via fastembed (BAAI/bge-small-en-v1.5, 384-dim)."""

    def __init__(self):
        from fastembed import TextEmbedding  # noqa: F401 — optional dependency

        self._model = TextEmbedding("BAAI/bge-small-en-v1.5")
        self.dim = 384

    def embed(self, texts: list[str]) -> np.ndarray:
        vectors = np.stack([np.asarray(v, dtype=np.float32) for v in self._model.embed(texts)])
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return vectors / norms


def get_embedder():
    try:
        embedder = FastEmbedEmbedder()
        print("[rag] using fastembed semantic embeddings")
        return embedder
    except Exception:
        print("[rag] fastembed unavailable — using local hashed embeddings")
        return HashedEmbedder()
