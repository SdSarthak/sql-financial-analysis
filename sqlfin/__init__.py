"""SQL-first financial analysis toolkit for a retail bank client book.

The analytical work lives in ``sql/`` as plain, portable SQL. This package is the thin
runner around it: it bootstraps a schema, loads a CSV extract, executes the analysis
queries against SQLite or PostgreSQL and renders the results as tables, CSV or Markdown.
"""

from sqlfin.analysis import Analysis, discover_analyses, get_analysis, run_analysis
from sqlfin.config import Settings, get_settings
from sqlfin.db import Database, QueryResult, connect
from sqlfin.loader import LoadError, LoadResult, load_csv
from sqlfin.schema import apply_schema

__all__ = [
    "Analysis",
    "Database",
    "LoadError",
    "LoadResult",
    "QueryResult",
    "Settings",
    "apply_schema",
    "connect",
    "discover_analyses",
    "get_analysis",
    "get_settings",
    "load_csv",
    "run_analysis",
]

__version__ = "1.0.0"
