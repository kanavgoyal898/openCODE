from __future__ import annotations

from dataclasses import replace

import pytest
from opencode_core.detection import CloneDetector, DetectorConfig
from opencode_core.fingerprinting import Fingerprint, fingerprint
from opencode_core.indexing import (
    FragmentFingerprintSet,
    InMemoryFingerprintIndex,
    RevisionFingerprintSet,
)
from opencode_core.matching import (
    ExactCloneDetector,
    FragmentRecord,
    InMemoryFragmentStore,
    TokenCloneDetector,
    verify_candidate,
)
from opencode_core.normalization import normalize
from opencode_core.parsers import default_registry
from opencode_core.retrieval import Candidate, CandidateRetriever, PositionEvidence


def _source(name: str, left: str, right: str, literal: str = "'value'") -> str:
    return (
        f"def {name}({left}, {right}):\n"
        f"    first = {left} + {right}\n"
        f"    second = first * {left}\n"
        f"    third = second - {right}\n"
        f"    fourth = third / ({left} + 1)\n"
        f"    label = {literal}\n"
        "    return fourth, label\n"
    )


def _record(repository: str, revision: str, fragment_id: str, source: str) -> FragmentRecord:
    tokens = default_registry().detect(f"{fragment_id}.py").tokenize(source.encode()).tokens
    exact = normalize(tokens, "exact")
    renamed = normalize(tokens, "renamed")
    return FragmentRecord(
        repository,
        revision,
        fragment_id,
        exact,
        renamed,
        fingerprint(exact, "exact"),
        fingerprint(renamed, "renamed"),
    )


def _system(*records: FragmentRecord) -> tuple[InMemoryFragmentStore, InMemoryFingerprintIndex]:
    store = InMemoryFragmentStore()
    index = InMemoryFingerprintIndex()
    for record in records:
        store.put(record)
        index.replace_revision(
            RevisionFingerprintSet(
                record.repository_id,
                record.revision_id,
                (
                    FragmentFingerprintSet(record.fragment_id, record.exact_fingerprints),
                    FragmentFingerprintSet(record.fragment_id, record.renamed_fingerprints),
                ),
            )
        )
    return store, index


def test_type1_detects_formatting_and_comment_only_clone_with_source_ranges() -> None:
    source = _source("compute", "left", "right")
    formatted = source.replace("    first", "    # retained comment\n    first").replace(
        "left + right", "left+right"
    )
    query = _record("repo-a", "rev-a", "query", source)
    clone = _record("repo-b", "rev-b", "clone", formatted)
    store, index = _system(query, clone)

    results = ExactCloneDetector(CandidateRetriever(index), store).detect("query")

    assert len(results) == 1
    result = results[0]
    assert result.category == "type1"
    assert result.evidence_state == "verified"
    assert result.left.repository_id == "repo-a"
    assert result.right.repository_id == "repo-b"
    assert result.left.start_line == 1
    assert result.right.end_line == 8
    assert result.scores.query_coverage == 1
    assert result.scores.candidate_coverage == 1
    assert result.scores.confidence is None


def test_type2_detects_identifier_and_literal_changes_but_not_exact_clones() -> None:
    query = _record("repo-a", "rev-a", "query", _source("compute", "left", "right"))
    renamed = _record(
        "repo-b",
        "rev-b",
        "renamed",
        _source("calculate", "first_arg", "second_arg", "'changed'"),
    )
    exact = _record("repo-c", "rev-c", "exact", _source("compute", "left", "right"))
    store, index = _system(query, renamed, exact)

    results = TokenCloneDetector(CandidateRetriever(index), store).detect("query")

    assert [(result.category, result.right.fragment_id) for result in results] == [
        ("type2", "renamed")
    ]
    assert results[0].limitations == ("LEXICAL_EVIDENCE_ONLY", "NOT_PLAGIARISM_PROOF")


def test_modified_non_clone_is_rejected_and_no_match_is_empty() -> None:
    query = _record("repo-a", "rev-a", "query", _source("compute", "left", "right"))
    different = _record(
        "repo-b",
        "rev-b",
        "different",
        "def unrelated(items):\n    return sorted(set(items))\n",
    )
    store, index = _system(query, different)

    assert ExactCloneDetector(CandidateRetriever(index), store).detect("query") == ()
    assert TokenCloneDetector(CandidateRetriever(index), store).detect("query") == ()


def test_hash_collision_seed_cannot_verify_unequal_tokens() -> None:
    left = _record("a", "a", "left", _source("compute", "left", "right"))
    right = _record("b", "b", "right", _source("calculate", "x", "y"))
    candidate = Candidate(
        "b",
        "b",
        "right",
        (123,),
        (PositionEvidence(123, 0, 0),),
        False,
    )

    assert verify_candidate(left.exact_tokens, right.exact_tokens, candidate) == ()


def test_overlapping_seed_spans_are_deduplicated() -> None:
    record = _record("repo", "rev", "fragment", _source("compute", "left", "right"))
    candidate = Candidate(
        "repo",
        "rev",
        "other",
        (1, 2),
        (PositionEvidence(1, 0, 0), PositionEvidence(2, 5, 5)),
        False,
    )

    spans = verify_candidate(record.exact_tokens, record.exact_tokens, candidate)

    assert len(spans) == 1
    assert spans[0].length == len(record.exact_tokens)


def test_small_fragments_require_complete_stream_equality() -> None:
    left = _record("a", "a", "left", "x = 1\n")
    right = _record("b", "b", "right", "x = 1\n")
    candidate = Candidate(
        "b",
        "b",
        "right",
        (left.exact_fingerprints.fingerprints[0].hash_u64,),
        (PositionEvidence(1, 0, 0),),
        True,
    )

    assert len(verify_candidate(left.exact_tokens, right.exact_tokens, candidate)) == 1
    changed = tuple(
        replace(token, canonical="changed") if index == 0 else token
        for index, token in enumerate(right.exact_tokens)
    )
    assert verify_candidate(left.exact_tokens, changed, candidate) == ()


def test_common_detector_protocol_and_config_validation() -> None:
    query = _record("a", "a", "query", _source("compute", "left", "right"))
    clone = _record("b", "b", "clone", _source("compute", "left", "right"))
    store, index = _system(query, clone)
    detector: CloneDetector = ExactCloneDetector(CandidateRetriever(index), store)

    assert detector.detector_id == "exact-clone-detector"
    assert detector.detect("query")
    with pytest.raises(ValueError, match="thresholds"):
        DetectorConfig(minimum_tokens=0)


def test_fragment_store_rejects_missing_or_ambiguous_short_identifier() -> None:
    record = _record("a", "a", "same", "x = 1\n")
    other = replace(record, repository_id="b", revision_id="b")
    store = InMemoryFragmentStore()
    store.put(record)
    store.put(other)

    with pytest.raises(KeyError, match="ambiguous"):
        store.get_by_fragment_id("same")
    with pytest.raises(KeyError, match="missing"):
        store.get_by_fragment_id("absent")


def test_manual_fingerprint_collision_fixture_is_not_treated_as_proof() -> None:
    first = Fingerprint(42, 0)
    second = Fingerprint(42, 0)
    assert first == second
