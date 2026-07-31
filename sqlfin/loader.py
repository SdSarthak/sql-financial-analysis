"""CSV ingestion for the client book.

The loader accepts the raw UCI "Bank Marketing" export (semicolon separated, short
column names such as ``default``/``housing``/``y``) as well as files that already use the
long column names from ``sql/schema.sql``. Values are normalised and type-checked before
they reach the database so a malformed extract fails loudly instead of silently skewing
the analysis.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Sequence

from sqlfin.db import Database
from sqlfin.schema import TABLE_NAME

#: Table columns in insertion order (``client_id`` is assigned by the loader).
TABLE_COLUMNS: tuple[str, ...] = (
    "age",
    "job",
    "marital",
    "education",
    "default_status",
    "balance",
    "housing_loan",
    "personal_loan",
    "contact",
    "last_contact_day",
    "last_contact_month",
    "last_contact_duration",
    "campaign_contacts",
    "days_since_last_contact",
    "previous_contacts",
    "previous_outcome",
    "subscribed",
)

#: Raw dataset header -> schema column.
COLUMN_ALIASES: dict[str, str] = {
    "default": "default_status",
    "housing": "housing_loan",
    "loan": "personal_loan",
    "day": "last_contact_day",
    "month": "last_contact_month",
    "duration": "last_contact_duration",
    "campaign": "campaign_contacts",
    "pdays": "days_since_last_contact",
    "previous": "previous_contacts",
    "poutcome": "previous_outcome",
    "y": "subscribed",
    "deposit": "subscribed",
}

INTEGER_COLUMNS = frozenset(
    {
        "age",
        "last_contact_day",
        "last_contact_duration",
        "campaign_contacts",
        "days_since_last_contact",
        "previous_contacts",
    }
)
NUMERIC_COLUMNS = frozenset({"balance"})
YES_NO_COLUMNS = frozenset({"default_status", "housing_loan", "personal_loan", "subscribed"})
REQUIRED_COLUMNS = frozenset({"age", "balance", "subscribed"})

#: Cap on how many per-row failures a lenient load reports back to the caller.
MAX_REPORTED_ERRORS = 20

TRUE_TOKENS = {"yes", "y", "true", "1", "t"}
FALSE_TOKENS = {"no", "n", "false", "0", "f"}

MONTH_ABBREVIATIONS = {
    "jan": "jan", "january": "jan",
    "feb": "feb", "february": "feb",
    "mar": "mar", "march": "mar",
    "apr": "apr", "april": "apr",
    "may": "may",
    "jun": "jun", "june": "jun",
    "jul": "jul", "july": "jul",
    "aug": "aug", "august": "aug",
    "sep": "sep", "sept": "sep", "september": "sep",
    "oct": "oct", "october": "oct",
    "nov": "nov", "november": "nov",
    "dec": "dec", "december": "dec",
}

DEFAULTS: dict[str, Any] = {
    "job": "unknown",
    "marital": "unknown",
    "education": "unknown",
    "default_status": "no",
    "housing_loan": "no",
    "personal_loan": "no",
    "contact": "unknown",
    "last_contact_day": 0,
    "last_contact_month": "unknown",
    "last_contact_duration": 0,
    "campaign_contacts": 1,
    "days_since_last_contact": -1,
    "previous_contacts": 0,
    "previous_outcome": "unknown",
}


class LoadError(ValueError):
    """Raised when the CSV cannot be mapped onto the schema."""


@dataclass
class LoadResult:
    """Outcome of a load: how many rows landed, and what was rejected."""

    rows_inserted: int = 0
    rows_skipped: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def rows_seen(self) -> int:
        return self.rows_inserted + self.rows_skipped


def normalise_header(name: str) -> str:
    cleaned = (name or "").strip().strip('"').strip().lower()
    cleaned = cleaned.replace(" ", "_").replace("-", "_")
    return COLUMN_ALIASES.get(cleaned, cleaned)


def map_headers(fieldnames: Sequence[str] | None) -> dict[str, str]:
    """Map raw CSV headers onto schema columns, ignoring unknown columns."""

    if not fieldnames:
        raise LoadError("CSV file has no header row")
    mapping: dict[str, str] = {}
    for raw in fieldnames:
        target = normalise_header(raw)
        if target in TABLE_COLUMNS:
            mapping[raw] = target
    missing = REQUIRED_COLUMNS - set(mapping.values())
    if missing:
        raise LoadError(
            "CSV is missing required column(s): " + ", ".join(sorted(missing))
        )
    return mapping


def sniff_delimiter(sample: str) -> str:
    """Pick the delimiter from the header line (the raw dataset uses ``;``)."""

    header = sample.splitlines()[0] if sample.splitlines() else ""
    counts = {candidate: header.count(candidate) for candidate in (";", ",", "\t", "|")}
    best = max(counts, key=lambda candidate: counts[candidate])
    return best if counts[best] > 0 else ","


def _coerce_yes_no(column: str, value: str) -> str:
    token = value.strip().strip('"').lower()
    if token in TRUE_TOKENS:
        return "yes"
    if token in FALSE_TOKENS:
        return "no"
    raise LoadError(f"column {column!r} expects yes/no, got {value!r}")


def _coerce_int(column: str, value: str) -> int:
    token = value.strip().strip('"')
    try:
        return int(float(token))
    except (TypeError, ValueError) as exc:
        raise LoadError(f"column {column!r} expects an integer, got {value!r}") from exc


def _coerce_float(column: str, value: str) -> float:
    token = value.strip().strip('"').replace(",", "")
    try:
        return float(token)
    except (TypeError, ValueError) as exc:
        raise LoadError(f"column {column!r} expects a number, got {value!r}") from exc


def coerce_row(raw: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
    """Turn one raw CSV record into a fully typed, schema-shaped row."""

    row: dict[str, Any] = dict(DEFAULTS)
    for source, target in mapping.items():
        value = raw.get(source)
        if value is None or str(value).strip() == "":
            if target in REQUIRED_COLUMNS:
                raise LoadError(f"column {target!r} is required but empty")
            continue
        text = str(value)
        if target in YES_NO_COLUMNS:
            row[target] = _coerce_yes_no(target, text)
        elif target in INTEGER_COLUMNS:
            row[target] = _coerce_int(target, text)
        elif target in NUMERIC_COLUMNS:
            row[target] = _coerce_float(target, text)
        elif target == "last_contact_month":
            token = text.strip().strip('"').lower()
            row[target] = MONTH_ABBREVIATIONS.get(token, token[:10])
        else:
            row[target] = text.strip().strip('"').lower()

    if row["age"] < 0:
        raise LoadError(f"age must be non-negative, got {row['age']}")
    return row


def read_rows(
    csv_path: Path | str,
    *,
    delimiter: str | None = None,
    strict: bool = True,
    on_error: Callable[[str], None] | None = None,
) -> Iterator[dict[str, Any]]:
    """Yield typed rows from ``csv_path``.

    In strict mode the first unparseable record raises :class:`LoadError`; otherwise the
    record is reported through ``on_error`` and skipped.
    """

    path = Path(csv_path)
    if not path.is_file():
        raise LoadError(f"CSV file not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(8192)
        handle.seek(0)
        reader = csv.DictReader(handle, delimiter=delimiter or sniff_delimiter(sample))
        mapping = map_headers(reader.fieldnames)
        for line_number, raw in enumerate(reader, start=2):
            try:
                row = coerce_row(raw, mapping)
            except LoadError as exc:
                message = f"line {line_number}: {exc}"
                if strict:
                    raise LoadError(message) from exc
                if on_error is not None:
                    on_error(message)
                continue
            yield row


def iter_rows(csv_path: Path | str, delimiter: str | None = None) -> Iterator[dict[str, Any]]:
    """Strict convenience wrapper around :func:`read_rows`."""

    return read_rows(csv_path, delimiter=delimiter, strict=True)


def insert_rows(db: Database, rows: Iterable[dict[str, Any]], *, batch_size: int = 1000) -> int:
    """Insert typed rows, assigning ``client_id`` sequentially after the current max."""

    columns = ("client_id",) + TABLE_COLUMNS
    placeholders = ", ".join([db.placeholder] * len(columns))
    statement = (
        f"INSERT INTO {TABLE_NAME} ({', '.join(columns)}) VALUES ({placeholders})"
    )
    next_id = int(db.scalar(f"SELECT COALESCE(MAX(client_id), 0) FROM {TABLE_NAME}") or 0) + 1

    inserted = 0
    batch: list[tuple[Any, ...]] = []
    for row in rows:
        batch.append((next_id,) + tuple(row[column] for column in TABLE_COLUMNS))
        next_id += 1
        if len(batch) >= batch_size:
            inserted += db.executemany(statement, batch)
            batch = []
    if batch:
        inserted += db.executemany(statement, batch)
    return inserted


def load_csv(
    db: Database,
    csv_path: Path | str,
    *,
    truncate: bool = False,
    batch_size: int = 1000,
    strict: bool = True,
    delimiter: str | None = None,
) -> LoadResult:
    """Load a CSV extract into ``client_data``.

    With ``strict=False`` unparseable rows are counted and skipped instead of aborting
    the whole load.
    """

    if truncate:
        db.execute(f"DELETE FROM {TABLE_NAME}")

    result = LoadResult()

    def _record_error(message: str) -> None:
        result.rows_skipped += 1
        if len(result.errors) < MAX_REPORTED_ERRORS:
            result.errors.append(message)

    rows = read_rows(
        Path(csv_path), delimiter=delimiter, strict=strict, on_error=_record_error
    )
    result.rows_inserted = insert_rows(db, rows, batch_size=batch_size)
    db.commit()
    return result
