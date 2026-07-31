import csv

import pytest

from sqlfin.loader import load_csv
from sqlfin.sampledata import RAW_HEADER, generate_rows, write_sample_csv
from sqlfin.schema import row_count


def test_generation_is_deterministic():
    first = list(generate_rows(rows=50, seed=7))
    second = list(generate_rows(rows=50, seed=7))
    third = list(generate_rows(rows=50, seed=8))
    assert first == second
    assert first != third


def test_generated_rows_match_the_raw_schema():
    rows = list(generate_rows(rows=200, seed=3))
    assert len(rows) == 200
    for row in rows:
        assert tuple(row) == RAW_HEADER
        assert 18 <= row["age"] <= 95
        assert row["y"] in {"yes", "no"}
        assert row["default"] in {"yes", "no"}
        assert row["campaign"] >= 1
        assert row["duration"] >= 5
        if row["poutcome"] == "unknown":
            assert row["pdays"] == -1
            assert row["previous"] == 0
        else:
            assert row["pdays"] >= 1


def test_generated_book_carries_signal():
    rows = list(generate_rows(rows=2000, seed=11))
    conversions = sum(1 for row in rows if row["y"] == "yes")
    assert 0.03 < conversions / len(rows) < 0.45
    assert any(row["balance"] < 0 for row in rows)


def test_negative_row_count_rejected():
    with pytest.raises(ValueError, match="non-negative"):
        list(generate_rows(rows=-1))


def test_written_sample_loads_into_the_database(tmp_path, db):
    path = write_sample_csv(tmp_path / "sample.csv", rows=120, seed=5)
    with path.open(encoding="utf-8", newline="") as handle:
        header = next(csv.reader(handle, delimiter=";"))
    assert header == list(RAW_HEADER)

    result = load_csv(db, path)
    assert result.rows_inserted == 120
    assert row_count(db) == 120
