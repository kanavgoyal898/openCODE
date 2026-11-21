"""Pinned tree-sitter adapters that tokenize bytes without executing source."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass

import tree_sitter_java
import tree_sitter_javascript
import tree_sitter_python
import tree_sitter_typescript
from tree_sitter import Language, Node, Parser

from opencode_core.parsers.adapters import AdapterRegistry
from opencode_core.parsers.model import (
    InvalidEncodingError,
    ParseCoverageError,
    StructuralNode,
    Token,
    TokenizationResult,
    TokenKind,
)

_COMMENT_TYPES = {"comment", "line_comment", "block_comment"}
_STRING_MARKERS = ("string", "template_string", "character_literal")
_NUMBER_MARKERS = ("integer", "float", "number", "decimal", "hex", "octal", "binary")
_IDENTIFIER_MARKERS = ("identifier",)
_BOOLEAN_TEXT = {"true", "false", "True", "False"}
_NULL_TEXT = {"null", "None", "undefined"}
_PUNCTUATION = frozenset("()[]{}.,:;")
_SCOPE_TYPES = {
    "arrow_function",
    "class_declaration",
    "class_definition",
    "function_declaration",
    "function_definition",
    "generator_function_declaration",
    "lambda",
    "method_declaration",
    "method_definition",
}


def _line_starts(source: bytes) -> tuple[int, ...]:
    starts = [0]
    index = 0
    while index < len(source):
        if source[index : index + 2] == b"\r\n":
            index += 2
            starts.append(index)
        elif source[index] in (10, 13):
            index += 1
            starts.append(index)
        else:
            index += 1
    return tuple(starts)


def _coordinate(source: bytes, starts: tuple[int, ...], offset: int) -> tuple[int, int]:
    import bisect

    line_index = bisect.bisect_right(starts, offset) - 1
    prefix = source[starts[line_index] : offset].decode("utf-8")
    return line_index + 1, len(prefix) + 1


def _error_nodes(root: Node) -> tuple[Node, ...]:
    errors: list[Node] = []
    stack = [root]
    while stack:
        node = stack.pop()
        if node.is_error or node.is_missing:
            errors.append(node)
        stack.extend(reversed(node.children))
    return tuple(errors)


def _token_nodes(root: Node) -> Iterator[Node]:
    stack = [root]
    while stack:
        node = stack.pop()
        node_type = node.type.casefold()
        if node_type in _COMMENT_TYPES:
            continue
        if any(marker in node_type for marker in _STRING_MARKERS):
            yield node
            continue
        if node.child_count == 0:
            if not node.is_missing and node.end_byte > node.start_byte:
                yield node
            continue
        stack.extend(reversed(node.children))


def _structural_nodes(root: Node, byte_offset: int) -> tuple[StructuralNode, ...]:
    result: list[StructuralNode] = []
    stack = [(root, 0)]
    while stack:
        node, depth = stack.pop()
        if node.is_named and node.type.casefold() not in _COMMENT_TYPES and node.child_count:
            result.append(
                StructuralNode(
                    node.type,
                    node.start_byte + byte_offset,
                    node.end_byte + byte_offset,
                    depth,
                )
            )
        stack.extend((child, depth + 1) for child in reversed(node.children))
    return tuple(result)


def _kind(node: Node, text: str) -> TokenKind:
    node_type = node.type.casefold()
    if text in _BOOLEAN_TEXT:
        return "boolean"
    if text in _NULL_TEXT:
        return "null"
    if any(marker in node_type for marker in _STRING_MARKERS):
        return "string"
    if any(marker in node_type for marker in _NUMBER_MARKERS):
        return "number"
    if any(marker in node_type for marker in _IDENTIFIER_MARKERS):
        return "identifier"
    if not node.is_named:
        if text in _PUNCTUATION:
            return "punctuation"
        if text.isidentifier():
            return "keyword"
        return "operator"
    return "other"


def _scope_nodes(root: Node) -> dict[tuple[int, int, str], str]:
    scopes: list[Node] = []
    stack = [root]
    while stack:
        node = stack.pop()
        if node.type in _SCOPE_TYPES:
            scopes.append(node)
        stack.extend(reversed(node.children))
    return {
        (node.start_byte, node.end_byte, node.type): f"scope-{index}"
        for index, node in enumerate(scopes)
    }


def _identifier_metadata(
    node: Node, source: bytes, scopes: dict[tuple[int, int, str], str]
) -> tuple[str, str]:
    prefix = source[max(0, node.start_byte - 8) : node.start_byte].rstrip()
    role = "member" if prefix.endswith(b".") else "local"
    parent = node.parent
    while parent is not None:
        key = (parent.start_byte, parent.end_byte, parent.type)
        if key in scopes:
            return role, scopes[key]
        parent = parent.parent
    return role, "module"


@dataclass(frozen=True, slots=True)
class TreeSitterAdapter:
    language: str
    grammar_version: str
    extensions: frozenset[str]
    language_factory: Callable[[], object]

    @property
    def version(self) -> str:
        return f"tree-sitter-{self.language}@{self.grammar_version}"

    def tokenize(self, source: bytes) -> TokenizationResult:
        bom_bytes = 3 if source.startswith(b"\xef\xbb\xbf") else 0
        payload = source[bom_bytes:]
        try:
            payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise InvalidEncodingError("source must be valid UTF-8") from error

        parser = Parser(Language(self.language_factory()))
        tree = parser.parse(payload)
        errors = _error_nodes(tree.root_node)
        error_bytes = sum(max(node.end_byte - node.start_byte, 1) for node in errors)
        coverage = 1.0 if not payload else max(0.0, 1.0 - error_bytes / len(payload))
        if coverage < 0.9:
            raise ParseCoverageError(
                f"{self.language} lexical coverage {coverage:.3f} is below 0.900"
            )

        starts = _line_starts(payload)
        scopes = _scope_nodes(tree.root_node)
        tokens: list[Token] = []
        for node in _token_nodes(tree.root_node):
            raw = payload[node.start_byte : node.end_byte]
            text = raw.decode("utf-8")
            start_line, start_column = _coordinate(payload, starts, node.start_byte)
            end_line, end_column = _coordinate(payload, starts, node.end_byte)
            kind = _kind(node, text)
            role, scope_id = (
                _identifier_metadata(node, payload, scopes)
                if kind == "identifier"
                else (None, "module")
            )
            tokens.append(
                Token(
                    kind=kind,
                    canonical=text,
                    start_byte=node.start_byte + bom_bytes,
                    end_byte=node.end_byte + bom_bytes,
                    start_line=start_line,
                    start_column=start_column,
                    end_line=end_line,
                    end_column=end_column,
                    role=role,
                    scope_id=scope_id,
                    subtype=node.type,
                )
            )
        return TokenizationResult(
            language=self.language,
            adapter_version=self.version,
            tokens=tuple(tokens),
            degraded=bool(errors),
            error_count=len(errors),
            lexical_coverage=coverage,
            structural_nodes=_structural_nodes(tree.root_node, bom_bytes),
        )


def default_registry() -> AdapterRegistry:
    return AdapterRegistry(
        (
            TreeSitterAdapter(
                "python", "0.25.0", frozenset({".py", ".pyi"}), tree_sitter_python.language
            ),
            TreeSitterAdapter(
                "javascript",
                "0.25.0",
                frozenset({".js", ".mjs", ".cjs", ".jsx"}),
                tree_sitter_javascript.language,
            ),
            TreeSitterAdapter(
                "typescript",
                "0.23.2",
                frozenset({".ts", ".tsx", ".mts", ".cts"}),
                tree_sitter_typescript.language_typescript,
            ),
            TreeSitterAdapter("java", "0.23.5", frozenset({".java"}), tree_sitter_java.language),
        )
    )
