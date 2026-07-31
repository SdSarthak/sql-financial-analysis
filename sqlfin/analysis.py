"""Discovery and execution of the analysis queries in ``sql/analysis``."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from sqlfin.config import Settings, get_settings
from sqlfin.db import Database, QueryResult
from sqlfin.sqltext import parse_metadata, split_statements, strip_leading_comments


class AnalysisError(RuntimeError):
    """Raised when an analysis file is malformed or unknown."""


@dataclass(frozen=True)
class Analysis:
    """One ``.sql`` analysis file: its metadata header and its single statement."""

    name: str
    title: str
    description: str
    path: Path
    sql: str

    @property
    def body(self) -> str:
        """The query with its metadata header stripped, for display purposes."""

        return strip_leading_comments(self.sql)


def _name_from_filename(path: Path) -> str:
    stem = path.stem
    head, sep, tail = stem.partition("_")
    if sep and head.isdigit():
        return tail
    return stem


def load_analysis_file(path: Path) -> Analysis:
    """Parse a single analysis file."""

    path = Path(path)
    text = path.read_text(encoding="utf-8")
    statements = split_statements(text)
    if not statements:
        raise AnalysisError(f"{path.name} contains no SQL statement")
    if len(statements) > 1:
        raise AnalysisError(
            f"{path.name} contains {len(statements)} statements; analyses must be a single query"
        )
    metadata = parse_metadata(text)
    name = metadata.get("name") or _name_from_filename(path)
    return Analysis(
        name=name,
        title=metadata.get("title") or name.replace("_", " ").capitalize(),
        description=metadata.get("description", ""),
        path=path,
        sql=statements[0],
    )


def discover_analyses(analysis_dir: Path | str | None = None, settings: Settings | None = None) -> list[Analysis]:
    """Load every ``*.sql`` analysis, ordered by filename."""

    if analysis_dir is None:
        settings = settings or get_settings()
        analysis_dir = settings.analysis_dir
    directory = Path(analysis_dir)
    if not directory.is_dir():
        raise AnalysisError(f"analysis directory not found: {directory}")

    analyses: list[Analysis] = []
    seen: dict[str, Path] = {}
    for path in sorted(directory.glob("*.sql")):
        analysis = load_analysis_file(path)
        if analysis.name in seen:
            raise AnalysisError(
                f"duplicate analysis name {analysis.name!r} in {path.name} and {seen[analysis.name].name}"
            )
        seen[analysis.name] = path
        analyses.append(analysis)
    if not analyses:
        raise AnalysisError(f"no analysis files found in {directory}")
    return analyses


def get_analysis(name: str, analyses: Sequence[Analysis] | None = None, **kwargs) -> Analysis:
    """Look up one analysis by name (or by filename stem)."""

    candidates = list(analyses) if analyses is not None else discover_analyses(**kwargs)
    wanted = name.strip().lower()
    for analysis in candidates:
        if analysis.name.lower() == wanted or analysis.path.stem.lower() == wanted:
            return analysis
    known = ", ".join(sorted(a.name for a in candidates))
    raise AnalysisError(f"unknown analysis {name!r}; available: {known}")


def run_analysis(db: Database, analysis: Analysis, *, limit: int | None = None) -> QueryResult:
    """Execute an analysis and return its rows.

    ``limit`` is applied in Python rather than by rewriting the SQL, so window functions
    that need the full result set stay correct.
    """

    result = db.query(analysis.sql)
    if limit is not None and limit >= 0:
        return QueryResult(columns=result.columns, rows=result.rows[:limit], sql=result.sql)
    return result


def run_all(db: Database, analyses: Sequence[Analysis] | None = None, *, limit: int | None = None) -> dict[str, QueryResult]:
    """Execute every analysis, keyed by name and preserving discovery order."""

    candidates = list(analyses) if analyses is not None else discover_analyses()
    return {analysis.name: run_analysis(db, analysis, limit=limit) for analysis in candidates}
