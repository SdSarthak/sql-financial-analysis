"""Rendering of query results: fixed-width tables, CSV and a Markdown report pack."""

from __future__ import annotations

import csv
import datetime as _dt
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable, Sequence

from sqlfin.analysis import Analysis, run_analysis
from sqlfin.db import Database, QueryResult, redact_url

NULL_DISPLAY = "-"


def format_value(value: Any) -> str:
    """Render a single cell for text output."""

    if value is None:
        return NULL_DISPLAY
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, Decimal):
        value = float(value)
    if isinstance(value, float):
        if value == int(value) and abs(value) < 1e15:
            return f"{int(value):,}"
        return f"{value:,.2f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def render_table(result: QueryResult) -> str:
    """Render a result as an aligned fixed-width table for the terminal."""

    if not result.columns:
        return "(no columns)"
    rendered = [[format_value(cell) for cell in row] for row in result.rows]
    widths = [len(column) for column in result.columns]
    for row in rendered:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    lines = [
        "  ".join(column.ljust(widths[index]) for index, column in enumerate(result.columns)).rstrip(),
        "  ".join("-" * widths[index] for index in range(len(result.columns))),
    ]
    for row in rendered:
        lines.append("  ".join(cell.ljust(widths[index]) for index, cell in enumerate(row)).rstrip())
    if not rendered:
        lines.append("(no rows)")
    return "\n".join(lines)


def render_markdown_table(result: QueryResult) -> str:
    """Render a result as a GitHub-flavoured Markdown table."""

    if not result.columns:
        return "_no columns_"
    header = "| " + " | ".join(result.columns) + " |"
    divider = "| " + " | ".join("---" for _ in result.columns) + " |"
    lines = [header, divider]
    for row in result.rows:
        lines.append("| " + " | ".join(format_value(cell) for cell in row) + " |")
    if not result.rows:
        lines.append("| " + " | ".join(NULL_DISPLAY for _ in result.columns) + " |")
    return "\n".join(lines)


def write_csv(path: Path | str, result: QueryResult) -> Path:
    """Write a result to CSV (raw values, not display-formatted)."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(result.columns)
        writer.writerows(result.rows)
    return target


def render_markdown_report(
    sections: Sequence[tuple[Analysis, QueryResult]],
    *,
    title: str = "Financial analysis report",
    generated_at: _dt.datetime | None = None,
    source: str = "",
) -> str:
    """Assemble the full Markdown report from analysis/result pairs."""

    stamp = (generated_at or _dt.datetime.now()).strftime("%Y-%m-%d %H:%M")
    lines = [f"# {title}", "", f"Generated {stamp}."]
    if source:
        lines.append(f"Source: `{source}`.")
    lines.extend(["", "## Contents", ""])
    for analysis, _ in sections:
        anchor = analysis.name.replace("_", "-")
        lines.append(f"- [{analysis.title}](#{anchor})")
    lines.append("")

    for analysis, result in sections:
        lines.extend([f"## {analysis.title}", ""])
        if analysis.description:
            lines.extend([analysis.description, ""])
        lines.extend([f"`{analysis.name}` - {len(result)} row(s)", ""])
        lines.extend([render_markdown_table(result), ""])
    return "\n".join(lines).rstrip() + "\n"


def build_report(
    db: Database,
    analyses: Iterable[Analysis],
    out_dir: Path | str,
    *,
    write_csvs: bool = True,
    generated_at: _dt.datetime | None = None,
) -> dict[str, Path]:
    """Run every analysis and write ``report.md`` plus one CSV per analysis."""

    directory = Path(out_dir)
    directory.mkdir(parents=True, exist_ok=True)

    sections: list[tuple[Analysis, QueryResult]] = []
    written: dict[str, Path] = {}
    for analysis in analyses:
        result = run_analysis(db, analysis)
        sections.append((analysis, result))
        if write_csvs:
            written[analysis.name] = write_csv(directory / f"{analysis.name}.csv", result)

    report_path = directory / "report.md"
    report_path.write_text(
        render_markdown_report(sections, generated_at=generated_at, source=redact_url(db.url)),
        encoding="utf-8",
    )
    written["report"] = report_path
    return written
