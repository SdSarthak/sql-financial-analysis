-- name: conversion_lift_by_segment
-- title: Conversion lift by occupation and education
-- description: Subscription rate of each job x education cell against the book-wide
--              rate, in percentage points and as a multiplicative lift. Cells with few
--              clients are statistically noisy, so the client count is always shown.

WITH book AS (
    SELECT 100.0 * SUM(subscribed_flag) / NULLIF(COUNT(*), 0) AS book_rate
    FROM v_client_profile
),
segment AS (
    SELECT
        job,
        education,
        COUNT(*)             AS clients,
        SUM(subscribed_flag) AS subscriptions
    FROM v_client_profile
    GROUP BY job, education
)
SELECT
    s.job,
    s.education,
    s.clients,
    s.subscriptions,
    ROUND(CAST(100.0 * s.subscriptions / NULLIF(s.clients, 0) AS NUMERIC), 2) AS conversion_rate_pct,
    ROUND(CAST(b.book_rate AS NUMERIC), 2) AS book_rate_pct,
    ROUND(CAST(100.0 * s.subscriptions / NULLIF(s.clients, 0) - b.book_rate AS NUMERIC), 2) AS lift_pp,
    ROUND(CAST((100.0 * s.subscriptions / NULLIF(s.clients, 0)) / NULLIF(b.book_rate, 0) AS NUMERIC), 3) AS lift_ratio
FROM segment s
CROSS JOIN book b
ORDER BY conversion_rate_pct DESC, s.clients DESC, s.job, s.education;
