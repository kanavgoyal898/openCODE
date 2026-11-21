"""Database construction and request-scoped sessions."""

from __future__ import annotations

from collections.abc import Iterator
from weakref import WeakSet

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from opencode_api.models import Base

_SQLITE_CONFIGURED: WeakSet[Engine] = WeakSet()


def build_engine(url: str) -> Engine:
    engine = create_engine(url, pool_pre_ping=True)
    enable_sqlite_foreign_keys(engine)
    return engine


def enable_sqlite_foreign_keys(engine: Engine) -> None:
    if engine.dialect.name != "sqlite" or engine in _SQLITE_CONFIGURED:
        return

    @event.listens_for(engine, "connect")
    def _foreign_keys(connection: object, _: object) -> None:
        cursor = connection.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    _SQLITE_CONFIGURED.add(engine)


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(engine, expire_on_commit=False)


def create_schema(engine: Engine) -> None:
    Base.metadata.create_all(engine)


def session_dependency(factory: sessionmaker[Session]) -> Iterator[Session]:
    with factory() as session:
        yield session
