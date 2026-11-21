"""Thread-safe copy-on-write fingerprint index for standalone operation."""

from __future__ import annotations

from collections.abc import Callable
from threading import RLock

from opencode_core.indexing.model import (
    FingerprintKey,
    FingerprintQuery,
    Posting,
    RevisionFingerprintSet,
)

CommitHook = Callable[[RevisionFingerprintSet], None]


class InMemoryFingerprintIndex:
    """Atomic revision replacement without database or service dependencies."""

    def __init__(self, commit_hook: CommitHook | None = None) -> None:
        self._postings: dict[FingerprintKey, tuple[Posting, ...]] = {}
        self._revision_keys: dict[str, tuple[tuple[FingerprintKey, Posting], ...]] = {}
        self._repository_revisions: dict[str, frozenset[str]] = {}
        self._commit_hook = commit_hook
        self._lock = RLock()

    def replace_revision(self, revision: RevisionFingerprintSet) -> None:
        staged = self._stage(revision)
        with self._lock:
            postings = dict(self._postings)
            revision_keys = dict(self._revision_keys)
            repository_revisions = dict(self._repository_revisions)
            self._remove_revision(
                revision.revision_id,
                postings,
                revision_keys,
                repository_revisions,
            )
            for key, posting in staged:
                postings[key] = tuple(sorted((*postings.get(key, ()), posting)))
            revision_keys[revision.revision_id] = staged
            revisions = set(repository_revisions.get(revision.repository_id, frozenset()))
            revisions.add(revision.revision_id)
            repository_revisions[revision.repository_id] = frozenset(revisions)
            if self._commit_hook is not None:
                self._commit_hook(revision)
            self._postings = postings
            self._revision_keys = revision_keys
            self._repository_revisions = repository_revisions

    def postings(self, query: FingerprintQuery) -> tuple[Posting, ...]:
        with self._lock:
            return self._postings.get(query.key, ())

    def document_frequency(self, query: FingerprintQuery) -> int:
        with self._lock:
            return len({posting.fragment_id for posting in self._postings.get(query.key, ())})

    def fragment_count(self) -> int:
        with self._lock:
            return len(
                {
                    posting.fragment_id
                    for postings in self._postings.values()
                    for posting in postings
                }
            )

    def delete_repository(self, repository_id: str) -> None:
        with self._lock:
            postings = dict(self._postings)
            revision_keys = dict(self._revision_keys)
            repository_revisions = dict(self._repository_revisions)
            for revision_id in repository_revisions.get(repository_id, frozenset()):
                self._remove_revision(
                    revision_id,
                    postings,
                    revision_keys,
                    repository_revisions,
                )
            repository_revisions.pop(repository_id, None)
            self._postings = postings
            self._revision_keys = revision_keys
            self._repository_revisions = repository_revisions

    @staticmethod
    def _stage(revision: RevisionFingerprintSet) -> tuple[tuple[FingerprintKey, Posting], ...]:
        staged: list[tuple[FingerprintKey, Posting]] = []
        for fragment in revision.fragments:
            fingerprint_set = fragment.fingerprints
            for selected in fingerprint_set.fingerprints:
                key = FingerprintKey(
                    fingerprint_set.algorithm_version,
                    fingerprint_set.normalization_version,
                    fingerprint_set.mode,
                    selected.hash_u64,
                )
                staged.append(
                    (
                        key,
                        Posting(
                            revision.repository_id,
                            revision.revision_id,
                            fragment.fragment_id,
                            selected.token_position,
                            selected.small,
                        ),
                    )
                )
        return tuple(sorted(staged))

    @staticmethod
    def _remove_revision(
        revision_id: str,
        postings: dict[FingerprintKey, tuple[Posting, ...]],
        revision_keys: dict[str, tuple[tuple[FingerprintKey, Posting], ...]],
        repository_revisions: dict[str, frozenset[str]],
    ) -> None:
        previous = revision_keys.pop(revision_id, ())
        repository_ids: set[str] = set()
        for key, posting in previous:
            repository_ids.add(posting.repository_id)
            retained = tuple(item for item in postings.get(key, ()) if item != posting)
            if retained:
                postings[key] = retained
            else:
                postings.pop(key, None)
        for repository_id in repository_ids:
            revisions = set(repository_revisions.get(repository_id, frozenset()))
            revisions.discard(revision_id)
            if revisions:
                repository_revisions[repository_id] = frozenset(revisions)
            else:
                repository_revisions.pop(repository_id, None)
