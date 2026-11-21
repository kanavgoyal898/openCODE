#!/usr/bin/env python3
"""Validate the persisted specification inventory and local Markdown links."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
REQUIREMENT = re.compile(r"^\| (REQ-[A-Z]+-[0-9]{3}) \|", re.MULTILINE)

REQUIRED = (
    "README.md",
    "AGENTS.md",
    *(f"docs/{number:02d}-{name}.md" for number, name in enumerate((
        "project-vision", "product-requirements", "functional-specification",
        "non-functional-requirements", "system-architecture", "code-clone-taxonomy",
        "fingerprinting-algorithms", "tokenization-normalization", "winnowing-design",
        "indexing-retrieval", "matching-verification", "database-design", "api-specification",
        "cli-specification", "security-threat-model", "testing-strategy", "benchmarking-plan",
        "deployment-architecture", "implementation-roadmap", "acceptance-criteria", "risk-register",
    ))),
    "docs/glossary.md",
    *(f"docs/adr/ADR-{number:03d}-{name}.md" for number, name in enumerate((
        "technology-stack", "fingerprinting-strategy", "indexing-strategy",
        "parser-strategy", "storage-strategy",
    ), start=1)),
    *(f"specs/{name}.md" for name in (
        "requirements", "architecture", "algorithm-contracts", "language-adapters",
        "data-model", "api-contracts", "cli-contracts", "test-cases",
        "acceptance-criteria", "traceability-matrix",
    )),
)


def validate() -> list[str]:
    errors: list[str] = []
    for relative in REQUIRED:
        path = ROOT / relative
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            errors.append(f"missing or empty: {relative}")

    markdown = sorted((*ROOT.glob("*.md"), *ROOT.glob("docs/**/*.md"), *ROOT.glob("specs/**/*.md")))
    for path in markdown:
        text = path.read_text(encoding="utf-8")
        for target in LINK.findall(text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            relative = target.split("#", 1)[0]
            if relative and not (path.parent / relative).resolve().exists():
                errors.append(f"broken link: {path.relative_to(ROOT)} -> {target}")

    requirements = REQUIREMENT.findall((ROOT / "specs/requirements.md").read_text(encoding="utf-8"))
    duplicates = sorted({item for item in requirements if requirements.count(item) > 1})
    if duplicates:
        errors.append(f"duplicate requirement definitions: {', '.join(duplicates)}")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"documentation validation passed: {len(REQUIRED)} required files")
