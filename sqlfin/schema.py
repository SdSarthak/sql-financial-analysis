"""Schema and reporting-view bootstrap."""

from __future__ import annotations

from pathlib import Path

from sqlfin.config import Settings, get_settings
from sqlfin.db import Database

TABLE_NAME = "client_data"
VIEW_NAMES = ("v_client_profile", "v_segment_conversion")


def apply_schema(db: Database, settings: Settings | None = None, *, views: bool = True) -> None:
    """Create the client table, its indexes and (optionally) the reporting views."""

    settings = settings or get_settings(db.url)
    _require(settings.schema_file)
    db.execute_file(settings.schema_file)
    if views:
        _require(settings.views_file)
        db.execute_file(settings.views_file)
    db.commit()


def drop_schema(db: Database) -> None:
    """Drop the reporting views and the client table (used by ``init-db --reset``)."""

    for view in VIEW_NAMES:
        db.execute(f"DROP VIEW IF EXISTS {view}")
    db.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
    db.commit()


def truncate(db: Database) -> None:
    """Remove every client row while keeping the schema in place."""

    db.execute(f"DELETE FROM {TABLE_NAME}")
    db.commit()


def row_count(db: Database) -> int:
    return int(db.scalar(f"SELECT COUNT(*) FROM {TABLE_NAME}") or 0)


def _require(path: Path) -> None:
    if not Path(path).is_file():
        raise FileNotFoundError(f"missing SQL file: {path}")
