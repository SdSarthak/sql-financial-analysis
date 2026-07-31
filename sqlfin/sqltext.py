"""Helpers for reading the ``.sql`` files that hold the actual analysis."""

from __future__ import annotations

import re

_METADATA_LINE = re.compile(r"^\s*--\s*([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$")
_CONTINUATION_LINE = re.compile(r"^\s*--\s{2,}(\S.*)$")


def split_statements(script: str) -> list[str]:
    """Split a SQL script into individual statements.

    Semicolons inside string literals, quoted identifiers and comments are ignored, which
    is all the sophistication the schema/view/analysis files in this project need.
    """

    statements: list[str] = []
    buffer: list[str] = []
    quote: str | None = None
    in_line_comment = False
    in_block_comment = False

    index = 0
    length = len(script)
    while index < length:
        char = script[index]
        nxt = script[index + 1] if index + 1 < length else ""

        if in_line_comment:
            buffer.append(char)
            if char == "\n":
                in_line_comment = False
            index += 1
            continue

        if in_block_comment:
            buffer.append(char)
            if char == "*" and nxt == "/":
                buffer.append(nxt)
                in_block_comment = False
                index += 2
                continue
            index += 1
            continue

        if quote is not None:
            buffer.append(char)
            if char == quote:
                if nxt == quote:  # escaped quote, e.g. 'it''s'
                    buffer.append(nxt)
                    index += 2
                    continue
                quote = None
            index += 1
            continue

        if char == "-" and nxt == "-":
            in_line_comment = True
            buffer.append(char)
            index += 1
            continue

        if char == "/" and nxt == "*":
            in_block_comment = True
            buffer.append(char)
            buffer.append(nxt)
            index += 2
            continue

        if char in {"'", '"'}:
            quote = char
            buffer.append(char)
            index += 1
            continue

        if char == ";":
            statements.append("".join(buffer))
            buffer = []
            index += 1
            continue

        buffer.append(char)
        index += 1

    statements.append("".join(buffer))
    return [statement.strip() for statement in statements if statement.strip()]


def strip_leading_comments(sql: str) -> str:
    """Remove the leading ``--`` header block from a query."""

    lines = sql.splitlines()
    start = 0
    for position, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("--") or not stripped:
            start = position + 1
            continue
        break
    return "\n".join(lines[start:]).strip()


def parse_metadata(sql: str) -> dict[str, str]:
    """Read ``-- key: value`` headers from the top of a SQL file.

    Values may wrap onto following comment lines that are indented by two or more spaces
    after the ``--`` marker.
    """

    metadata: dict[str, str] = {}
    current_key: str | None = None
    for line in sql.splitlines():
        stripped = line.strip()
        if not stripped:
            if metadata:
                break
            continue
        if not stripped.startswith("--"):
            break
        continuation = _CONTINUATION_LINE.match(line)
        if current_key and continuation and not _METADATA_LINE.match(line):
            metadata[current_key] = f"{metadata[current_key]} {continuation.group(1).strip()}".strip()
            continue
        match = _METADATA_LINE.match(line)
        if not match:
            current_key = None
            continue
        current_key = match.group(1).strip().lower()
        metadata[current_key] = match.group(2).strip()
    return metadata
