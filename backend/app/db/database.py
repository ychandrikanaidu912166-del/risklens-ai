"""SQLite / SQLAlchemy setup."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from backend.app.config import get_settings

_settings = get_settings()

_engine = create_engine(
    _settings.db_url,
    connect_args={"check_same_thread": False} if _settings.db_url.startswith("sqlite") else {},
    future=True,
)


@event.listens_for(_engine, "connect")
def _sqlite_pragma(dbapi_connection, connection_record):  # type: ignore[no-untyped-def]
    if _settings.db_url.startswith("sqlite"):
        cur = dbapi_connection.cursor()
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute("PRAGMA foreign_keys=ON;")
        cur.close()


SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_engine():
    return _engine


@contextmanager
def session_scope() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from backend.app.db import models  # noqa: F401  (register models)

    Base.metadata.create_all(bind=_engine)
