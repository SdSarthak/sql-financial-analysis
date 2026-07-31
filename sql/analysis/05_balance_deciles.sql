-- name: balance_deciles
-- title: Deposit concentration by balance decile
-- description: Splits clients into ten equal cohorts by balance and reports each
--              cohort's share of total deposits plus the cumulative (Lorenz) curve.

WITH ranked AS (
    SELECT
        balance,
        subscribed_flag,
        NTILE(10) OVER (ORDER BY balance) AS decile
    FROM v_client_profile
),
agg AS (
    SELECT
        decile,
        COUNT(*)             AS clients,
        MIN(balance)         AS min_balance,
        MAX(balance)         AS max_balance,
        AVG(balance)         AS avg_balance,
        SUM(balance)         AS total_balance,
        SUM(subscribed_flag) AS subscriptions
    FROM ranked
    GROUP BY decile
)
SELECT
    decile,
    clients,
    min_balance,
    max_balance,
    ROUND(CAST(avg_balance AS NUMERIC), 2)   AS avg_balance,
    ROUND(CAST(total_balance AS NUMERIC), 2) AS total_balance,
    ROUND(CAST(100.0 * total_balance / NULLIF(SUM(total_balance) OVER (), 0) AS NUMERIC), 2) AS pct_of_book,
    ROUND(CAST(
        100.0 * SUM(total_balance) OVER (ORDER BY decile ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
        / NULLIF(SUM(total_balance) OVER (), 0)
        AS NUMERIC), 2) AS cumulative_pct_of_book,
    ROUND(CAST(100.0 * subscriptions / NULLIF(clients, 0) AS NUMERIC), 2) AS conversion_rate_pct
FROM agg
ORDER BY decile;
