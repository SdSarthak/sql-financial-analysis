-- name: monthly_campaign_trend
-- title: Month-over-month campaign trend
-- description: Calendar-ordered contact volume and conversions with period-over-period
--              growth and a running subscription total.

WITH monthly AS (
    SELECT
        last_contact_month_number AS month_number,
        last_contact_month        AS month,
        COUNT(*)                  AS contacts,
        SUM(subscribed_flag)      AS subscriptions,
        AVG(last_contact_duration) AS avg_duration
    FROM v_client_profile
    GROUP BY last_contact_month_number, last_contact_month
)
SELECT
    month,
    contacts,
    subscriptions,
    ROUND(CAST(100.0 * subscriptions / NULLIF(contacts, 0) AS NUMERIC), 2) AS conversion_rate_pct,
    ROUND(CAST(avg_duration AS NUMERIC), 2) AS avg_contact_seconds,
    LAG(subscriptions) OVER (ORDER BY month_number) AS prev_month_subscriptions,
    ROUND(CAST(
        100.0 * (subscriptions - LAG(subscriptions) OVER (ORDER BY month_number))
        / NULLIF(LAG(subscriptions) OVER (ORDER BY month_number), 0)
        AS NUMERIC), 2) AS subscriptions_growth_pct,
    SUM(subscriptions) OVER (ORDER BY month_number ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_subscriptions,
    SUM(contacts) OVER (ORDER BY month_number ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_contacts
FROM monthly
ORDER BY month_number;
