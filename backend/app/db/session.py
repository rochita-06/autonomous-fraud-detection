from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..config import settings
from .models import Base

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db():
    """Create tables for local/dev SQLite. In Postgres (or any prod env),
    schema is managed by Alembic — run `alembic upgrade head` instead, so
    this is a no-op there to avoid drifting from migration history.
    """
    if settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
