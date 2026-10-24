from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class TransactionEvent(Base):
    """Every transaction that entered the pipeline (clean or suspicious)."""

    __tablename__ = "transaction_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tx_id: Mapped[str] = mapped_column(String(32), index=True)
    user_id: Mapped[str] = mapped_column(String(16), index=True)
    receiver_id: Mapped[str] = mapped_column(String(16), default="")
    amount: Mapped[float] = mapped_column(Float)
    country: Mapped[str] = mapped_column(String(8), default="")
    device_id: Mapped[str] = mapped_column(String(16), default="")
    merchant_category: Mapped[str] = mapped_column(String(32), default="")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    prefilter_risk: Mapped[float] = mapped_column(Float, default=0.0)
    # clean | investigating | allow | review | block
    status: Mapped[str] = mapped_column(String(16), default="clean")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Investigation(Base):
    """Full agent investigation result, including the reasoning trace."""

    __tablename__ = "investigations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tx_id: Mapped[str] = mapped_column(String(32), index=True)
    user_id: Mapped[str] = mapped_column(String(16), index=True)
    amount: Mapped[float] = mapped_column(Float)
    fraud_score: Mapped[float] = mapped_column(Float)
    confidence: Mapped[str] = mapped_column(String(8))
    action: Mapped[str] = mapped_column(String(16))
    reasons: Mapped[str] = mapped_column(Text)          # JSON list[str]
    reasoning_log: Mapped[str] = mapped_column(Text)    # JSON list[step]
    explanation: Mapped[str] = mapped_column(Text)
    engine: Mapped[str] = mapped_column(String(16), default="rules")  # claude | rules
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
