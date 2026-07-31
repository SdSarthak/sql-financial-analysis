-- name: age_cohort_profile
-- title: Balance and conversion by age cohort
-- description: Average holdings and subscription rate per age band, indexed against the
--              book average (100 = same as the book).

WITH cohort AS (
    SELECT
        age_band,
        COUNT(*)                   AS clients,
        AVG(balance)               AS avg_balance,
        SUM(balance)               AS total_balance,
        SUM(subscribed_flag)       AS subscriptions,
        AVG(last_contact_duration) AS avg_duration,
        AVG(campaign_contacts)     AS avg_contacts
    FROM v_client_profile
    GROUP BY age_band
)
SELECT
    age_band,
    clients,
    ROUND(CAST(avg_balance AS NUMERIC), 2)   AS avg_balance,
    ROUND(CAST(total_balance AS NUMERIC), 2) AS total_balance,
    ROUND(CAST(100.0 * total_balance / NULLIF(SUM(total_balance) OVER (), 0) AS NUMERIC), 2) AS pct_of_book,
    ROUND(CAST(
        100.0 * avg_balance
        / NULLIF(SUM(total_balance) OVER () / NULLIF(SUM(clients) OVER (), 0), 0)
        AS NUMERIC), 1) AS avg_balance_index,
    subscriptions,
    ROUND(CAST(100.0 * subscriptions / NULLIF(clients, 0) AS NUMERIC), 2) AS conversion_rate_pct,
    ROUND(CAST(avg_duration AS NUMERIC), 2) AS avg_contact_seconds,
    ROUND(CAST(avg_contacts AS NUMERIC), 2) AS avg_campaign_contacts
FROM cohort
ORDER BY age_band;
