"""Ingest new fraud cases into the knowledge base.

Appends validated rows to data/fraud_cases.csv (the RAG source-of-truth)
and rebuilds the FAISS index so newly ingested cases are searchable
immediately, without needing to restart the API process.

Usage:
    python scripts/ingest_cases.py --file new_cases.csv
    python scripts/ingest_cases.py --file new_cases.json
    echo '[{"case_id":"C999","fraud_type":"...", "pattern":"...", "description":"..."}]' \\
        | python scripts/ingest_cases.py --stdin

Each case needs: case_id, fraud_type, pattern, description.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.config import settings  # noqa: E402

REQUIRED_FIELDS = ["case_id", "fraud_type", "pattern", "description"]
CASES_PATH = settings.data_dir / "fraud_cases.csv"


def _load_rows(args: argparse.Namespace) -> list[dict]:
    if args.stdin:
        raw = sys.stdin.read()
        return json.loads(raw)
    path = Path(args.file)
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _validate(rows: list[dict]) -> list[dict]:
    clean = []
    for i, row in enumerate(rows):
        missing = [f for f in REQUIRED_FIELDS if not row.get(f)]
        if missing:
            print(f"[skip] row {i}: missing fields {missing}", file=sys.stderr)
            continue
        clean.append({k: str(row[k]).strip() for k in REQUIRED_FIELDS})
    return clean


def ingest(rows: list[dict], dedupe: bool = True) -> int:
    existing: list[dict] = []
    if CASES_PATH.exists():
        with open(CASES_PATH, newline="", encoding="utf-8") as f:
            existing = list(csv.DictReader(f))
    existing_ids = {r["case_id"] for r in existing}

    new_rows = [r for r in rows if not (dedupe and r["case_id"] in existing_ids)]
    if not new_rows:
        print("Nothing new to ingest (all case_ids already present).")
        return 0

    all_rows = existing + new_rows
    with open(CASES_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REQUIRED_FIELDS)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Ingested {len(new_rows)} new case(s) -> {CASES_PATH}")
    return len(new_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", help="CSV or JSON file of new cases")
    parser.add_argument("--stdin", action="store_true", help="Read a JSON array from stdin")
    parser.add_argument("--no-reindex", action="store_true", help="Skip rebuilding the FAISS index")
    args = parser.parse_args()

    if not args.file and not args.stdin:
        parser.error("provide --file or --stdin")

    rows = _validate(_load_rows(args))
    if not rows:
        print("No valid rows to ingest.", file=sys.stderr)
        sys.exit(1)

    added = ingest(rows)
    if added and not args.no_reindex:
        from update_index import rebuild_index  # noqa: E402

        rebuild_index()


if __name__ == "__main__":
    main()
