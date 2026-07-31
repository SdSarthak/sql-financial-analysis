"""Thin database abstraction over SQLite (default) and PostgreSQL (optional).

Only the handful of operations the runner needs are wrapped, which keeps the analysis
SQL itself completely engine-agnostic.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

from sqlfin.sqltext import split_statements

SQLITE_SCHEMES = ("sqlite:///", "sqlite://")
POSTGRES_SCHEMES = ("postgresql://", "postgres://", "postgresql+psycopg://")

MEMORY_TOKENS = {":memory:", "", "/:memory:"}


class DatabaseError(RuntimeError):
    """Raised for configuration problems with the database connection."""


class MissingDriverError(DatabaseError):
    """Raised when a backend is requested but its driver is not installed."""


@dataclass(frozen=True)
class QueryResult:
    """Column names plus fully materialised rows for a single query."""

    columns: list[str]
    rows: list[tuple[Any, ...]]
    sql: str = field(default="", repr=False)

    def __len__(self) -> int:
        return len(self.rows)

    def __iter__(self):
        return iter(self.rows)

    def dicts(self) -> list[dict[str, Any]]:
        return [dict(zip(self.columns, row)) for row in self.rows]

    def first(self) -> dict[str, Any] | None:
        rows = self.dicts()
        return rows[0] if rows else None


def backend_for(url: str) -> str:
    """Return ``"sqlite"`` or ``"postgresql"`` for a connection URL."""

    lowered = url.strip().lower()
    if lowered.startswith(SQLITE_SCHEMES):
        return "sqlite"
    if lowered.startswith(POSTGRES_SCHEMES):
        return "postgresql"
    raise DatabaseError(
        f"unsupported database URL {url!r}; expected a sqlite:// or postgresql:// URL"
    )


def redact_url(url: str) -> str:
    """Hide any embedded credentials so a URL is safe to print or write to a report."""

    if "@" not in url or "://" not in url:
        return url
    scheme, _, remainder = url.partition("://")
    credentials, _, host = remainder.rpartition("@")
    if not credentials:
        return url
    user = credentials.split(":", 1)[0]
    return f"{scheme}://{user}:***@{host}"


def sqlite_path(url: str) -> str:
    """Extract the filesystem path (or ``:memory:``) from a SQLite URL."""

    remainder = url.strip()
    for scheme in SQLITE_SCHEMES:
        if remainder.lower().startswith(scheme):
            remainder = remainder[len(scheme) :]
            break
    if remainder in MEMORY_TOKENS:
        return ":memory:"
    return remainder


class Database:
    """A live connection with the small amount of behaviour the project needs."""

    def __init__(self, connection: Any, backend: str, url: str) -> None:
        self._connection = connection
        self.backend = backend
        self.url = url

    # -- lifecycle -----------------------------------------------------------------
    @property
    def connection(self) -> Any:
        return self._connection

    @property
    def placeholder(self) -> str:
        return "?" if self.backend == "sqlite" else "%s"

    def commit(self) -> None:
        self._connection.commit()

    def rollback(self) -> None:
        self._connection.rollback()

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type is None:
                self.commit()
            else:
                self.rollback()
        finally:
            self.close()

    # -- statements ----------------------------------------------------------------
    def execute(self, sql: str, params: Sequence[Any] = ()) -> None:
        cursor = self._connection.cursor()
        try:
            cursor.execute(sql, tuple(params))
        finally:
            cursor.close()

    def executemany(self, sql: str, rows: Iterable[Sequence[Any]]) -> int:
        batch = [tuple(row) for row in rows]
        if not batch:
            return 0
        cursor = self._connection.cursor()
        try:
            cursor.executemany(sql, batch)
        finally:
            cursor.close()
        return len(batch)

    def execute_script(self, script: str) -> int:
        """Run every statement in a SQL script; returns the statement count."""

        statements = split_statements(script)
        for statement in statements:
            self.execute(statement)
        return len(statements)

    def execute_file(self, path: Path) -> int:
        return self.execute_script(Path(path).read_text(encoding="utf-8"))

    def query(self, sql: str, params: Sequence[Any] = ()) -> QueryResult:
        cursor = self._connection.cursor()
        try:
            cursor.execute(sql, tuple(params))
            description = cursor.description or []
            columns = [column[0] for column in description]
            rows = [tuple(row) for row in cursor.fetchall()]
        finally:
            cursor.close()
        return QueryResult(columns=columns, rows=rows, sql=sql)

    def scalar(self, sql: str, params: Sequence[Any] = ()) -> Any:
        result = self.query(sql, params)
        if not result.rows:
            return None
        return result.rows[0][0]

    def table_exists(self, table: str) -> bool:
        if self.backend == "sqlite":
            found = self.scalar(
                "SELECT COUNT(*) FROM sqlite_master WHERE type IN ('table','view') AND name = ?",
                (table,),
            )
        else:
            found = self.scalar("SELECT to_regclass(%s) IS NOT NULL", (table,))
        return bool(found)


def connect(url: str) -> Database:
    """Open a connection for ``url``, creating parent directories for SQLite files."""

    backend = backend_for(url)
    if backend == "sqlite":
        path = sqlite_path(url)
        if path != ":memory:":
            parent = Path(path).expanduser().parent
            if str(parent):
                parent.mkdir(parents=True, exist_ok=True)
            path = str(Path(path).expanduser())
        connection = sqlite3.connect(path)
        connection.execute("PRAGMA foreign_keys = ON")
        return Database(connection, backend, url)

    try:  # pragma: no cover - exercised only when PostgreSQL is configured
        import psycopg
    except ImportError as exc:  # pragma: no cover
        raise MissingDriverError(
            "PostgreSQL support requires the psycopg driver: pip install 'psycopg[binary]'"
        ) from exc

    dsn = url.replace("postgresql+psycopg://", "postgresql://", 1)
    connection = psycopg.connect(dsn)  # pragma: no cover
    return Database(connection, backend, url)  # pragma: no cover
