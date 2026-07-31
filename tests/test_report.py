import csv
import datetime as dt

from sqlfin.analysis import get_analysis
from sqlfin.db import QueryResult
from sqlfin.report import (
    build_report,
    format_value,
    render_markdown_report,
    render_markdown_table,
    render_table,
    write_csv,
)


def make_result():
    return QueryResult(columns=["job", "clients", "rate"], rows=[("retired", 2, 73.905), ("student", 1, None)])


def test_format_value_handles_types():
    assert format_value(None) == "-"
    assert format_value(1234567) == "1,234,567"
    assert format_value(1234.5) == "1,234.50"
    assert format_value(12.0) == "12"
    assert format_value("retired") == "retired"
    assert format_value(True) == "yes"


def test_render_table_aligns_columns():
    text = render_table(make_result())
    lines = text.splitlines()
    assert lines[0].startswith("job")
    assert set(lines[1]) <= {"-", " "}
    assert "retired" in lines[2]
    assert lines[3].endswith("-")


def test_render_table_reports_empty_result():
    text = render_table(QueryResult(columns=["a"], rows=[]))
    assert "(no rows)" in text


def test_render_markdown_table_shape():
    text = render_markdown_table(make_result())
    lines = text.splitlines()
    assert lines[0] == "| job | clients | rate |"
    assert lines[1] == "| --- | --- | --- |"
    assert lines[2] == "| retired | 2 | 73.91 |"


def test_write_csv_round_trips_raw_values(tmp_path):
    path = write_csv(tmp_path / "out" / "result.csv", make_result())
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    assert rows[0] == ["job", "clients", "rate"]
    assert rows[1] == ["retired", "2", "73.905"]


def test_render_markdown_report_has_toc_and_sections(analyses, loaded_db):
    from sqlfin.analysis import run_analysis

    selected = [get_analysis("book_overview", analyses)]
    sections = [(a, run_analysis(loaded_db, a)) for a in selected]
    text = render_markdown_report(
        sections, generated_at=dt.datetime(2024, 1, 31, 9, 30), source="sqlite:///demo.db"
    )
    assert "Generated 2024-01-31 09:30" in text
    assert "- [Client book overview](#book-overview)" in text
    assert "## Client book overview" in text
    assert "`book_overview` - 1 row(s)" in text


def test_build_report_writes_markdown_and_csvs(loaded_db, analyses, tmp_path):
    written = build_report(loaded_db, analyses, tmp_path / "reports")
    assert written["report"].is_file()
    assert len(written) == len(analyses) + 1
    for analysis in analyses:
        assert written[analysis.name].is_file()
    body = written["report"].read_text(encoding="utf-8")
    assert body.startswith("# Financial analysis report")
    assert "## Client book overview" in body


def test_build_report_can_skip_csvs(loaded_db, analyses, tmp_path):
    written = build_report(loaded_db, analyses, tmp_path / "md-only", write_csvs=False)
    assert list(written) == ["report"]


def test_build_report_redacts_credentials(loaded_db, analyses, tmp_path, monkeypatch):
    monkeypatch.setattr(loaded_db, "url", "postgresql://analyst:s3cret@db.internal:5432/bank")
    written = build_report(loaded_db, analyses, tmp_path / "redacted", write_csvs=False)
    body = written["report"].read_text(encoding="utf-8")
    assert "s3cret" not in body
    assert "analyst:***@db.internal" in body
