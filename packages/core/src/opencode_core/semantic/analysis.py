"""Conservative language-neutral program-analysis evidence for semantic candidates."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise

from opencode_core.matching.store import FragmentRecord

_CONTROL = {
    "for": "LOOP",
    "while": "LOOP",
    "if": "BRANCH",
    "elif": "BRANCH",
    "else": "BRANCH",
    "switch": "BRANCH",
    "case": "BRANCH",
    "return": "RETURN",
    "break": "BREAK",
    "continue": "CONTINUE",
    "try": "EXCEPTION",
    "catch": "EXCEPTION",
    "except": "EXCEPTION",
}
_UNSUPPORTED = {
    "eval",
    "exec",
    "open",
    "socket",
    "subprocess",
    "reflection",
    "reflect",
    "importlib",
    "__import__",
}


def _jaccard(left: frozenset[str], right: frozenset[str]) -> float:
    union = left | right
    # Absence of evidence is not agreement and cannot promote a candidate.
    return len(left & right) / len(union) if union else 0.0


def _cfg(record: FragmentRecord) -> frozenset[str]:
    controls = [
        _CONTROL[token.canonical] for token in record.exact_tokens if token.canonical in _CONTROL
    ]
    return frozenset(
        [f"NODE:{value}" for value in controls]
        + [f"EDGE:{left}>{right}" for left, right in pairwise(controls)]
    )


def _data_flow(record: FragmentRecord) -> frozenset[str]:
    definitions: dict[str, int] = {}
    edges: set[str] = set()
    tokens = record.exact_tokens
    for index, token in enumerate(tokens):
        if token.kind != "identifier":
            continue
        following = tokens[index + 1].canonical if index + 1 < len(tokens) else ""
        if following in {"=", ":="}:
            definitions[token.canonical] = index
            continue
        if token.canonical in definitions:
            distance = index - definitions[token.canonical]
            edges.add(f"DEF_USE:{'NEAR' if distance <= 3 else 'FAR'}")
    return frozenset(edges)


@dataclass(frozen=True, slots=True)
class ProgramAnalysisEvidence:
    cfg_similarity: float
    data_flow_similarity: float
    pdg_similarity: float
    supported: bool
    unsupported_constructs: tuple[str, ...]


def compare_program_evidence(
    left: FragmentRecord, right: FragmentRecord
) -> ProgramAnalysisEvidence:
    left_cfg, right_cfg = _cfg(left), _cfg(right)
    left_data, right_data = _data_flow(left), _data_flow(right)
    left_pdg = left_cfg | frozenset(f"PDG:{item}" for item in left_data)
    right_pdg = right_cfg | frozenset(f"PDG:{item}" for item in right_data)
    seen = {token.canonical.casefold() for record in (left, right) for token in record.exact_tokens}
    unsupported = tuple(sorted(seen & _UNSUPPORTED))
    return ProgramAnalysisEvidence(
        _jaccard(left_cfg, right_cfg),
        _jaccard(left_data, right_data),
        _jaccard(left_pdg, right_pdg),
        not unsupported,
        unsupported,
    )
