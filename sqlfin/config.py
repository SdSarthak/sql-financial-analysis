"""Configuration resolved from the environment.

No credentials are ever hardcoded: the connection string comes from the
``SQLFIN_DATABASE_URL`` environment variable (optionally seeded from a local ``.env``
file, which is git-ignored). The default is a file-backed SQLite database so the project
runs end to end without any server.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, MutableMapping

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ENV_DATABASE_URL = "SQLFIN_DATABASE_URL"
ENV_REPORT_DIR = "SQLFIN_REPORT_DIR"

DEFAULT_DATABASE_URL = "sqlite:///data/financial.db"
DEFAULT_REPORT_DIR = "reports"


@dataclass(frozen=True)
class Settings:
    """Everything the runner needs to locate SQL, the database and output."""

    database_url: str
    sql_dir: Path
    report_dir: Path

    @property
    def schema_file(self) -> Path:
        return self.sql_dir / "schema.sql"

    @property
    def views_file(self) -> Path:
        return self.sql_dir / "views.sql"

    @property
    def analysis_dir(self) -> Path:
        return self.sql_dir / "analysis"


def parse_dotenv(text: str) -> dict[str, str]:
    """Parse ``KEY=value`` lines from a ``.env`` file body.

    Supports ``export`` prefixes, ``#`` comments and single/double quoted values.
    Deliberately minimal so the project keeps a zero-dependency runtime.
    """

    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        key, sep, value = line.partition("=")
        if not sep:
            continue
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def load_dotenv(path: Path | None = None, env: MutableMapping[str, str] | None = None) -> dict[str, str]:
    """Load ``.env`` into ``env`` without overriding variables already set."""

    env = os.environ if env is None else env
    path = PROJECT_ROOT / ".env" if path is None else path
    if not path.is_file():
        return {}
    values = parse_dotenv(path.read_text(encoding="utf-8"))
    for key, value in values.items():
        env.setdefault(key, value)
    return values


def get_settings(
    database_url: str | None = None,
    *,
    env: Mapping[str, str] | None = None,
    project_root: Path | None = None,
    use_dotenv: bool = True,
) -> Settings:
    """Build :class:`Settings`, preferring explicit arguments over the environment."""

    if use_dotenv and env is None:
        load_dotenv()
    env = os.environ if env is None else env
    root = PROJECT_ROOT if project_root is None else Path(project_root)

    url = database_url or env.get(ENV_DATABASE_URL) or DEFAULT_DATABASE_URL
    report_dir = Path(env.get(ENV_REPORT_DIR) or DEFAULT_REPORT_DIR)
    if not report_dir.is_absolute():
        report_dir = root / report_dir

    return Settings(database_url=url, sql_dir=root / "sql", report_dir=report_dir)
