import pytest

from sqlfin.cli import main


@pytest.fixture
def db_url(tmp_path):
    return f"sqlite:///{(tmp_path / 'financial.db').as_posix()}"


def run_cli(*args, url=None):
    argv = list(args)
    if url:
        argv = ["--database-url", url] + argv
    return main(argv)


def test_init_load_and_status(db_url, fixture_csv, capsys):
    assert run_cli("init-db", url=db_url) == 0
    assert run_cli("load", str(fixture_csv), url=db_url) == 0
    assert run_cli("status", url=db_url) == 0
    output = capsys.readouterr().out
    assert "loaded 10 row(s)" in output
    assert "clients  : 10" in output
    assert "analyses : " in output


def test_init_db_reset_clears_previous_rows(db_url, fixture_csv, capsys):
    run_cli("load", str(fixture_csv), url=db_url)
    run_cli("init-db", "--reset", url=db_url)
    run_cli("status", url=db_url)
    assert "clients  : 0" in capsys.readouterr().out


def test_load_creates_schema_when_missing(db_url, fixture_csv, capsys):
    assert run_cli("load", str(fixture_csv), url=db_url) == 0
    assert "now holds 10 row(s)" in capsys.readouterr().out


def test_load_skip_bad_rows(db_url, tmp_path, capsys):
    csv_path = tmp_path / "mixed.csv"
    csv_path.write_text("age;balance;y\n30;100;yes\n31;bad;no\n", encoding="utf-8")
    assert run_cli("load", str(csv_path), "--skip-bad-rows", url=db_url) == 0
    output = capsys.readouterr().out
    assert "loaded 1 row(s)" in output
    assert "skipped 1 malformed row(s)" in output


def test_load_reports_error_on_bad_row(db_url, tmp_path, capsys):
    csv_path = tmp_path / "mixed.csv"
    csv_path.write_text("age;balance;y\n30;bad;yes\n", encoding="utf-8")
    assert run_cli("load", str(csv_path), url=db_url) == 1
    assert "error:" in capsys.readouterr().err


def test_run_requires_schema(db_url, capsys):
    assert run_cli("run", "book_overview", url=db_url) == 1
    assert "init-db" in capsys.readouterr().err


def test_list_and_show(db_url, capsys):
    assert run_cli("list", url=db_url) == 0
    listing = capsys.readouterr().out
    assert "book_overview" in listing

    assert run_cli("show", "book_overview", url=db_url) == 0
    shown = capsys.readouterr().out
    assert "SELECT" in shown
    assert "-- name:" not in shown


def test_show_unknown_analysis(db_url, capsys):
    assert run_cli("show", "nope", url=db_url) == 1
    assert "unknown analysis" in capsys.readouterr().err


def test_run_single_analysis_formats(db_url, fixture_csv, capsys):
    run_cli("load", str(fixture_csv), url=db_url)
    capsys.readouterr()

    assert run_cli("run", "book_overview", url=db_url) == 0
    assert "Client book overview" in capsys.readouterr().out

    assert run_cli("run", "balance_by_job", "--format", "markdown", "--limit", "2", url=db_url) == 0
    markdown = capsys.readouterr().out
    assert markdown.count("\n| ") >= 2
    assert "| retired |" in markdown


def test_run_all_analyses_writes_file(db_url, fixture_csv, tmp_path, capsys):
    run_cli("load", str(fixture_csv), url=db_url)
    capsys.readouterr()
    out_file = tmp_path / "out" / "all.md"
    assert run_cli("run", "--format", "markdown", "--out", str(out_file), url=db_url) == 0
    body = out_file.read_text(encoding="utf-8")
    assert "## Client book overview" in body
    assert "## Campaign contact efficiency" in body


def test_run_csv_output(db_url, fixture_csv, tmp_path, capsys):
    run_cli("load", str(fixture_csv), url=db_url)
    capsys.readouterr()
    out_file = tmp_path / "overview.csv"
    assert run_cli("run", "book_overview", "--format", "csv", "--out", str(out_file), url=db_url) == 0
    assert out_file.read_text(encoding="utf-8").splitlines()[0].startswith("clients,")


def test_report_writes_pack(db_url, fixture_csv, tmp_path, capsys):
    run_cli("load", str(fixture_csv), url=db_url)
    capsys.readouterr()
    out_dir = tmp_path / "reports"
    assert run_cli("report", "--out", str(out_dir), url=db_url) == 0
    assert (out_dir / "report.md").is_file()
    assert (out_dir / "book_overview.csv").is_file()
    assert "CSV extract(s)" in capsys.readouterr().out


def test_sample_command_writes_csv(db_url, tmp_path, capsys):
    out_file = tmp_path / "sample.csv"
    assert run_cli("sample", "--rows", "25", "--out", str(out_file), url=db_url) == 0
    assert out_file.is_file()
    assert len(out_file.read_text(encoding="utf-8").strip().splitlines()) == 26
    assert "wrote 25 synthetic row(s)" in capsys.readouterr().out


def test_unsupported_database_url_is_reported(fixture_csv, capsys):
    assert run_cli("status", url="mysql://localhost/bank") == 1
    assert "unsupported database URL" in capsys.readouterr().err
