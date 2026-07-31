-- name: campaign_efficiency
-- title: Campaign contact efficiency
-- description: Marginal and cumulative return on repeated calls. Shows where extra
--              contact attempts stop paying for themselves.

WITH bucketed AS (
    SELECT
        CASE
            WHEN campaign_contacts <= 1 THEN 1
            WHEN campaign_contacts = 2 THEN 2
            WHEN campaign_contacts = 3 THEN 3
            WHEN campaign_contacts <= 5 THEN 4
            WHEN campaign_contacts <= 10 THEN 5
            ELSE 6
        END AS bucket_order,
        CASE
            WHEN campaign_contacts <= 1 THEN '1 call'
            WHEN campaign_contacts = 2 THEN '2 calls'
            WHEN campaign_contacts = 3 THEN '3 calls'
            WHEN campaign_contacts <= 5 THEN '4-5 calls'
            WHEN campaign_contacts <= 10 THEN '6-10 calls'
            ELSE '11+ calls'
        END AS contact_bucket,
        subscribed_flag,
        last_contact_duration
    FROM v_client_profile
),
agg AS (
    SELECT
        bucket_order,
        contact_bucket,
        COUNT(*)                    AS clients,
        SUM(subscribed_flag)        AS subscriptions,
        SUM(last_contact_duration)  AS total_talk_seconds
    FROM bucketed
    GROUP BY bucket_order, contact_bucket
)
SELECT
    contact_bucket,
    clients,
    subscriptions,
    ROUND(CAST(100.0 * subscriptions / NULLIF(clients, 0) AS NUMERIC), 2) AS conversion_rate_pct,
    SUM(clients) OVER (ORDER BY bucket_order ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_clients,
    SUM(subscriptions) OVER (ORDER BY bucket_order ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_subscriptions,
    ROUND(CAST(
        100.0 * SUM(subscriptions) OVER (ORDER BY bucket_order ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
        / NULLIF(SUM(clients) OVER (ORDER BY bucket_order ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0)
        AS NUMERIC), 2) AS cumulative_conversion_pct,
    ROUND(CAST(total_talk_seconds / 60.0 / NULLIF(subscriptions, 0) AS NUMERIC), 2) AS talk_minutes_per_subscription
FROM agg
ORDER BY bucket_order;
