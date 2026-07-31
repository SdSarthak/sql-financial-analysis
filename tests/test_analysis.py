import pytest

from sqlfin.analysis import AnalysisError, discover_analyses, get_analysis, load_analysis_file, run_all


def test_discovery_finds_every_analysis(analyses):
    assert len(analyses) >= 9
    names = [analysis.name for analysis in analyses]
    assert len(names) == len(set(names))
    assert "book_overview" in names


def test_every_analysis_has_metadata_and_one_statement(analyses):
    for analysis in analyses:
        assert analysis.title, f"{analysis.path.name} has no title"
        assert analysis.description, f"{analysis.path.name} has no description"
        assert ";" not in analysis.sql
        assert analysis.body.upper().lstrip().startswith(("SELECT", "WITH"))


def test_get_analysis_accepts_name_or_filename_stem(analyses):
    by_name = get_analysis("book_overview", analyses)
    by_stem = get_analysis("01_book_overview", analyses)
    assert by_name is by_stem


def test_get_analysis_rejects_unknown_name(analyses):
    with pytest.raises(AnalysisError, match="unknown analysis"):
        get_analysis("does_not_exist", analyses)


def test_load_analysis_file_rejects_multi_statement(tmp_path):
    path = tmp_path / "bad.sql"
    path.write_text("SELECT 1;\nSELECT 2;\n", encoding="utf-8")
    with pytest.raises(AnalysisError, match="single query"):
        load_analysis_file(path)


def test_load_analysis_file_rejects_empty_file(tmp_path):
    path = tmp_path / "empty.sql"
    path.write_text("-- name: nothing\n", encoding="utf-8")
    with pytest.raises(AnalysisError, match="no SQL statement"):
        load_analysis_file(path)


def test_load_analysis_file_falls_back_to_filename(tmp_path):
    path = tmp_path / "12_fallback_name.sql"
    path.write_text("SELECT 1 AS x;\n", encoding="utf-8")
    analysis = load_analysis_file(path)
    assert analysis.name == "fallback_name"
    assert analysis.title == "Fallback name"


def test_discover_analyses_rejects_duplicate_names(tmp_path):
    (tmp_path / "01_a.sql").write_text("-- name: dup\nSELECT 1;\n", encoding="utf-8")
    (tmp_path / "02_b.sql").write_text("-- name: dup\nSELECT 2;\n", encoding="utf-8")
    with pytest.raises(AnalysisError, match="duplicate analysis name"):
        discover_analyses(tmp_path)


def test_discover_analyses_rejects_empty_directory(tmp_path):
    with pytest.raises(AnalysisError, match="no analysis files"):
        discover_analyses(tmp_path)


def test_run_all_executes_every_analysis(loaded_db, analyses):
    results = run_all(loaded_db, analyses)
    assert set(results) == {analysis.name for analysis in analyses}
    for name, result in results.items():
        assert result.columns, f"{name} returned no columns"


def test_analyses_survive_an_empty_book(db, analyses):
    """Guarded denominators mean the suite must not blow up on an empty table."""

    results = run_all(db, analyses)
    assert results["book_overview"].first()["clients"] == 0
    assert len(results["balance_by_job"]) == 0
