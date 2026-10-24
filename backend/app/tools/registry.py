"""Investigation tools the agent can call.

Each tool returns structured JSON. The same registry serves both engines:
the Claude agent receives TOOL_SPECS as its tool definitions, and the
rule-based fallback calls execute_tool() directly.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import lru_cache

import pandas as pd

from ..config import settings
from ..db.models import TransactionEvent
from ..db.session import SessionLocal
from ..graph.client import get_graph
from ..rag.store import get_store


@lru_cache(maxsize=1)
def _users_df() -> pd.DataFrame:
    return pd.read_csv(settings.data_dir / "users.csv", dtype={"user_id": str})


@lru_cache(maxsize=1)
def _tx_df() -> pd.DataFrame:
    df = pd.read_csv(settings.data_dir / "transactions.csv")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def get_user_history(user_id: str) -> dict:
    """Aggregate the user's historical transaction behaviour."""
    users = _users_df()
    row = users[users["user_id"] == user_id]
    if row.empty:
        return {"user_id": user_id, "found": False,
                "note": "unknown user — no history on file, treat as elevated risk"}
    profile = row.iloc[0]

    txs = _tx_df()
    sent = txs[txs["sender_id"] == user_id]
    history = {
        "user_id": user_id,
        "found": True,
        "country": profile["country"],
        "signup_date": profile["signup_date"],
        "is_flagged": bool(profile["is_flagged"]),
        "tx_count_90d": int(len(sent)),
        "avg_amount": round(float(sent["amount"].mean()), 2) if len(sent) else float(profile["avg_tx_amount"]),
        "max_amount": round(float(sent["amount"].max()), 2) if len(sent) else 0.0,
        "usual_countries": sorted(sent["country"].unique().tolist()) if len(sent) else [profile["country"]],
        "usual_categories": sent["merchant_category"].value_counts().head(3).index.tolist() if len(sent) else [],
        "prior_fraud_labels": int(sent["label"].sum()) if len(sent) else 0,
    }
    return history


def check_transaction_pattern(tx: dict) -> dict:
    """Compare a live transaction against the sender's behavioural baseline."""
    user_id = tx.get("user_id", "")
    amount = float(tx.get("amount", 0))
    history = get_user_history(user_id)

    anomalies: list[str] = []
    avg = float(history.get("avg_amount") or 0) or 1.0
    ratio = round(amount / avg, 2)
    if ratio >= 3:
        anomalies.append("amount_far_above_average")
    elif ratio >= 1.8:
        anomalies.append("amount_above_average")

    country = tx.get("country") or ""
    usual = history.get("usual_countries", [])
    if country and usual and country not in usual:
        anomalies.append("unusual_country")

    ts_raw = tx.get("timestamp")
    hour = None
    if ts_raw:
        try:
            hour = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00")).hour
        except ValueError:
            hour = None
    if hour is not None and (hour <= 5 or hour == 23):
        anomalies.append("odd_hour")

    category = tx.get("merchant_category") or ""
    if category in ("crypto_exchange", "gift_cards"):
        anomalies.append("high_risk_category")

    if amount >= 500 and amount % 100 == 0:
        anomalies.append("round_amount")

    # Velocity: how many transactions has this user pushed through the live
    # pipeline in the last 10 minutes?
    with SessionLocal() as db:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=10)
        recent = (
            db.query(TransactionEvent)
            .filter(TransactionEvent.user_id == user_id,
                    TransactionEvent.created_at >= cutoff)
            .count()
        )
    if recent >= 4:
        anomalies.append("high_velocity")

    return {
        "tx_id": tx.get("tx_id"),
        "user_id": user_id,
        "amount": amount,
        "amount_ratio_vs_avg": ratio,
        "user_avg_amount": round(avg, 2),
        "hour": hour,
        "recent_tx_count_10min": recent,
        "anomalies": anomalies,
        "anomaly_count": len(anomalies),
    }


def get_linked_accounts(user_id: str) -> dict:
    """Query the graph for shared devices, transfer partners and flagged links."""
    return get_graph().linked_accounts(user_id)


def search_similar_cases(query: str) -> dict:
    """Vector-search the fraud-case knowledge base for similar known patterns."""
    return {"query": query, "matches": get_store().search(query, k=3)}


TOOLS = {
    "get_user_history": get_user_history,
    "check_transaction_pattern": check_transaction_pattern,
    "get_linked_accounts": get_linked_accounts,
    "search_similar_cases": search_similar_cases,
}

# Anthropic tool definitions for the Claude-powered agent
TOOL_SPECS = [
    {
        "name": "get_user_history",
        "description": "Get the sender's 90-day behavioural baseline: average/max amounts, usual countries and merchant categories, prior fraud labels, and whether the account is already flagged. Call this first for any investigation.",
        "input_schema": {
            "type": "object",
            "properties": {"user_id": {"type": "string", "description": "Sender account ID, e.g. U012"}},
            "required": ["user_id"],
        },
    },
    {
        "name": "check_transaction_pattern",
        "description": "Compare the live transaction against the sender's baseline. Returns anomaly flags (amount ratio, unusual country, odd hour, high-risk category, velocity).",
        "input_schema": {
            "type": "object",
            "properties": {
                "tx": {
                    "type": "object",
                    "description": "The transaction under investigation, exactly as provided.",
                }
            },
            "required": ["tx"],
        },
    },
    {
        "name": "get_linked_accounts",
        "description": "Query the identity graph: devices this user shares with other accounts, transfer partners, and any connections to already-flagged fraudster accounts within 2 hops.",
        "input_schema": {
            "type": "object",
            "properties": {"user_id": {"type": "string"}},
            "required": ["user_id"],
        },
    },
    {
        "name": "search_similar_cases",
        "description": "Vector-search a knowledge base of known fraud cases. Describe the suspicious behaviour in natural language (e.g. 'large crypto transfer at 3am from shared device') and get the closest known fraud patterns with similarity scores.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Natural-language description of the suspicious behaviour"}},
            "required": ["query"],
        },
    },
]


def execute_tool(name: str, tool_input: dict) -> dict:
    fn = TOOLS.get(name)
    if fn is None:
        return {"error": f"unknown tool: {name}"}
    try:
        return fn(**tool_input)
    except TypeError as e:
        return {"error": f"bad arguments for {name}: {e}"}
