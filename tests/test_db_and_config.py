import pytest

from sqlfin.config import (
    DEFAULT_DATABASE_URL,
    ENV_DATABASE_URL,
    get_settings,
    load_dotenv,
    parse_dotenv,
)
from sqlfin.db import DatabaseError, backend_for, connect, redact_url, sqlite_path
from sqlfin.schema import apply_schema, drop_schema, row_count


def test_backend_detection():
    assert backend_for("sqlite:///data/financial.db") == "sqlite"
    assert backend_for("postgresql://user:pw@localhost/bank") == "postgresql"
    assert backend_for("postgres://user@localhost/bank") == "postgresql"
    with pytest.raises(DatabaseError, match="unsupported database URL"):
        backend_for("mysql://localhost/bank")


def test_sqlite_path_extraction():
    assert sqlite_path("sqlite:///data/financial.db") == "data/financial.db"
    assert sqlite_path("sqlite:///:memory:") == ":memory:"
    assert sqlite_path("sqlite://") == ":memory:"


def test_redact_url_hides_password():
    assert redact_url("postgresql://analyst:s3cret@host:5432/bank") == (
        "postgresql://analyst:***@host:5432/bank"
    )
    assert redact_url("sqlite:///data/financial.db") == "sqlite:///data/financial.db"


def test_parse_dotenv_supports_comments_quotes_and_export():
    parsed = parse_dotenv(
        "# comment\n"
        "export SQLFIN_DATABASE_URL='sqlite:///data/x.db'\n"
        'OTHER="value"\n'
        "BLANK=\n"
        "not-an-assignment\n"
    )
    assert parsed == {
        "SQLFIN_DATABASE_URL": "sqlite:///data/x.db",
        "OTHER": "value",
        "BLANK": "",
    }


def test_load_dotenv_does_not_override_existing_env(tmp_path):
    path = tmp_path / ".env"
    path.write_text("SQLFIN_DATABASE_URL=sqlite:///from-file.db\nEXTRA=1\n", encoding="utf-8")
    env = {"SQLFIN_DATABASE_URL": "sqlite:///from-env.db"}
    load_dotenv(path, env)
    assert env["SQLFIN_DATABASE_URL"] == "sqlite:///from-env.db"
    assert env["EXTRA"] == "1"


def test_load_dotenv_missing_file_is_noop(tmp_path):
    assert load_dotenv(tmp_path / "nope.env", {}) == {}


def test_settings_prefers_argument_then_env_then_default():
    env = {ENV_DATABASE_URL: "sqlite:///from-env.db"}
    assert get_settings("sqlite:///explicit.db", env=env).database_url == "sqlite:///explicit.db"
    assert get_settings(env=env).database_url == "sqlite:///from-env.db"
    assert get_settings(env={}).database_url == DEFAULT_DATABASE_URL


def test_settings_expose_sql_paths():
    settings = get_settings(env={})
    assert settings.schema_file.is_file()
    assert settings.views_file.is_file()
    assert settings.analysis_dir.is_dir()
    assert settings.report_dir.name == "reports"


def test_settings_report_dir_from_env(tmp_path):
    settings = get_settings(env={"SQLFIN_REPORT_DIR": str(tmp_path)})
    assert settings.report_dir == tmp_path


def test_connect_creates_parent_directory_for_sqlite_file(tmp_path):
    target = tmp_path / "nested" / "financial.db"
    url = f"sqlite:///{target.as_posix()}"
    with connect(url) as database:
        assert database.backend == "sqlite"
        assert database.placeholder == "?"
        database.execute("CREATE TABLE t (a INTEGER)")
    assert target.is_file()


def test_apply_schema_is_idempotent_and_drop_works(db, settings):
    apply_schema(db, settings)
    assert db.table_exists("client_data")
    assert db.table_exists("v_client_profile")
    assert row_count(db) == 0
    drop_schema(db)
    assert not db.table_exists("client_data")
    assert not db.table_exists("v_client_profile")


def test_schema_rejects_invalid_subscribed_value(db):
    with pytest.raises(Exception):
        db.execute(
            "INSERT INTO client_data (client_id, age, balance, subscribed) VALUES (1, 30, 100, 'maybe')"
        )


def test_query_result_helpers(db):
    result = db.query("SELECT 1 AS a, 'x' AS b")
    assert result.columns == ["a", "b"]
    assert len(result) == 1
    assert result.first() == {"a": 1, "b": "x"}
    assert list(result) == [(1, "x")]
    assert db.scalar("SELECT COUNT(*) FROM client_data") == 0
    assert db.scalar("SELECT a FROM (SELECT 1 AS a) sub WHERE a = 2") is None
