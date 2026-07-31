from sqlfin.sqltext import parse_metadata, split_statements, strip_leading_comments


def test_split_statements_separates_on_semicolons():
    script = "SELECT 1; SELECT 2;\nSELECT 3"
    assert split_statements(script) == ["SELECT 1", "SELECT 2", "SELECT 3"]


def test_split_statements_ignores_semicolons_in_literals_and_comments():
    script = """
    -- a comment with a ; semicolon
    SELECT 'a;b' AS label, "od;d" AS quoted; /* block ; comment */
    SELECT 2;
    """
    statements = split_statements(script)
    assert len(statements) == 2
    assert "'a;b'" in statements[0]


def test_split_statements_handles_escaped_quotes():
    statements = split_statements("SELECT 'it''s fine; really' AS note; SELECT 1;")
    assert len(statements) == 2
    assert statements[0].endswith("AS note")


def test_split_statements_ignores_trailing_whitespace_only_chunks():
    assert split_statements("SELECT 1;\n\n   \n") == ["SELECT 1"]


def test_parse_metadata_reads_header_keys():
    sql = """-- name: my_query
-- title: My query
-- description: First line
--              second line
SELECT 1;
"""
    metadata = parse_metadata(sql)
    assert metadata["name"] == "my_query"
    assert metadata["title"] == "My query"
    assert metadata["description"] == "First line second line"


def test_parse_metadata_stops_at_sql():
    sql = "-- name: x\nSELECT 1 -- not: metadata\n"
    assert parse_metadata(sql) == {"name": "x"}


def test_strip_leading_comments_keeps_query_body():
    sql = "-- name: x\n-- title: y\n\nSELECT 1\nFROM t"
    assert strip_leading_comments(sql) == "SELECT 1\nFROM t"
