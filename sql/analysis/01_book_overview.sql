-- name: book_overview
-- title: Client book overview
-- description: Headline balance and campaign KPIs for the entire client book.

SELECT
    COUNT(*)                                        AS clients,
    ROUND(CAST(SUM(balance) AS NUMERIC), 2)         AS total_balance,
    ROUND(CAST(AVG(balance) AS NUMERIC), 2)         AS avg_balance,
    MIN(balance)                                    AS min_balance,
    MAX(balance)                                    AS max_balance,
    SUM(is_overdrawn)                               AS overdrawn_clients,
    ROUND(CAST(100.0 * SUM(is_overdrawn) / NULLIF(COUNT(*), 0) AS NUMERIC), 2) AS overdrawn_pct,
    ROUND(CAST(SUM(CASE WHEN balance < 0 THEN balance ELSE 0 END) AS NUMERIC), 2) AS overdrawn_exposure,
    SUM(in_default)                                 AS clients_in_default,
    SUM(subscribed_flag)                            AS subscriptions,
    ROUND(CAST(100.0 * SUM(subscribed_flag) / NULLIF(COUNT(*), 0) AS NUMERIC), 2) AS conversion_rate_pct,
    ROUND(CAST(AVG(campaign_contacts) AS NUMERIC), 2)      AS avg_campaign_contacts,
    ROUND(CAST(AVG(last_contact_duration) AS NUMERIC), 2)  AS avg_contact_seconds
FROM v_client_profile;
