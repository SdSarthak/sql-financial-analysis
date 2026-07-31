import pytest

from sqlfin.loader import (
    LoadError,
    coerce_row,
    load_csv,
    map_headers,
    normalise_header,
    read_rows,
    sniff_delimiter,
)
from sqlfin.schema import row_count

RAW_HEADER = [
    "age", "job", "marital", "education", "default", "balance", "housing", "loan",
    "contact", "day", "month", "duration", "campaign", "pdays", "previous", "poutcome", "y",
]


def test_normalise_header_maps_raw_dataset_names():
    assert normalise_header("default") == "default_status"
    assert normalise_header(" Housing ") == "housing_loan"
    assert normalise_header("y") == "subscribed"
    assert normalise_header("balance") == "balance"


def test_map_headers_accepts_long_column_names():
    mapping = map_headers(["age", "balance", "subscribed", "irrelevant"])
    assert mapping == {"age": "age", "balance": "balance", "subscribed": "subscribed"}


def test_map_headers_rejects_missing_required_columns():
    with pytest.raises(LoadError, match="missing required column"):
        map_headers(["age", "job"])


def test_map_headers_rejects_missing_header():
    with pytest.raises(LoadError, match="no header row"):
        map_headers(None)


def test_sniff_delimiter_prefers_semicolon_for_raw_extract():
    assert sniff_delimiter("age;job;balance\n30;x;1") == ";"
    assert sniff_delimiter("age,job,balance\n30,x,1") == ","
    assert sniff_delimiter("age\n30") == ","


def test_coerce_row_types_and_defaults():
    mapping = {name: normalise_header(name) for name in RAW_HEADER}
    raw = dict.fromkeys(RAW_HEADER, "")
    raw.update({"age": "30", "balance": "1 000".replace(" ", ""), "y": "YES", "month": "March"})
    row = coerce_row(raw, mapping)
    assert row["age"] == 30
    assert row["balance"] == 1000.0
    assert row["subscribed"] == "yes"
    assert row["last_contact_month"] == "mar"
    # Blank optional fields fall back to schema-safe defaults.
    assert row["job"] == "unknown"
    assert row["days_since_last_contact"] == -1
    assert row["campaign_contacts"] == 1


def test_coerce_row_rejects_bad_values():
    mapping = {"age": "age", "balance": "balance", "subscribed": "subscribed"}
    with pytest.raises(LoadError, match="integer"):
        coerce_row({"age": "old", "balance": "1", "subscribed": "yes"}, mapping)
    with pytest.raises(LoadError, match="number"):
        coerce_row({"age": "30", "balance": "n/a", "subscribed": "yes"}, mapping)
    with pytest.raises(LoadError, match="yes/no"):
        coerce_row({"age": "30", "balance": "1", "subscribed": "maybe"}, mapping)
    with pytest.raises(LoadError, match="required"):
        coerce_row({"age": "30", "balance": "", "subscribed": "yes"}, mapping)


def test_coerce_row_rejects_negative_age():
    mapping = {"age": "age", "balance": "balance", "subscribed": "subscribed"}
    with pytest.raises(LoadError, match="non-negative"):
        coerce_row({"age": "-1", "balance": "1", "subscribed": "yes"}, mapping)


def test_read_rows_reports_line_numbers(tmp_path):
    path = tmp_path / "broken.csv"
    path.write_text("age;balance;y\n30;100;yes\n31;oops;no\n", encoding="utf-8")
    with pytest.raises(LoadError, match="line 3"):
        list(read_rows(path))


def test_read_rows_can_skip_bad_rows(tmp_path):
    path = tmp_path / "broken.csv"
    path.write_text("age;balance;y\n30;100;yes\n31;oops;no\n32;200;no\n", encoding="utf-8")
    errors: list[str] = []
    rows = list(read_rows(path, strict=False, on_error=errors.append))
    assert [row["age"] for row in rows] == [30, 32]
    assert len(errors) == 1


def test_read_rows_missing_file(tmp_path):
    with pytest.raises(LoadError, match="not found"):
        list(read_rows(tmp_path / "nope.csv"))


def test_load_csv_inserts_fixture(db, fixture_csv):
    result = load_csv(db, fixture_csv)
    assert result.rows_inserted == 10
    assert result.rows_skipped == 0
    assert row_count(db) == 10

    stored = db.query(
        "SELECT client_id, age, job, default_status, subscribed FROM client_data ORDER BY client_id"
    ).dicts()
    assert stored[0] == {
        "client_id": 1,
        "age": 30,
        "job": "management",
        "default_status": "no",
        "subscribed": "yes",
    }
    assert stored[-1]["client_id"] == 10


def test_load_csv_appends_without_truncate(db, fixture_csv):
    load_csv(db, fixture_csv)
    load_csv(db, fixture_csv)
    assert row_count(db) == 20
    assert db.scalar("SELECT MAX(client_id) FROM client_data") == 20

    load_csv(db, fixture_csv, truncate=True)
    assert row_count(db) == 10


def test_load_csv_skip_mode_counts_rejects(db, tmp_path):
    path = tmp_path / "mixed.csv"
    path.write_text("age;balance;y\n30;100;yes\n31;oops;no\n32;200;no\n", encoding="utf-8")
    result = load_csv(db, path, strict=False)
    assert (result.rows_inserted, result.rows_skipped, result.rows_seen) == (2, 1, 3)
    assert result.errors and "line 3" in result.errors[0]
