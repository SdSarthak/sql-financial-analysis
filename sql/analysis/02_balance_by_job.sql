-- name: balance_by_job
-- title: Deposit concentration by occupation
-- description: How much of the deposit book each occupation holds, with its share of
--              total balances, conversion rate and balance rank.

WITH segment AS (
    SELECT
        job,
        COUNT(*)               AS clients,
        SUM(balance)           AS total_balance,
        AVG(balance)           AS avg_balance,
        SUM(subscribed_flag)   AS subscriptions
    FROM v_client_profile
    GROUP BY job
)
SELECT
    job,
    clients,
    ROUND(CAST(total_balance AS NUMERIC), 2) AS total_balance,
    ROUND(CAST(avg_balance AS NUMERIC), 2)   AS avg_balance,
    ROUND(CAST(100.0 * total_balance / NULLIF(SUM(total_balance) OVER (), 0) AS NUMERIC), 2) AS pct_of_book,
    ROUND(CAST(100.0 * clients / NULLIF(SUM(clients) OVER (), 0) AS NUMERIC), 2)             AS pct_of_clients,
    subscriptions,
    ROUND(CAST(100.0 * subscriptions / NULLIF(clients, 0) AS NUMERIC), 2) AS conversion_rate_pct,
    RANK() OVER (ORDER BY total_balance DESC) AS balance_rank
FROM segment
ORDER BY total_balance DESC, job;
