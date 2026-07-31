"""Shared fixtures: an in-memory database loaded with the synthetic client extract."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlfin.analysis import discover_analyses  # noqa: E402
from sqlfin.config import get_settings  # noqa: E402
from sqlfin.db import connect  # noqa: E402
from sqlfin.loader import load_csv  # noqa: E402
from sqlfin.schema import apply_schema  # noqa: E402

FIXTURE_CSV = PROJECT_ROOT / "tests" / "fixtures" / "sample_clients.csv"

MEMORY_URL = "sqlite:///:memory:"


@pytest.fixture
def settings():
    return get_settings(MEMORY_URL, env={}, use_dotenv=False)


@pytest.fixture
def db(settings):
    with connect(settings.database_url) as database:
        apply_schema(database, settings)
        yield database


@pytest.fixture
def loaded_db(db, settings):
    load_csv(db, FIXTURE_CSV)
    return db


@pytest.fixture
def analyses(settings):
    return discover_analyses(settings.analysis_dir)


@pytest.fixture
def fixture_csv():
    return FIXTURE_CSV
