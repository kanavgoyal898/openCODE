"""PostgreSQL-backed polling worker for durable queued scans."""

from __future__ import annotations

import os
import signal
import time

from opencode_api.db import build_engine, build_session_factory
from opencode_api.models import ScanJobModel
from sqlalchemy import select

from opencode_worker.tasks import process_scan

_running = True


def _stop(_: int, __: object) -> None:
    global _running
    _running = False


def run_once(database_url: str) -> int:
    factory = build_session_factory(build_engine(database_url))
    with factory() as session:
        identifiers = tuple(
            session.scalars(
                select(ScanJobModel.id)
                .where(ScanJobModel.status == "queued")
                .order_by(ScanJobModel.created_at)
                .limit(10)
            )
        )
    for identifier in identifiers:
        process_scan(factory, identifier)
    return len(identifiers)


def main() -> None:
    database_url = os.environ.get(
        "OPENCODE_DATABASE_URL",
        "postgresql+psycopg://opencode:opencode@localhost:5432/opencode",
    )
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    while _running:
        processed = run_once(database_url)
        if processed == 0:
            time.sleep(2)


if __name__ == "__main__":
    main()
