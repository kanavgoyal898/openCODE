from __future__ import annotations

from dataclasses import replace

import pytest
from opencode_core.fingerprinting import Fingerprint, FingerprintSet
from opencode_core.indexing import (
    FingerprintQuery,
    FragmentFingerprintSet,
    InMemoryFingerprintIndex,
    RevisionFingerprintSet,
)
from opencode_core.normalization import Mode


def _set(mode: Mode, *values: tuple[int, int]) -> FingerprintSet:
    return FingerprintSet(
        mode=mode,
        fingerprints=tuple(Fingerprint(value, position) for value, position in values),
        token_count=40,
    )


def _revision(repository: str, revision: str, value: int) -> RevisionFingerprintSet:
    return RevisionFingerprintSet(
        repository,
        revision,
        (
            FragmentFingerprintSet("fragment-b", _set("exact", (value, 8))),
            FragmentFingerprintSet("fragment-a", _set("exact", (value, 3))),
        ),
    )


def _query(value: int, mode: Mode = "exact") -> FingerprintQuery:
    return FingerprintQuery("fp-v1", "norm-v1", mode, value)


def test_index_returns_all_and_only_stably_ordered_postings() -> None:
    index = InMemoryFingerprintIndex()
    index.replace_revision(_revision("repo-2", "rev-2", 42))
    index.replace_revision(_revision("repo-1", "rev-1", 42))

    postings = index.postings(_query(42))

    assert [(item.repository_id, item.fragment_id, item.token_position) for item in postings] == [
        ("repo-1", "fragment-a", 3),
        ("repo-1", "fragment-b", 8),
        ("repo-2", "fragment-a", 3),
        ("repo-2", "fragment-b", 8),
    ]
    assert index.postings(_query(99)) == ()
    assert index.postings(_query(42, "renamed")) == ()
    assert index.document_frequency(_query(42)) == 4
    assert index.fragment_count() == 4


def test_revision_replacement_removes_stale_postings() -> None:
    index = InMemoryFingerprintIndex()
    index.replace_revision(_revision("repo", "revision", 10))

    index.replace_revision(_revision("repo", "revision", 20))

    assert index.postings(_query(10)) == ()
    assert len(index.postings(_query(20))) == 2


def test_failed_commit_preserves_previous_complete_revision() -> None:
    fail = False

    def hook(_: RevisionFingerprintSet) -> None:
        if fail:
            raise RuntimeError("injected transaction failure")

    index = InMemoryFingerprintIndex(hook)
    index.replace_revision(_revision("repo", "revision", 10))
    fail = True

    with pytest.raises(RuntimeError, match="injected"):
        index.replace_revision(_revision("repo", "revision", 20))

    assert len(index.postings(_query(10))) == 2
    assert index.postings(_query(20)) == ()


def test_repository_deletion_cascades_only_target_repository() -> None:
    index = InMemoryFingerprintIndex()
    index.replace_revision(_revision("repo-a", "revision-a", 42))
    index.replace_revision(_revision("repo-b", "revision-b", 42))

    index.delete_repository("repo-a")
    index.delete_repository("missing")

    assert {item.repository_id for item in index.postings(_query(42))} == {"repo-b"}


def test_model_rejects_invalid_revision_and_duplicate_fragments() -> None:
    fragment = FragmentFingerprintSet("same", _set("exact", (1, 0)))
    with pytest.raises(ValueError, match="identifiers are required"):
        RevisionFingerprintSet("", "revision", ())
    with pytest.raises(ValueError, match="unique"):
        RevisionFingerprintSet("repo", "revision", (fragment, replace(fragment)))
