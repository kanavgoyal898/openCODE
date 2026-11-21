from __future__ import annotations

import logging
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from opencode_api.app import create_app
from opencode_api.hashing import i64_to_u64, u64_to_i64
from opencode_api.identifiers import uuid7
from opencode_api.models import (
    CloneMatchModel,
    DeletionOutboxModel,
    FileRevisionModel,
    FingerprintPostingModel,
    RepositoryModel,
    ScanJobModel,
    SourceFileModel,
)
from sqlalchemy import Engine, create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


def _source() -> str:
    return (
        "def compute(left, right):\n"
        "    first = left + right\n"
        "    second = first * left\n"
        "    third = second - right\n"
        "    fourth = third / (left + 1)\n"
        "    label = 'value'\n"
        "    return fourth, label\n"
    )


def _client(tmp_path: Path, token: str | None = None) -> tuple[TestClient, Engine]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    app = create_app(
        engine=engine, allowed_roots=(tmp_path,), hosted_token=token, expose_source=True
    )
    return TestClient(app), engine


def _repository(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    root.mkdir()
    (root / "one.py").write_text(_source(), encoding="utf-8")
    (root / "two.py").write_text(_source(), encoding="utf-8")
    return root


def test_repository_scan_clone_and_delete_lifecycle(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    client, engine = _client(tmp_path)
    with client:
        created = client.post(
            "/api/v1/repositories",
            headers={"Idempotency-Key": "repository-1"},
            json={"name": "fixture", "localPath": str(root)},
        )
        assert created.status_code == 201
        repository = created.json()
        assert created.headers["X-Request-Id"]
        repeated = client.post(
            "/api/v1/repositories",
            headers={"Idempotency-Key": "repository-1"},
            json={"name": "ignored", "localPath": str(root)},
        )
        assert repeated.json()["id"] == repository["id"]

        listed = client.get("/api/v1/repositories", params={"limit": 1})
        assert listed.status_code == 200
        assert listed.json()["items"][0]["id"] == repository["id"]
        assert client.get(f"/api/v1/repositories/{repository['id']}").status_code == 200

        accepted = client.post(
            "/api/v1/scans",
            headers={"Idempotency-Key": "scan-1"},
            json={"repositoryId": repository["id"]},
        )
        assert accepted.status_code == 202
        scan_id = accepted.json()["id"]
        scan = client.get(f"/api/v1/scans/{scan_id}").json()
        assert scan["status"] == "completed"
        assert scan["counts"]["files"] == 2
        assert scan["counts"]["clones"] == 1

        clones = client.get("/api/v1/clones", params={"scan": scan_id}).json()
        assert len(clones["items"]) == 1
        clone_id = clones["items"][0]["id"]
        detail = client.get(f"/api/v1/clones/{clone_id}")
        assert detail.status_code == 200
        assert detail.json()["evidence_state"] == "verified"
        assert detail.json()["leftSource"] == _source()
        assert detail.json()["rightSource"] == _source()

        (root / "two.py").write_text("value = 1\n", encoding="utf-8")
        second_scan = client.post(
            "/api/v1/scans",
            headers={"Idempotency-Key": "scan-2"},
            json={"repositoryId": repository["id"]},
        )
        assert second_scan.status_code == 202
        second_state = client.get(f"/api/v1/scans/{second_scan.json()['id']}").json()
        assert second_state["status"] == "completed"
        with Session(engine) as session:
            assert session.scalar(select(func.count()).select_from(SourceFileModel)) == 2
            assert session.scalar(select(func.count()).select_from(FileRevisionModel)) == 2

        search = client.post(
            "/api/v1/search",
            json={
                "repositoryIds": [repository["id"]],
                "code": _source(),
                "language": "python",
                "mode": "exact",
            },
        )
        assert search.status_code == 200
        assert search.json()["items"]
        assert search.json()["items"][0]["category"] == "type1"

        deleted = client.delete(f"/api/v1/repositories/{repository['id']}")
        assert deleted.status_code == 202
        assert client.get(f"/api/v1/repositories/{repository['id']}").status_code == 404

    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(RepositoryModel)) == 0
        assert session.scalar(select(func.count()).select_from(SourceFileModel)) == 0
        assert session.scalar(select(func.count()).select_from(FingerprintPostingModel)) == 0
        assert session.scalar(select(func.count()).select_from(CloneMatchModel)) == 0
        assert session.scalar(select(func.count()).select_from(DeletionOutboxModel)) == 1


def test_contract_errors_auth_health_and_openapi(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    client, _ = _client(tmp_path, token="secret")
    with client:
        unauthorized = client.get("/api/v1/repositories")
        assert unauthorized.status_code == 401
        assert unauthorized.json()["error"]["code"] == "UNAUTHORIZED"
        assert unauthorized.headers["X-Content-Type-Options"] == "nosniff"
        assert unauthorized.headers["Cache-Control"] == "no-store"
        headers = {"Authorization": "Bearer secret"}
        invalid = client.post(
            "/api/v1/repositories",
            headers=headers,
            json={"name": "invalid", "localPath": str(root), "remote": {"url": "https://x"}},
        )
        assert invalid.status_code == 422
        assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"
        outside = client.post(
            "/api/v1/repositories",
            headers=headers,
            json={"name": "outside", "localPath": "/"},
        )
        assert outside.status_code == 422
        assert outside.json()["error"]["code"] == "PATH_NOT_ALLOWED"
        assert client.get("/api/v1/health").json() == {"status": "ok"}
        assert client.get("/api/v1/health", params={"ready": True}).status_code == 200
        openapi = client.get("/openapi.json").json()
        assert openapi["openapi"].startswith("3.1")
        assert "/api/v1/search" in openapi["paths"]


def test_security_limits_source_policy_metrics_and_redacted_logs(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    root = _repository(tmp_path)
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    app = create_app(
        engine=engine,
        allowed_roots=(tmp_path,),
        hosted_token="token",
        expose_source=False,
    )
    headers = {"Authorization": "Bearer token"}
    caplog.set_level(logging.INFO, logger="opencode.api")
    with TestClient(app) as client:
        too_large = client.post(
            "/api/v1/search",
            headers={**headers, "Content-Length": "2100001"},
            content=b"{}",
        )
        assert too_large.status_code == 413
        created = client.post(
            "/api/v1/repositories",
            headers=headers,
            json={"name": "secure", "localPath": str(root)},
        ).json()
        scan = client.post(
            "/api/v1/scans", headers=headers, json={"repositoryId": created["id"]}
        ).json()
        clone = client.get("/api/v1/clones", headers=headers, params={"scan": scan["id"]}).json()[
            "items"
        ][0]
        detail = client.get(f"/api/v1/clones/{clone['id']}", headers=headers).json()
        assert "leftSource" not in detail
        metrics = client.get("/api/v1/metrics", headers=headers).json()
        assert metrics["total"] >= 5
        client.get("/api/v1/health?canary=DO_NOT_LOG_ME")
    assert "DO_NOT_LOG_ME" not in caplog.text


def test_active_scan_quota_is_tenant_scoped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENCODE_MAX_ACTIVE_SCANS", "1")
    root = _repository(tmp_path)
    client, engine = _client(tmp_path)
    with client:
        repository = client.post(
            "/api/v1/repositories", json={"name": "quota", "localPath": str(root)}
        ).json()
        with Session(engine) as session:
            session.add(ScanJobModel(repository_id=repository["id"], status="queued"))
            session.commit()
        response = client.post("/api/v1/scans", json={"repositoryId": repository["id"]})
        assert response.status_code == 429
        assert response.json()["error"]["code"] == "SCAN_QUOTA_EXCEEDED"


def test_uuid7_and_hash_mapping_boundaries() -> None:
    generated = uuid7()
    assert generated.split("-")[2].startswith("7")
    values = (0, 1, (1 << 63) - 1, 1 << 63, (1 << 64) - 1)
    encoded = [u64_to_i64(value) for value in values]
    assert encoded == sorted(encoded)
    assert [i64_to_u64(value) for value in encoded] == list(values)


def test_alembic_initial_migration_upgrades_and_downgrades(tmp_path: Path) -> None:
    database = tmp_path / "migration.db"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite+pysqlite:///{database}")

    command.upgrade(config, "head")
    engine = create_engine(f"sqlite+pysqlite:///{database}")
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(RepositoryModel)) == 0
    command.downgrade(config, "base")
