-- name: credit_risk_exposure
-- title: Credit risk exposure by loan profile
-- description: Overdraft exposure and default incidence for each combination of
--              secured/unsecured lending, ordered by the size of the negative balance
--              the bank is carrying.

WITH profiled AS (
    SELECT
        CASE WHEN in_default = 1 THEN 'in default' ELSE 'current' END AS default_state,
        loan_profile,
        balance,
        is_overdrawn,
        subscribed_flag
    FROM v_client_profile
),
agg AS (
    SELECT
        default_state,
        loan_profile,
        COUNT(*)             AS clients,
        AVG(balance)         AS avg_balance,
        SUM(balance)         AS total_balance,
        SUM(is_overdrawn)    AS overdrawn_clients,
        SUM(CASE WHEN balance < 0 THEN balance ELSE 0 END) AS overdrawn_exposure,
        SUM(subscribed_flag) AS subscriptions
    FROM profiled
    GROUP BY default_state, loan_profile
)
SELECT
    default_state,
    loan_profile,
    clients,
    ROUND(CAST(100.0 * clients / NULLIF(SUM(clients) OVER (), 0) AS NUMERIC), 2) AS pct_of_clients,
    ROUND(CAST(avg_balance AS NUMERIC), 2)   AS avg_balance,
    ROUND(CAST(total_balance AS NUMERIC), 2) AS total_balance,
    overdrawn_clients,
    ROUND(CAST(100.0 * overdrawn_clients / NULLIF(clients, 0) AS NUMERIC), 2) AS overdrawn_pct,
    ROUND(CAST(overdrawn_exposure AS NUMERIC), 2) AS overdrawn_exposure,
    ROUND(CAST(100.0 * overdrawn_exposure / NULLIF(SUM(overdrawn_exposure) OVER (), 0) AS NUMERIC), 2) AS pct_of_overdrawn_exposure,
    ROUND(CAST(100.0 * subscriptions / NULLIF(clients, 0) AS NUMERIC), 2) AS conversion_rate_pct
FROM agg
ORDER BY overdrawn_exposure, default_state, loan_profile;
