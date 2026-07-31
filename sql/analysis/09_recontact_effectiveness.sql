-- name: recontact_effectiveness
-- title: Effectiveness of re-contacting prior prospects
-- description: Conversion by previous campaign outcome and by how long ago the client
--              was last reached, with lift against the never-contacted baseline.

WITH tagged AS (
    SELECT
        CASE WHEN is_first_campaign = 1 THEN 'never contacted' ELSE previous_outcome END AS previous_outcome,
        CASE
            WHEN is_first_campaign = 1 THEN '0_never'
            WHEN days_since_last_contact <= 90 THEN '1_0-90d'
            WHEN days_since_last_contact <= 180 THEN '2_91-180d'
            WHEN days_since_last_contact <= 365 THEN '3_181-365d'
            ELSE '4_365d+'
        END AS recency_band,
        subscribed_flag
    FROM v_client_profile
),
baseline AS (
    SELECT 100.0 * SUM(subscribed_flag) / NULLIF(COUNT(*), 0) AS baseline_rate
    FROM tagged
    WHERE recency_band = '0_never'
),
agg AS (
    SELECT
        previous_outcome,
        recency_band,
        COUNT(*)             AS clients,
        SUM(subscribed_flag) AS subscriptions
    FROM tagged
    GROUP BY previous_outcome, recency_band
)
SELECT
    a.previous_outcome,
    a.recency_band,
    a.clients,
    a.subscriptions,
    ROUND(CAST(100.0 * a.subscriptions / NULLIF(a.clients, 0) AS NUMERIC), 2) AS conversion_rate_pct,
    ROUND(CAST(b.baseline_rate AS NUMERIC), 2) AS never_contacted_rate_pct,
    ROUND(CAST(100.0 * a.subscriptions / NULLIF(a.clients, 0) - b.baseline_rate AS NUMERIC), 2) AS lift_pp,
    ROUND(CAST(100.0 * a.clients / NULLIF(SUM(a.clients) OVER (), 0) AS NUMERIC), 2) AS pct_of_clients
FROM agg a
CROSS JOIN baseline b
ORDER BY conversion_rate_pct DESC, a.clients DESC, a.previous_outcome, a.recency_band;
