"""Relational schema shared by PostgreSQL production and SQLite contract tests."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from opencode_api.identifiers import uuid7


def utc_now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class RepositoryModel(Base):
    __tablename__ = "repositories"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name"),
        UniqueConstraint("tenant_id", "idempotency_key"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid7)
    tenant_id: Mapped[str] = mapped_column(String(128), default="local", index=True)
    name: Mapped[str] = mapped_column(String(255))
    local_path: Mapped[str | None] = mapped_column(Text)
    origin_redacted: Mapped[str | None] = mapped_column(Text)
    revision: Mapped[str | None] = mapped_column(String(255))
    retention_policy: Mapped[str] = mapped_column(String(64), default="metadata")
    idempotency_key: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    files: Mapped[list[SourceFileModel]] = relationship(cascade="all, delete-orphan")
    scans: Mapped[list[ScanJobModel]] = relationship(cascade="all, delete-orphan")


class SourceFileModel(Base):
    __tablename__ = "source_files"
    __table_args__ = (UniqueConstraint("repository_id", "logical_path"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid7)
    repository_id: Mapped[str] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"), index=True
    )
    logical_path: Mapped[str] = mapped_column(Text)
    active_revision_id: Mapped[str | None] = mapped_column(String(36))
    revisions: Mapped[list[FileRevisionModel]] = relationship(cascade="all, delete-orphan")


class FileRevisionModel(Base):
    __tablename__ = "file_revisions"
    __table_args__ = (UniqueConstraint("source_file_id", "content_sha256", "adapter_version"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid7)
    source_file_id: Mapped[str] = mapped_column(
        ForeignKey("source_files.id", ondelete="CASCADE"), index=True
    )
    content_sha256: Mapped[str] = mapped_column(String(64))
    byte_size: Mapped[int] = mapped_column(Integer)
    language: Mapped[str] = mapped_column(String(32))
    adapter_version: Mapped[str] = mapped_column(String(128))
    fragments: Mapped[list[FragmentModel]] = relationship(cascade="all, delete-orphan")


class FragmentModel(Base):
    __tablename__ = "fragments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid7)
    file_revision_id: Mapped[str] = mapped_column(
        ForeignKey("file_revisions.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(32), default="file")
    token_start: Mapped[int] = mapped_column(Integer, default=0)
    token_end: Mapped[int] = mapped_column(Integer)
    start_byte: Mapped[int] = mapped_column(Integer)
    end_byte: Mapped[int] = mapped_column(Integer)
    start_line: Mapped[int] = mapped_column(Integer)
    end_line: Mapped[int] = mapped_column(Integer)
    postings: Mapped[list[FingerprintPostingModel]] = relationship(cascade="all, delete-orphan")


class AlgorithmVersionModel(Base):
    __tablename__ = "algorithm_versions"
    __table_args__ = (UniqueConstraint("config_sha256"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid7)
    fingerprint_version: Mapped[str] = mapped_column(String(64))
    normalization_version: Mapped[str] = mapped_column(String(64))
    config_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    config_sha256: Mapped[str] = mapped_column(String(64))


class FingerprintModel(Base):
    __tablename__ = "fingerprints"
    __table_args__ = (UniqueConstraint("algorithm_version_id", "mode", "hash_i64"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid7)
    algorithm_version_id: Mapped[str] = mapped_column(
        ForeignKey("algorithm_versions.id", ondelete="RESTRICT"), index=True
    )
    mode: Mapped[str] = mapped_column(String(16))
    hash_i64: Mapped[int] = mapped_column(BigInteger)


class FingerprintPostingModel(Base):
    __tablename__ = "fingerprint_postings"
    fingerprint_id: Mapped[str] = mapped_column(
        ForeignKey("fingerprints.id", ondelete="CASCADE"), primary_key=True
    )
    fragment_id: Mapped[str] = mapped_column(
        ForeignKey("fragments.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    token_position: Mapped[int] = mapped_column(Integer, primary_key=True)
    small: Mapped[bool] = mapped_column(Boolean, default=False)


class ScanJobModel(Base):
    __tablename__ = "scan_jobs"
    __table_args__ = (UniqueConstraint("tenant_id", "idempotency_key"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid7)
    tenant_id: Mapped[str] = mapped_column(String(128), default="local")
    repository_id: Mapped[str] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"), index=True
    )
    algorithm_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("algorithm_versions.id", ondelete="RESTRICT")
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(16), default="queued", index=True)
    strict: Mapped[bool] = mapped_column(Boolean, default=False)
    modes_json: Mapped[list[str]] = mapped_column(JSON, default=lambda: ["exact", "renamed"])
    counts_json: Mapped[dict[str, int]] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    groups: Mapped[list[CloneGroupModel]] = relationship(cascade="all, delete-orphan")


class CloneGroupModel(Base):
    __tablename__ = "clone_groups"
    __table_args__ = (UniqueConstraint("scan_job_id", "signature"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid7)
    scan_job_id: Mapped[str] = mapped_column(
        ForeignKey("scan_jobs.id", ondelete="CASCADE"), index=True
    )
    clone_type: Mapped[str] = mapped_column(String(16), index=True)
    signature: Mapped[str] = mapped_column(String(64))
    matches: Mapped[list[CloneMatchModel]] = relationship(cascade="all, delete-orphan")


class CloneMatchModel(Base):
    __tablename__ = "clone_matches"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid7)
    clone_group_id: Mapped[str] = mapped_column(
        ForeignKey("clone_groups.id", ondelete="CASCADE"), index=True
    )
    left_fragment_id: Mapped[str] = mapped_column(String(255))
    right_fragment_id: Mapped[str] = mapped_column(String(255))
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    evidence: Mapped[list[MatchEvidenceModel]] = relationship(cascade="all, delete-orphan")


class MatchEvidenceModel(Base):
    __tablename__ = "match_evidence"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid7)
    clone_match_id: Mapped[str] = mapped_column(
        ForeignKey("clone_matches.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(32))
    version: Mapped[str] = mapped_column(String(64))
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON)


class DeletionOutboxModel(Base):
    __tablename__ = "deletion_outbox"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid7)
    repository_id: Mapped[str] = mapped_column(String(36), index=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


Index(
    "ix_postings_fingerprint_fragment",
    FingerprintPostingModel.fingerprint_id,
    FingerprintPostingModel.fragment_id,
)
