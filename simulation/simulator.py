"""Real-time transaction simulator.

Streams synthetic transactions to the pipeline every few seconds. Roughly
1 in 6 transactions is crafted to look fraudulent (huge amount, odd hour,
high-risk category, fraud-ring receiver / shared device).

Usage:
    python simulator.py                          # -> n8n webhook (default)
    python simulator.py --target backend         # -> FastAPI directly
    python simulator.py --interval 3 --count 20
"""

from __future__ import annotations

import argparse
import csv
import random
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
N8N_URL = "http://localhost:5678/webhook/transaction"
BACKEND_INVESTIGATE = "http://localhost:8000/investigate"
BACKEND_RECORD = "http://localhost:8000/transactions"

RING_USERS = ["U050", "U051", "U052", "U053", "U054", "U055"]
SHARED_RING_DEVICES = ["D666", "D667"]


def load_users() -> list[dict]:
    with open(DATA_DIR / "users.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def make_transaction(users: list[dict]) -> tuple[dict, bool]:
    sender = random.choice(users)
    fraudulent = random.random() < 0.18

    if fraudulent:
        amount = round(float(sender["avg_tx_amount"]) * random.uniform(5, 14), 2)
        tx = {
            "user_id": sender["user_id"],
            "receiver_id": random.choice(RING_USERS),
            "amount": amount,
            "country": random.choice([c for c in ["IN", "US", "GB", "SG", "AE"] if c != sender["country"]]),
            "device_id": random.choice(SHARED_RING_DEVICES),
            "merchant_category": random.choice(["crypto_exchange", "gift_cards", "electronics"]),
        }
    else:
        amount = round(max(2.0, random.gauss(float(sender["avg_tx_amount"]), float(sender["avg_tx_amount"]) * 0.3)), 2)
        tx = {
            "user_id": sender["user_id"],
            "receiver_id": random.choice(users)["user_id"],
            "amount": amount,
            "country": sender["country"],
            "device_id": f"D{random.randint(1, 100):03d}",
            "merchant_category": random.choice(["groceries", "dining", "utilities", "fashion", "fuel"]),
        }

    tx.update({
        "tx_id": f"TX-{uuid.uuid4().hex[:8].upper()}",
        "currency": "USD",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    return tx, fraudulent


def prefilter_risk(tx: dict) -> float:
    """Mirror of the n8n pre-filter, used when posting directly to the backend."""
    risk = 0.0
    if tx["amount"] > 1000:
        risk += 0.4
    elif tx["amount"] > 500:
        risk += 0.25
    hour = datetime.fromisoformat(tx["timestamp"]).hour
    if hour <= 5 or hour == 23:
        risk += 0.2
    if tx["merchant_category"] in ("crypto_exchange", "gift_cards"):
        risk += 0.25
    if tx["amount"] >= 500 and tx["amount"] % 100 == 0:
        risk += 0.1
    return min(risk, 1.0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=["n8n", "backend"], default="n8n")
    parser.add_argument("--interval", type=float, default=3.0, help="seconds between transactions")
    parser.add_argument("--count", type=int, default=0, help="0 = run forever")
    args = parser.parse_args()

    users = load_users()
    sent = 0
    print(f"Streaming transactions to {args.target} every {args.interval}s (Ctrl+C to stop)")

    while args.count == 0 or sent < args.count:
        tx, crafted_fraud = make_transaction(users)
        try:
            if args.target == "n8n":
                resp = requests.post(N8N_URL, json=tx, timeout=120)
                info = f"-> n8n {resp.status_code}"
            else:
                tx["prefilter_risk"] = prefilter_risk(tx)
                if tx["prefilter_risk"] >= 0.3:
                    resp = requests.post(BACKEND_INVESTIGATE, json=tx, timeout=300)
                    body = resp.json()
                    info = f"-> INVESTIGATED score={body.get('fraud_score')} action={body.get('action')}"
                else:
                    requests.post(BACKEND_RECORD, json=tx, timeout=30)
                    info = "-> recorded (clean)"
        except requests.RequestException as e:
            info = f"!! {type(e).__name__}: {e}"

        tag = "FRAUD-LIKE" if crafted_fraud else "normal    "
        print(f"[{tag}] {tx['tx_id']} {tx['user_id']} ${tx['amount']:<9} {tx['merchant_category']:<16} {info}")
        sent += 1
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
