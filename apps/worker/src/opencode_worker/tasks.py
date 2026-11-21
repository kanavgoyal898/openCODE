"""Scan job execution and atomic relational persistence."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from opencode_api.hashing import u64_to_i64
from opencode_api.models import (
    AlgorithmVersionModel,
    CloneGroupModel,
    CloneMatchModel,
    FileRevisionModel,
    FingerprintModel,
    FingerprintPostingModel,
    FragmentModel,
    MatchEvidenceModel,
    RepositoryModel,
    ScanJobModel,
    SourceFileModel,
    utc_now,
)
from opencode_core.engine import analyze_directory, find_clones
from opencode_core.version import FINGERPRINT_VERSION, NORMALIZATION_VERSION
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker


def _algorithm(session: Session) -> AlgorithmVersionModel:
    config = {
        "fingerprintVersion": FINGERPRINT_VERSION,
        "normalizationVersion": NORMALIZATION_VERSION,
    }
    checksum = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    existing = session.scalar(
        select(AlgorithmVersionModel).where(AlgorithmVersionModel.config_sha256 == checksum)
    )
    if existing is not None:
        return existing
    model = AlgorithmVersionModel(
        fingerprint_version=FINGERPRINT_VERSION,
        normalization_version=NORMALIZATION_VERSION,
        config_json=config,
        config_sha256=checksum,
    )
    session.add(model)
    session.flush()
    return model


def _persist_workspace(session: Session, repository: RepositoryModel, scan: ScanJobModel) -> None:
    if repository.local_path is None:
        raise ValueError("remote repository acquisition is not configured")
    workspace = analyze_directory(Path(repository.local_path))
    algorithm = _algorithm(session)
    scan.algorithm_version_id = algorithm.id
    fingerprint_cache: dict[tuple[str, int], FingerprintModel] = {}
    for record in workspace.records:
        source_path = workspace.root / record.fragment_id
        content = source_path.read_bytes()
        source = session.scalar(
            select(SourceFileModel).where(
                SourceFileModel.repository_id == repository.id,
                SourceFileModel.logical_path == record.fragment_id,
            )
        )
        if source is None:
            source = SourceFileModel(repository_id=repository.id, logical_path=record.fragment_id)
            session.add(source)
            session.flush()
        session.execute(
            delete(FileRevisionModel).where(FileRevisionModel.source_file_id == source.id)
        )
        first = record.exact_tokens[0].source if record.exact_tokens else None
        last = record.exact_tokens[-1].source if record.exact_tokens else None
        revision = FileRevisionModel(
            source_file_id=source.id,
            content_sha256=hashlib.sha256(content).hexdigest(),
            byte_size=len(content),
            language=Path(record.fragment_id).suffix.lstrip("."),
            adapter_version="tree-sitter-pinned",
        )
        session.add(revision)
        session.flush()
        fragment = FragmentModel(
            file_revision_id=revision.id,
            token_start=0,
            token_end=len(record.exact_tokens),
            start_byte=0 if first is None else first.start_byte,
            end_byte=0 if last is None else last.end_byte,
            start_line=1 if first is None else first.start_line,
            end_line=1 if last is None else last.end_line,
        )
        session.add(fragment)
        session.flush()
        fingerprint_sets = {
            "exact": record.exact_fingerprints,
            "renamed": record.renamed_fingerprints,
        }
        for mode in scan.modes_json:
            if mode not in fingerprint_sets:
                continue
            fingerprint_set = fingerprint_sets[mode]
            for selected in fingerprint_set.fingerprints:
                cache_key = (fingerprint_set.mode, selected.hash_u64)
                fingerprint_model = fingerprint_cache.get(cache_key)
                if fingerprint_model is None:
                    fingerprint_model = session.scalar(
                        select(FingerprintModel).where(
                            FingerprintModel.algorithm_version_id == algorithm.id,
                            FingerprintModel.mode == fingerprint_set.mode,
                            FingerprintModel.hash_i64 == u64_to_i64(selected.hash_u64),
                        )
                    )
                    if fingerprint_model is None:
                        fingerprint_model = FingerprintModel(
                            algorithm_version_id=algorithm.id,
                            mode=fingerprint_set.mode,
                            hash_i64=u64_to_i64(selected.hash_u64),
                        )
                        session.add(fingerprint_model)
                        session.flush()
                    fingerprint_cache[cache_key] = fingerprint_model
                session.add(
                    FingerprintPostingModel(
                        fingerprint_id=fingerprint_model.id,
                        fragment_id=fragment.id,
                        token_position=selected.token_position,
                        small=selected.small,
                    )
                )
        source.active_revision_id = revision.id

    categories = tuple(
        category
        for mode, category in (
            ("exact", "type1"),
            ("renamed", "type2"),
            ("structural", "type3"),
        )
        if mode in scan.modes_json
    )
    matches = find_clones(workspace, categories)
    for result in matches:
        payload = asdict(result)
        payload["left"]["repository_id"] = repository.id
        payload["right"]["repository_id"] = repository.id
        signature = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        group = CloneGroupModel(
            scan_job_id=scan.id, clone_type=result.category, signature=signature
        )
        session.add(group)
        session.flush()
        match = CloneMatchModel(
            clone_group_id=group.id,
            left_fragment_id=result.left.fragment_id,
            right_fragment_id=result.right.fragment_id,
            payload_json=payload,
        )
        session.add(match)
        session.flush()
        session.add(
            MatchEvidenceModel(
                clone_match_id=match.id,
                kind="token",
                version=NORMALIZATION_VERSION,
                payload_json=asdict(result.evidence),
            )
        )
    scan.counts_json = {
        "files": len(workspace.records),
        "tokens": sum(len(record.exact_tokens) for record in workspace.records),
        "clones": len(matches),
        "skips": len(workspace.diagnostics),
    }
    scan.status = "partial" if workspace.diagnostics else "completed"
    if scan.strict and workspace.diagnostics:
        scan.status = "failed"
        scan.error = "strict scan rejected file-level diagnostics"
    scan.completed_at = utc_now()


def process_scan(factory: sessionmaker[Session], scan_id: str) -> None:
    with factory() as session:
        scan = session.get(ScanJobModel, scan_id)
        if scan is None or scan.status not in {"queued", "running"}:
            return
        scan.status = "running"
        session.commit()
    try:
        with factory.begin() as session:
            scan = session.get(ScanJobModel, scan_id)
            if scan is None:
                return
            repository = session.get(RepositoryModel, scan.repository_id)
            if repository is None:
                raise ValueError("repository no longer exists")
            _persist_workspace(session, repository, scan)
    except Exception as error:
        with factory.begin() as session:
            scan = session.get(ScanJobModel, scan_id)
            if scan is not None:
                scan.status = "failed"
                scan.error = str(error)[:1000]
                scan.completed_at = utc_now()
