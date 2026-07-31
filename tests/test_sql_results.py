"""Value-level checks of the analysis SQL against the hand-computed fixture book.

The fixture holds ten clients with a total balance of 23,000, two overdrawn accounts
(-600 combined), one client in default and five subscriptions.
"""

import pytest

from sqlfin.analysis import get_analysis, run_analysis


def run(db, analyses, name):
    return run_analysis(db, get_analysis(name, analyses))


def test_book_overview_matches_hand_computed_totals(loaded_db, analyses):
    row = run(loaded_db, analyses, "book_overview").first()
    assert row["clients"] == 10
    assert row["total_balance"] == pytest.approx(23000)
    assert row["avg_balance"] == pytest.approx(2300)
    assert row["min_balance"] == pytest.approx(-500)
    assert row["max_balance"] == pytest.approx(12000)
    assert row["overdrawn_clients"] == 2
    assert row["overdrawn_pct"] == pytest.approx(20.0)
    assert row["overdrawn_exposure"] == pytest.approx(-600)
    assert row["clients_in_default"] == 1
    assert row["subscriptions"] == 5
    assert row["conversion_rate_pct"] == pytest.approx(50.0)
    assert row["avg_campaign_contacts"] == pytest.approx(3.2)
    assert row["avg_contact_seconds"] == pytest.approx(271.0)


def test_balance_by_job_ranks_and_shares(loaded_db, analyses):
    rows = run(loaded_db, analyses, "balance_by_job").dicts()
    assert [row["job"] for row in rows][:3] == ["retired", "management", "technician"]
    retired = rows[0]
    assert retired["clients"] == 2
    assert retired["total_balance"] == pytest.approx(17000)
    assert retired["avg_balance"] == pytest.approx(8500)
    assert retired["pct_of_book"] == pytest.approx(73.91, abs=0.01)
    assert retired["pct_of_clients"] == pytest.approx(20.0)
    assert retired["conversion_rate_pct"] == pytest.approx(100.0)
    assert retired["balance_rank"] == 1
    assert sum(row["clients"] for row in rows) == 10
    assert sum(row["pct_of_book"] for row in rows) == pytest.approx(100.0, abs=0.05)


def test_conversion_lift_is_relative_to_the_book_rate(loaded_db, analyses):
    rows = run(loaded_db, analyses, "conversion_lift_by_segment").dicts()
    cell = next(r for r in rows if r["job"] == "management" and r["education"] == "tertiary")
    assert cell["clients"] == 2
    assert cell["subscriptions"] == 2
    assert cell["conversion_rate_pct"] == pytest.approx(100.0)
    assert cell["book_rate_pct"] == pytest.approx(50.0)
    assert cell["lift_pp"] == pytest.approx(50.0)
    assert cell["lift_ratio"] == pytest.approx(2.0)


def test_campaign_efficiency_cumulates_in_bucket_order(loaded_db, analyses):
    rows = run(loaded_db, analyses, "campaign_efficiency").dicts()
    assert [row["contact_bucket"] for row in rows] == [
        "1 call", "2 calls", "3 calls", "4-5 calls", "11+ calls",
    ]
    first = rows[0]
    assert (first["clients"], first["subscriptions"]) == (4, 3)
    assert first["conversion_rate_pct"] == pytest.approx(75.0)
    assert first["cumulative_clients"] == 4
    assert rows[1]["cumulative_clients"] == 6
    assert rows[1]["cumulative_subscriptions"] == 4
    last = rows[-1]
    assert last["cumulative_clients"] == 10
    assert last["cumulative_subscriptions"] == 5
    assert last["cumulative_conversion_pct"] == pytest.approx(50.0)


def test_balance_deciles_form_a_cumulative_curve(loaded_db, analyses):
    rows = run(loaded_db, analyses, "balance_deciles").dicts()
    assert len(rows) == 10
    assert [row["decile"] for row in rows] == list(range(1, 11))
    assert all(row["clients"] == 1 for row in rows)
    assert rows[0]["min_balance"] == pytest.approx(-500)
    assert rows[-1]["max_balance"] == pytest.approx(12000)
    assert rows[-1]["cumulative_pct_of_book"] == pytest.approx(100.0, abs=0.05)
    # The cumulative column is the running sum of the per-decile share. It only rises
    # monotonically once the overdrawn deciles are behind it, which is the point of the
    # curve: the top decile alone carries most of the book.
    running = 0.0
    for row in rows:
        running += row["pct_of_book"]
        assert row["cumulative_pct_of_book"] == pytest.approx(running, abs=0.05)
    assert rows[-1]["pct_of_book"] > 50.0


def test_monthly_trend_is_calendar_ordered(loaded_db, analyses):
    rows = run(loaded_db, analyses, "monthly_campaign_trend").dicts()
    assert [row["month"] for row in rows] == ["may", "jun", "jul", "aug", "sep", "oct"]
    assert [row["contacts"] for row in rows] == [2, 2, 2, 2, 1, 1]
    assert [row["subscriptions"] for row in rows] == [1, 2, 0, 1, 1, 0]
    assert rows[0]["prev_month_subscriptions"] is None
    assert rows[1]["prev_month_subscriptions"] == 1
    assert rows[1]["subscriptions_growth_pct"] == pytest.approx(100.0)
    # A zero prior month must not raise a division error; it yields NULL instead.
    assert rows[3]["subscriptions_growth_pct"] is None
    assert [row["running_subscriptions"] for row in rows] == [1, 3, 3, 4, 5, 5]
    assert rows[-1]["running_contacts"] == 10


def test_credit_risk_exposure_splits_default_state(loaded_db, analyses):
    rows = run(loaded_db, analyses, "credit_risk_exposure").dicts()
    defaulted = [row for row in rows if row["default_state"] == "in default"]
    assert len(defaulted) == 1
    assert defaulted[0]["loan_profile"] == "housing + personal"
    assert defaulted[0]["clients"] == 1
    assert defaulted[0]["overdrawn_exposure"] == pytest.approx(-500)
    assert defaulted[0]["pct_of_overdrawn_exposure"] == pytest.approx(83.33, abs=0.01)
    # Ordered by exposure, the deepest overdraft comes first.
    assert rows[0]["overdrawn_exposure"] == pytest.approx(-500)
    assert sum(row["clients"] for row in rows) == 10


def test_recontact_effectiveness_uses_never_contacted_baseline(loaded_db, analyses):
    rows = run(loaded_db, analyses, "recontact_effectiveness").dicts()
    baseline = next(row for row in rows if row["recency_band"] == "0_never")
    assert baseline["previous_outcome"] == "never contacted"
    assert baseline["clients"] == 7
    assert baseline["subscriptions"] == 3
    assert baseline["conversion_rate_pct"] == pytest.approx(42.86, abs=0.01)
    assert all(row["never_contacted_rate_pct"] == pytest.approx(42.86, abs=0.01) for row in rows)

    successes = [row for row in rows if row["previous_outcome"] == "success"]
    assert {row["recency_band"] for row in successes} == {"1_0-90d", "2_91-180d"}
    assert all(row["conversion_rate_pct"] == pytest.approx(100.0) for row in successes)
    assert all(row["lift_pp"] == pytest.approx(57.14, abs=0.01) for row in successes)
    assert sum(row["clients"] for row in rows) == 10


def test_age_cohort_profile_indexes_against_the_book(loaded_db, analyses):
    rows = run(loaded_db, analyses, "age_cohort_profile").dicts()
    bands = {row["age_band"]: row for row in rows}
    assert set(bands) == {"18-24", "25-34", "35-44", "45-54", "55-64", "65+"}
    assert bands["25-34"]["clients"] == 3
    assert bands["25-34"]["total_balance"] == pytest.approx(1800)
    assert bands["65+"]["avg_balance"] == pytest.approx(12000)
    assert bands["65+"]["avg_balance_index"] == pytest.approx(521.7, abs=0.1)
    assert sum(row["clients"] for row in rows) == 10
    assert sum(row["pct_of_book"] for row in rows) == pytest.approx(100.0, abs=0.05)


def test_reporting_views_are_available(loaded_db):
    assert loaded_db.table_exists("v_client_profile")
    profile = loaded_db.query(
        "SELECT age_band, loan_profile, subscribed_flag, is_first_campaign, last_contact_month_number"
        " FROM v_client_profile WHERE client_id = 4"
    ).first()
    assert profile == {
        "age_band": "55-64",
        "loan_profile": "unsecured-free",
        "subscribed_flag": 1,
        "is_first_campaign": 0,
        "last_contact_month_number": 6,
    }
    segments = loaded_db.query("SELECT job, clients FROM v_segment_conversion ORDER BY job").dicts()
    assert sum(row["clients"] for row in segments) == 10
