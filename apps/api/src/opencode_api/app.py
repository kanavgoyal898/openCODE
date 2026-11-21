"""FastAPI application implementing the versioned REST contract."""

from __future__ import annotations

import base64
import os
import tempfile
import uuid
from collections.abc import AsyncIterator, Callable, Iterator
from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Annotated, Any
from urllib.parse import urlsplit, urlunsplit

from fastapi import BackgroundTasks, Depends, FastAPI, Header, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from opencode_core.engine import compare_files
from opencode_core.parsers import SourceScanner, default_registry
from opencode_worker.tasks import process_scan
from sqlalchemy import Engine, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from opencode_api.db import (
    build_engine,
    build_session_factory,
    create_schema,
    enable_sqlite_foreign_keys,
    session_dependency,
)
from opencode_api.models import (
    CloneGroupModel,
    CloneMatchModel,
    DeletionOutboxModel,
    RepositoryModel,
    ScanJobModel,
)
from opencode_api.schemas import (
    Deletion,
    Health,
    Page,
    Repository,
    RepositoryCreate,
    Scan,
    ScanCreate,
    SearchRequest,
    SearchResult,
)


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        self.status = status
        self.code = code
        self.message = message


def _redact_url(value: str) -> str:
    parsed = urlsplit(value)
    hostname = parsed.hostname or ""
    netloc = hostname
    if parsed.port:
        netloc += f":{parsed.port}"
    return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, ""))


def _repository(model: RepositoryModel) -> Repository:
    return Repository(
        id=model.id,
        name=model.name,
        origin_redacted=model.origin_redacted,
        revision=model.revision,
        created_at=model.created_at,
    )


def _scan(model: ScanJobModel) -> Scan:
    return Scan(
        id=model.id,
        repository_id=model.repository_id,
        status=model.status,  # type: ignore[arg-type]
        counts=model.counts_json,
        error=model.error,
        created_at=model.created_at,
        completed_at=model.completed_at,
    )


def _cursor(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode()).decode().rstrip("=")


def _decode_cursor(value: str) -> str:
    try:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4)).decode()
    except Exception as error:
        raise ApiError(400, "INVALID_CURSOR", "cursor is malformed") from error


def _within(path: Path, roots: tuple[Path, ...]) -> bool:
    resolved = path.resolve(strict=True)
    return any(resolved == root or resolved.is_relative_to(root) for root in roots)


def create_app(
    database_url: str | None = None,
    *,
    engine: Engine | None = None,
    allowed_roots: tuple[Path, ...] | None = None,
    hosted_token: str | None = None,
    initialize_schema: bool = True,
) -> FastAPI:
    database = engine or build_engine(
        database_url or os.environ.get("OPENCODE_DATABASE_URL", "sqlite+pysqlite:///opencode.db")
    )
    enable_sqlite_foreign_keys(database)
    factory = build_session_factory(database)
    roots = tuple(root.resolve() for root in (allowed_roots or (Path.cwd(),)))

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if initialize_schema:
            create_schema(database)
        yield

    app = FastAPI(title="openCODE API", version="1", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            item.strip()
            for item in os.environ.get("OPENCODE_CORS_ORIGINS", "http://localhost:3000").split(",")
            if item.strip()
        ],
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Request-Id"],
    )
    app.state.engine = database
    app.state.session_factory = factory

    def session() -> Iterator[Session]:
        yield from session_dependency(factory)

    def authorize(authorization: Annotated[str | None, Header()] = None) -> None:
        if hosted_token is not None and authorization != f"Bearer {hosted_token}":
            raise ApiError(401, "UNAUTHORIZED", "valid bearer authentication is required")

    @app.middleware("http")
    async def request_id(request: Request, call_next: Callable[[Request], Any]) -> Any:
        identifier = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        request.state.request_id = identifier
        response = await call_next(request)
        response.headers["X-Request-Id"] = identifier
        return response

    @app.exception_handler(ApiError)
    async def api_error(request: Request, error: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=error.status,
            content={
                "error": {
                    "code": error.code,
                    "message": error.message,
                    "requestId": request.state.request_id,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "request validation failed",
                    "requestId": request.state.request_id,
                    "details": {"errors": jsonable_encoder(error.errors())},
                }
            },
        )

    @app.post(
        "/api/v1/repositories",
        response_model=Repository,
        response_model_by_alias=True,
        status_code=201,
        dependencies=[Depends(authorize)],
    )
    def create_repository(
        payload: RepositoryCreate,
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
        db: Session = Depends(session),
    ) -> Repository:
        if idempotency_key is not None and not 1 <= len(idempotency_key) <= 128:
            raise ApiError(400, "INVALID_IDEMPOTENCY_KEY", "idempotency key length is invalid")
        if idempotency_key:
            existing = db.scalar(
                select(RepositoryModel).where(
                    RepositoryModel.tenant_id == "local",
                    RepositoryModel.idempotency_key == idempotency_key,
                )
            )
            if existing is not None:
                return _repository(existing)
        local_path = None
        origin = None
        if payload.local_path is not None:
            path = Path(payload.local_path)
            if not _within(path, roots) or not path.is_dir():
                raise ApiError(422, "PATH_NOT_ALLOWED", "local path is outside configured roots")
            local_path = str(path.resolve())
            origin = local_path
        elif payload.remote is not None:
            origin = _redact_url(payload.remote.url)
        model = RepositoryModel(
            name=payload.name,
            local_path=local_path,
            origin_redacted=origin,
            revision=payload.revision,
            idempotency_key=idempotency_key,
        )
        db.add(model)
        try:
            db.commit()
        except IntegrityError as error:
            db.rollback()
            raise ApiError(409, "REPOSITORY_CONFLICT", "repository name already exists") from error
        return _repository(model)

    @app.get("/api/v1/repositories", response_model=Page, dependencies=[Depends(authorize)])
    def list_repositories(
        cursor: str | None = None,
        limit: Annotated[int, Query(ge=1, le=100)] = 50,
        db: Session = Depends(session),
    ) -> Page:
        statement = select(RepositoryModel).where(RepositoryModel.deleted_at.is_(None))
        if cursor:
            statement = statement.where(RepositoryModel.id > _decode_cursor(cursor))
        models = list(db.scalars(statement.order_by(RepositoryModel.id).limit(limit + 1)))
        more = len(models) > limit
        models = models[:limit]
        return Page(
            items=[_repository(model).model_dump(by_alias=True, mode="json") for model in models],
            next_cursor=_cursor(models[-1].id) if more and models else None,
        )

    @app.get(
        "/api/v1/repositories/{repository_id}",
        response_model=Repository,
        dependencies=[Depends(authorize)],
    )
    def get_repository(repository_id: str, db: Session = Depends(session)) -> Repository:
        model = db.get(RepositoryModel, repository_id)
        if model is None or model.deleted_at is not None:
            raise ApiError(404, "REPOSITORY_NOT_FOUND", "repository was not found")
        return _repository(model)

    @app.delete(
        "/api/v1/repositories/{repository_id}",
        response_model=Deletion,
        status_code=202,
        dependencies=[Depends(authorize)],
    )
    def delete_repository(repository_id: str, db: Session = Depends(session)) -> Deletion:
        model = db.get(RepositoryModel, repository_id)
        if model is None:
            raise ApiError(404, "REPOSITORY_NOT_FOUND", "repository was not found")
        db.add(
            DeletionOutboxModel(
                repository_id=model.id, payload_json={"localPath": model.local_path}
            )
        )
        db.delete(model)
        db.commit()
        return Deletion(id=repository_id)

    @app.post(
        "/api/v1/scans",
        response_model=Scan,
        response_model_by_alias=True,
        status_code=202,
        dependencies=[Depends(authorize)],
    )
    def create_scan(
        payload: ScanCreate,
        background: BackgroundTasks,
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
        db: Session = Depends(session),
    ) -> Scan:
        if idempotency_key:
            existing = db.scalar(
                select(ScanJobModel).where(
                    ScanJobModel.tenant_id == "local",
                    ScanJobModel.idempotency_key == idempotency_key,
                )
            )
            if existing is not None:
                return _scan(existing)
        repository = db.get(RepositoryModel, payload.repository_id)
        if repository is None:
            raise ApiError(404, "REPOSITORY_NOT_FOUND", "repository was not found")
        model = ScanJobModel(
            repository_id=repository.id,
            idempotency_key=idempotency_key,
            strict=payload.strict,
            modes_json=list(payload.modes),
            status="queued",
        )
        db.add(model)
        db.commit()
        response = _scan(model)
        background.add_task(process_scan, factory, model.id)
        return response

    @app.get("/api/v1/scans/{scan_id}", response_model=Scan, dependencies=[Depends(authorize)])
    def get_scan(scan_id: str, db: Session = Depends(session)) -> Scan:
        model = db.get(ScanJobModel, scan_id)
        if model is None:
            raise ApiError(404, "SCAN_NOT_FOUND", "scan was not found")
        return _scan(model)

    @app.get("/api/v1/clones", response_model=Page, dependencies=[Depends(authorize)])
    def list_clones(
        repository: str | None = None,
        scan: str | None = None,
        clone_type: Annotated[str | None, Query(alias="type")] = None,
        cursor: str | None = None,
        limit: Annotated[int, Query(ge=1, le=100)] = 50,
        db: Session = Depends(session),
    ) -> Page:
        statement = select(CloneMatchModel).join(CloneGroupModel).join(ScanJobModel)
        if repository:
            statement = statement.where(ScanJobModel.repository_id == repository)
        if scan:
            statement = statement.where(ScanJobModel.id == scan)
        if clone_type:
            statement = statement.where(CloneGroupModel.clone_type == clone_type)
        if cursor:
            statement = statement.where(CloneMatchModel.id > _decode_cursor(cursor))
        models = list(db.scalars(statement.order_by(CloneMatchModel.id).limit(limit + 1)))
        more = len(models) > limit
        models = models[:limit]
        return Page(
            items=[{"id": model.id, **model.payload_json} for model in models],
            next_cursor=_cursor(models[-1].id) if more and models else None,
        )

    @app.get("/api/v1/clones/{clone_id}", dependencies=[Depends(authorize)])
    def get_clone(clone_id: str, db: Session = Depends(session)) -> dict[str, Any]:
        model = db.get(CloneMatchModel, clone_id)
        if model is None:
            raise ApiError(404, "CLONE_NOT_FOUND", "clone was not found")
        payload = {"id": model.id, **model.payload_json}
        group = db.get(CloneGroupModel, model.clone_group_id)
        scan_model = None if group is None else db.get(ScanJobModel, group.scan_job_id)
        repository_model = (
            None if scan_model is None else db.get(RepositoryModel, scan_model.repository_id)
        )
        if repository_model is not None and repository_model.local_path is not None:
            root = Path(repository_model.local_path).resolve()
            for side in ("left", "right"):
                relative = Path(payload[side]["fragment_id"])
                source = (root / relative).resolve()
                if source.is_relative_to(root) and source.is_file():
                    payload[f"{side}Source"] = source.read_text(
                        encoding="utf-8", errors="replace"
                    )
        return payload

    @app.post("/api/v1/search", response_model=SearchResult, dependencies=[Depends(authorize)])
    def search(payload: SearchRequest, db: Session = Depends(session)) -> SearchResult:
        repositories = list(
            db.scalars(
                select(RepositoryModel).where(RepositoryModel.id.in_(payload.repository_ids))
            )
        )
        if len(repositories) != len(set(payload.repository_ids)):
            raise ApiError(404, "REPOSITORY_NOT_FOUND", "one or more repositories were not found")
        suffix = {"python": ".py", "javascript": ".js", "typescript": ".ts", "java": ".java"}[
            payload.language
        ]
        items: list[dict[str, Any]] = []
        with tempfile.TemporaryDirectory(prefix="opencode-search-") as temporary:
            query_path = Path(temporary) / f"query{suffix}"
            query_path.write_text(payload.code, encoding="utf-8")
            for repository_model in repositories:
                if repository_model.local_path is None:
                    continue
                scanner = SourceScanner(default_registry())
                for source in scanner.scan(Path(repository_model.local_path)):
                    candidate_path = Path(repository_model.local_path) / source.path
                    matches = compare_files(query_path, candidate_path)
                    for match in matches:
                        if payload.mode == "exact" and match.category != "type1":
                            continue
                        if payload.mode == "renamed" and match.category != "type2":
                            continue
                        items.append(asdict(match))
                        if len(items) >= payload.limit:
                            return SearchResult(items=items, truncated=True)
        return SearchResult(items=items, truncated=False)

    @app.get("/api/v1/health", response_model=Health)
    def health(ready: bool = False, db: Session = Depends(session)) -> Health | JSONResponse:
        if ready:
            try:
                db.execute(text("SELECT 1"))
            except Exception:
                return JSONResponse(status_code=503, content={"status": "not_ready"})
        return Health(status="ok")

    return app


app = create_app()
