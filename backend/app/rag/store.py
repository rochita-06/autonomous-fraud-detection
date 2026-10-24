"""FAISS-backed vector store over the fraud-case knowledge base."""

from __future__ import annotations

import csv

import numpy as np

from ..config import settings
from .embeddings import get_embedder


class CaseStore:
    def __init__(self):
        self.embedder = get_embedder()
        self.cases: list[dict] = []
        self._index = None
        self._matrix: np.ndarray | None = None
        self._load()

    def _load(self):
        path = settings.data_dir / "fraud_cases.csv"
        with open(path, newline="", encoding="utf-8") as f:
            self.cases = list(csv.DictReader(f))

        texts = [f"{c['fraud_type']}. {c['pattern']}. {c['description']}" for c in self.cases]
        vectors = self.embedder.embed(texts).astype(np.float32)

        try:
            import faiss

            index = faiss.IndexFlatIP(vectors.shape[1])  # cosine (vectors are normalized)
            index.add(vectors)
            self._index = index
            print(f"[rag] FAISS index built with {len(self.cases)} cases")
        except Exception:
            self._matrix = vectors
            print(f"[rag] faiss unavailable — numpy cosine search over {len(self.cases)} cases")

    def search(self, query: str, k: int = 3) -> list[dict]:
        q = self.embedder.embed([query]).astype(np.float32)
        if self._index is not None:
            scores, ids = self._index.search(q, k)
            pairs = zip(ids[0].tolist(), scores[0].tolist())
        else:
            sims = (self._matrix @ q[0]).tolist()
            order = np.argsort(sims)[::-1][:k]
            pairs = [(int(i), float(sims[i])) for i in order]

        results = []
        for idx, score in pairs:
            if idx < 0:
                continue
            case = self.cases[idx]
            results.append({
                "case_id": case["case_id"],
                "fraud_type": case["fraud_type"],
                "pattern": case["pattern"],
                "description": case["description"],
                "similarity": round(float(score), 4),
            })
        return results


_store: CaseStore | None = None


def get_store() -> CaseStore:
    global _store
    if _store is None:
        _store = CaseStore()
    return _store
