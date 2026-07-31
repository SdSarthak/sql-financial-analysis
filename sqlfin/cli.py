"""Command line entry point: ``python -m sqlfin <command>``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from sqlfin.analysis import AnalysisError, discover_analyses, get_analysis, run_analysis
from sqlfin.config import Settings, get_settings
from sqlfin.db import Database, DatabaseError, connect, redact_url
from sqlfin.loader import LoadError, load_csv
from sqlfin.report import build_report, render_markdown_table, render_table, write_csv
from sqlfin.sampledata import write_sample_csv
from sqlfin.schema import TABLE_NAME, apply_schema, drop_schema, row_count

DEFAULT_SAMPLE_PATH = "data/sample_clients.csv"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sqlfin",
        description="Run the SQL financial analysis suite against SQLite or PostgreSQL.",
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="Connection URL; defaults to $SQLFIN_DATABASE_URL or sqlite:///data/financial.db",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init-db", help="create the table, indexes and reporting views")
    init.add_argument("--reset", action="store_true", help="drop existing objects first")

    load = subparsers.add_parser("load", help="load a CSV extract into client_data")
    load.add_argument("csv_path", help="path to the CSV extract")
    load.add_argument("--truncate", action="store_true", help="delete existing rows first")
    load.add_argument("--delimiter", default=None, help="override the detected delimiter")
    load.add_argument(
        "--skip-bad-rows",
        action="store_true",
        help="skip unparseable rows instead of aborting the load",
    )
    load.add_argument("--batch-size", type=int, default=1000, help="rows per insert batch")

    sample = subparsers.add_parser("sample", help="write a synthetic extract for demos and tests")
    sample.add_argument("--rows", type=int, default=5000, help="number of rows to generate")
    sample.add_argument("--seed", type=int, default=20240131, help="random seed")
    sample.add_argument("--out", default=DEFAULT_SAMPLE_PATH, help="output CSV path")

    subparsers.add_parser("list", help="list the available analyses")

    show = subparsers.add_parser("show", help="print the SQL of one analysis")
    show.add_argument("name")

    run = subparsers.add_parser("run", help="run one analysis (or all of them)")
    run.add_argument("name", nargs="?", default=None, help="analysis name; omit to run all")
    run.add_argument("--limit", type=int, default=None, help="only show the first N rows")
    run.add_argument(
        "--format", choices=("table", "markdown", "csv"), default="table", help="output format"
    )
    run.add_argument("--out", default=None, help="write the result to this file instead of stdout")

    report = subparsers.add_parser("report", help="write report.md plus one CSV per analysis")
    report.add_argument("--out", default=None, help="output directory (default: reports/)")
    report.add_argument("--no-csv", action="store_true", help="only write the Markdown report")

    subparsers.add_parser("status", help="show connection and row count information")

    return parser


def _open(args: argparse.Namespace, settings: Settings) -> Database:
    return connect(settings.database_url)


def _print(text: str) -> None:
    sys.stdout.write(text + "\n")


def cmd_init_db(args: argparse.Namespace, settings: Settings) -> int:
    with _open(args, settings) as db:
        if args.reset:
            drop_schema(db)
        apply_schema(db, settings)
        _print(f"schema ready on {redact_url(settings.database_url)}")
    return 0


def cmd_load(args: argparse.Namespace, settings: Settings) -> int:
    with _open(args, settings) as db:
        if not db.table_exists(TABLE_NAME):
            apply_schema(db, settings)
        result = load_csv(
            db,
            args.csv_path,
            truncate=args.truncate,
            batch_size=args.batch_size,
            strict=not args.skip_bad_rows,
            delimiter=args.delimiter,
        )
        _print(f"loaded {result.rows_inserted} row(s) from {args.csv_path}")
        if result.rows_skipped:
            _print(f"skipped {result.rows_skipped} malformed row(s):")
            for message in result.errors:
                _print(f"  {message}")
        _print(f"{TABLE_NAME} now holds {row_count(db)} row(s)")
    return 0


def cmd_sample(args: argparse.Namespace, settings: Settings) -> int:
    path = write_sample_csv(args.out, rows=args.rows, seed=args.seed)
    _print(f"wrote {args.rows} synthetic row(s) to {path}")
    return 0


def cmd_list(args: argparse.Namespace, settings: Settings) -> int:
    for analysis in discover_analyses(settings.analysis_dir):
        _print(f"{analysis.name:<28} {analysis.title}")
    return 0


def cmd_show(args: argparse.Namespace, settings: Settings) -> int:
    analysis = get_analysis(args.name, discover_analyses(settings.analysis_dir))
    _print(f"-- {analysis.title} ({analysis.path.name})")
    if analysis.description:
        _print(f"-- {analysis.description}")
    _print("")
    _print(analysis.body)
    return 0


def cmd_run(args: argparse.Namespace, settings: Settings) -> int:
    analyses = discover_analyses(settings.analysis_dir)
    selected = [get_analysis(args.name, analyses)] if args.name else analyses

    with _open(args, settings) as db:
        _require_data(db)
        chunks: list[str] = []
        for analysis in selected:
            result = run_analysis(db, analysis, limit=args.limit)
            if args.format == "csv":
                if args.out and len(selected) == 1:
                    write_csv(args.out, result)
                    _print(f"wrote {args.out}")
                    return 0
                chunks.append(_result_to_csv_text(result))
            elif args.format == "markdown":
                chunks.append(f"## {analysis.title}\n\n{render_markdown_table(result)}")
            else:
                chunks.append(f"{analysis.title}\n{render_table(result)}")
        output = "\n\n".join(chunks)

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(output + "\n", encoding="utf-8")
        _print(f"wrote {args.out}")
    else:
        _print(output)
    return 0


def cmd_report(args: argparse.Namespace, settings: Settings) -> int:
    out_dir = Path(args.out) if args.out else settings.report_dir
    with _open(args, settings) as db:
        _require_data(db)
        written = build_report(
            db, discover_analyses(settings.analysis_dir), out_dir, write_csvs=not args.no_csv
        )
    _print(f"wrote {written['report']}")
    if not args.no_csv:
        _print(f"wrote {len(written) - 1} CSV extract(s) to {out_dir}")
    return 0


def cmd_status(args: argparse.Namespace, settings: Settings) -> int:
    with _open(args, settings) as db:
        _print(f"database : {redact_url(settings.database_url)} ({db.backend})")
        if db.table_exists(TABLE_NAME):
            _print(f"clients  : {row_count(db)}")
        else:
            _print("clients  : table not created yet (run: python -m sqlfin init-db)")
        _print(f"analyses : {len(discover_analyses(settings.analysis_dir))}")
    return 0


def _require_data(db: Database) -> None:
    if not db.table_exists(TABLE_NAME):
        raise DatabaseError(
            "client_data does not exist yet; run 'python -m sqlfin init-db' and then 'load'"
        )


def _result_to_csv_text(result) -> str:
    import csv as _csv
    import io

    buffer = io.StringIO()
    writer = _csv.writer(buffer, lineterminator="\n")
    writer.writerow(result.columns)
    writer.writerows(result.rows)
    return buffer.getvalue().rstrip("\n")


COMMANDS = {
    "init-db": cmd_init_db,
    "load": cmd_load,
    "sample": cmd_sample,
    "list": cmd_list,
    "show": cmd_show,
    "run": cmd_run,
    "report": cmd_report,
    "status": cmd_status,
}


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = get_settings(args.database_url)
    handler = COMMANDS[args.command]
    try:
        return handler(args, settings)
    except (AnalysisError, DatabaseError, LoadError, FileNotFoundError) as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
