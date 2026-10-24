from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..agents.explain import format_explanation
from ..agents.investigator import investigate
from ..core.security import require_api_key, verify_webhook_signature
from ..db.models import Investigation, TransactionEvent
from ..db.session import get_db
from ..graph.client import get_graph

# /health has no auth — safe for load balancers / container healthchecks.
public_router = APIRouter()
# Every other route requires X-API-Key (no-op in dev when API_KEY is unset).
router = APIRouter(dependencies=[Depends(require_api_key)])


class TransactionIn(BaseModel):
    tx_id: str = Field(default_factory=lambda: f"TX-{uuid.uuid4().hex[:8].upper()}")
    user_id: str
    receiver_id: str = ""
    amount: float
    currency: str = "USD"
    country: str = ""
    device_id: str = ""
    merchant_category: str = ""
    timestamp: str = ""
    prefilter_risk: float = 0.0


def _record_event(db: Session, tx: TransactionIn, status: str) -> TransactionEvent:
    ts = None
    if tx.timestamp:
        try:
            ts = datetime.fromisoformat(tx.timestamp.replace("Z", "+00:00"))
        except ValueError:
            ts = None
    event = TransactionEvent(
        tx_id=tx.tx_id, user_id=tx.user_id, receiver_id=tx.receiver_id,
        amount=tx.amount, country=tx.country, device_id=tx.device_id,
        merchant_category=tx.merchant_category,
        timestamp=ts or datetime.now(timezone.utc),
        prefilter_risk=tx.prefilter_risk, status=status,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@public_router.get("/health")
def health():
    """Unauthenticated liveness probe — safe to expose to load balancers."""
    return {"status": "ok", "graph_backend": get_graph().backend}


@router.post("/transactions", dependencies=[Depends(verify_webhook_signature)])
def record_transaction(tx: TransactionIn, db: Session = Depends(get_db)):
    """Low-risk transactions from the n8n pre-filter — recorded, not investigated.

    Protected by X-API-Key plus an optional HMAC X-Webhook-Signature so this
    ingestion path can't be hit by anyone who isn't the automation pipeline.
    """
    event = _record_event(db, tx, status="clean")
    get_graph().record_transaction(
        tx.user_id, receiver_id=tx.receiver_id, device_id=tx.device_id,
        amount=tx.amount, flagged=False,
    )
    return {"tx_id": event.tx_id, "status": "clean"}


@router.post("/investigate", dependencies=[Depends(verify_webhook_signature)])
def investigate_transaction(tx: TransactionIn, db: Session = Depends(get_db)):
    """Run the autonomous agent on a suspicious transaction."""
    event = _record_event(db, tx, status="investigating")

    result = investigate(tx.model_dump())
    decision = result["decision"]
    explanation = format_explanation(decision)

    event.status = decision["action"]
    get_graph().record_transaction(
        tx.user_id, receiver_id=tx.receiver_id, device_id=tx.device_id,
        amount=tx.amount, flagged=(decision["action"] == "block"),
    )
    inv = Investigation(
        tx_id=tx.tx_id, user_id=tx.user_id, amount=tx.amount,
        fraud_score=decision["fraud_score"], confidence=decision["confidence"],
        action=decision["action"],
        reasons=json.dumps(decision["reasons"]),
        reasoning_log=json.dumps(result["reasoning_log"], default=str),
        explanation=explanation, engine=result["engine"],
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)

    return {
        "tx_id": tx.tx_id,
        "user_id": tx.user_id,
        "amount": tx.amount,
        "fraud_score": decision["fraud_score"],
        "confidence": decision["confidence"],
        "action": decision["action"],
        "reasons": decision["reasons"],
        "summary": decision.get("summary", ""),
        "explanation": explanation,
        "engine": result["engine"],
        "reasoning_log": result["reasoning_log"],
        "investigation_id": inv.id,
    }


@router.get("/transactions/feed")
def transaction_feed(limit: int = 50, db: Session = Depends(get_db)):
    rows = (
        db.query(TransactionEvent)
        .order_by(TransactionEvent.id.desc())
        .limit(min(limit, 200))
        .all()
    )
    return [{
        "tx_id": r.tx_id, "user_id": r.user_id, "receiver_id": r.receiver_id,
        "amount": r.amount, "country": r.country, "device_id": r.device_id,
        "merchant_category": r.merchant_category, "status": r.status,
        "prefilter_risk": r.prefilter_risk,
        "created_at": r.created_at.isoformat(),
    } for r in rows]


@router.get("/investigations")
def list_investigations(limit: int = 25, db: Session = Depends(get_db)):
    rows = (
        db.query(Investigation)
        .order_by(Investigation.id.desc())
        .limit(min(limit, 100))
        .all()
    )
    return [{
        "id": r.id, "tx_id": r.tx_id, "user_id": r.user_id, "amount": r.amount,
        "fraud_score": r.fraud_score, "confidence": r.confidence, "action": r.action,
        "reasons": json.loads(r.reasons), "explanation": r.explanation,
        "engine": r.engine, "created_at": r.created_at.isoformat(),
    } for r in rows]


@router.get("/investigations/{inv_id}")
def get_investigation(inv_id: int, db: Session = Depends(get_db)):
    r = db.get(Investigation, inv_id)
    if r is None:
        return {"error": "not found"}
    return {
        "id": r.id, "tx_id": r.tx_id, "user_id": r.user_id, "amount": r.amount,
        "fraud_score": r.fraud_score, "confidence": r.confidence, "action": r.action,
        "reasons": json.loads(r.reasons), "explanation": r.explanation,
        "engine": r.engine, "reasoning_log": json.loads(r.reasoning_log),
        "created_at": r.created_at.isoformat(),
    }


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    total = db.query(func.count(TransactionEvent.id)).scalar() or 0
    investigated = db.query(func.count(Investigation.id)).scalar() or 0
    blocked = (
        db.query(func.count(Investigation.id))
        .filter(Investigation.action == "block").scalar() or 0
    )
    review = (
        db.query(func.count(Investigation.id))
        .filter(Investigation.action == "review").scalar() or 0
    )
    avg_score = db.query(func.avg(Investigation.fraud_score)).scalar()
    return {
        "total_transactions": total,
        "investigated": investigated,
        "blocked": blocked,
        "under_review": review,
        "avg_fraud_score": round(float(avg_score), 3) if avg_score is not None else 0.0,
    }


@router.get("/graph/{user_id}")
def user_subgraph(user_id: str):
    return get_graph().subgraph(user_id)
