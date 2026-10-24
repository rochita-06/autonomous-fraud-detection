"""Rebuild the FAISS vector index from data/fraud_cases.csv.

Run this any time fraud_cases.csv changes outside of ingest_cases.py (e.g.
after a manual edit, or a bulk load from a data warehouse export). The
running API picks up a freshly built index on next restart; ingest_cases.py
calls rebuild_index() in-process so no restart is needed there.

Usage:
    python scripts/update_index.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))


def rebuild_index() -> int:
    """Force a fresh CaseStore build (bypassing any cached singleton) and
    return the number of cases indexed. Safe to call repeatedly.
    """
    import app.rag.store as store_module

    store_module._store = None  # drop the cached singleton so _load() reruns
    store = store_module.get_store()
    return len(store.cases)


def main() -> None:
    start = time.perf_counter()
    count = rebuild_index()
    elapsed = time.perf_counter() - start
    print(f"Rebuilt FAISS index: {count} cases in {elapsed:.2f}s")


if __name__ == "__main__":
    main()
