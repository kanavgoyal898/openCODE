from __future__ import annotations

import pytest
from opencode_core.fingerprinting import Fingerprint, FingerprintSet
from opencode_core.indexing import (
    FragmentFingerprintSet,
    InMemoryFingerprintIndex,
    RevisionFingerprintSet,
)
from opencode_core.retrieval import CandidateRetriever, RetrievalPolicy


def _fingerprints(*values: int, small: bool = False) -> FingerprintSet:
    return FingerprintSet(
        "exact",
        tuple(Fingerprint(value, index, small) for index, value in enumerate(values)),
        10 if small else 50,
    )


def _insert(
    index: InMemoryFingerprintIndex,
    repository: str,
    revision: str,
    fragment: str,
    *hashes: int,
    small: bool = False,
) -> None:
    index.replace_revision(
        RevisionFingerprintSet(
            repository,
            revision,
            (FragmentFingerprintSet(fragment, _fingerprints(*hashes, small=small)),),
        )
    )


def test_retrieval_requires_three_distinct_hashes_and_has_stable_ranking() -> None:
    index = InMemoryFingerprintIndex()
    _insert(index, "repo-b", "rev-b", "fragment", 1, 2, 3)
    _insert(index, "repo-a", "rev-a", "fragment", 1, 2, 3, 4)
    _insert(index, "repo-c", "rev-c", "fragment", 1, 2)

    result = CandidateRetriever(index).retrieve(_fingerprints(1, 2, 3, 4))

    assert [(item.repository_id, len(item.shared_hashes)) for item in result.candidates] == [
        ("repo-a", 4),
        ("repo-b", 3),
    ]
    assert result.postings_examined == 9
    assert not result.truncated


def test_stop_fingerprints_are_suppressed_but_reported() -> None:
    index = InMemoryFingerprintIndex()
    _insert(index, "repo-a", "rev-a", "a", 7, 8, 9, 10)
    _insert(index, "repo-b", "rev-b", "b", 7, 8, 9, 11)
    retriever = CandidateRetriever(index, RetrievalPolicy(stop_floor=1, stop_ratio=0))

    result = retriever.retrieve(_fingerprints(7, 8, 9, 10))

    assert result.stop_hashes == (7, 8, 9)
    assert result.candidates == ()


def test_small_fingerprint_bypasses_three_hash_threshold() -> None:
    index = InMemoryFingerprintIndex()
    _insert(index, "repo", "rev", "small", 99, small=True)

    result = CandidateRetriever(index).retrieve(_fingerprints(99, small=True))

    assert len(result.candidates) == 1
    assert result.candidates[0].small


def test_exclusion_and_budgets_are_explicit_and_deterministic() -> None:
    index = InMemoryFingerprintIndex()
    _insert(index, "repo-a", "rev-a", "a", 1, 2, 3)
    _insert(index, "repo-b", "rev-b", "b", 1, 2, 3)
    retriever = CandidateRetriever(
        index,
        RetrievalPolicy(max_postings=4, max_candidates=1),
    )

    result = retriever.retrieve(
        _fingerprints(1, 2, 3),
        excluded_fragments=(("repo-a", "rev-a", "a"),),
    )

    assert result.truncated
    assert result.postings_examined == 4
    assert len(result.candidates) <= 1


@pytest.mark.parametrize(
    "policy",
    [
        RetrievalPolicy(minimum_shared_hashes=1),
        RetrievalPolicy(stop_floor=0),
        RetrievalPolicy(stop_ratio=0),
    ],
)
def test_valid_boundary_policies_are_accepted(policy: RetrievalPolicy) -> None:
    assert policy


@pytest.mark.parametrize(
    "kwargs",
    [
        {"minimum_shared_hashes": 0},
        {"stop_floor": -1},
        {"stop_ratio": -0.1},
        {"stop_ratio": 1.1},
        {"max_postings": 0},
        {"max_candidates": 0},
    ],
)
def test_invalid_retrieval_policy_is_rejected(kwargs: dict[str, int | float]) -> None:
    with pytest.raises(ValueError):
        RetrievalPolicy(**kwargs)  # type: ignore[arg-type]
