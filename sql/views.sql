-- Derived reporting layer.
--
-- Every analysis query reads v_client_profile rather than client_data directly, so
-- banding rules (age cohorts, balance tiers, loan profile, month ordering) are defined
-- exactly once. DROP + CREATE is used instead of CREATE OR REPLACE / IF NOT EXISTS
-- because that spelling is portable across SQLite and PostgreSQL.

DROP VIEW IF EXISTS v_segment_conversion;
DROP VIEW IF EXISTS v_client_profile;

CREATE VIEW v_client_profile AS
SELECT
    c.client_id,
    c.age,
    CASE
        WHEN c.age < 25 THEN '18-24'
        WHEN c.age < 35 THEN '25-34'
        WHEN c.age < 45 THEN '35-44'
        WHEN c.age < 55 THEN '45-54'
        WHEN c.age < 65 THEN '55-64'
        ELSE '65+'
    END AS age_band,
    c.job,
    c.marital,
    c.education,
    c.balance,
    CASE
        WHEN c.balance < 0 THEN '1_overdrawn'
        WHEN c.balance < 500 THEN '2_low'
        WHEN c.balance < 2000 THEN '3_mid'
        WHEN c.balance < 10000 THEN '4_high'
        ELSE '5_premium'
    END AS balance_band,
    CASE WHEN c.balance < 0 THEN 1 ELSE 0 END AS is_overdrawn,
    CASE WHEN c.default_status = 'yes' THEN 1 ELSE 0 END AS in_default,
    CASE WHEN c.housing_loan = 'yes' THEN 1 ELSE 0 END AS has_housing_loan,
    CASE WHEN c.personal_loan = 'yes' THEN 1 ELSE 0 END AS has_personal_loan,
    CASE
        WHEN c.housing_loan = 'yes' AND c.personal_loan = 'yes' THEN 'housing + personal'
        WHEN c.housing_loan = 'yes' THEN 'housing only'
        WHEN c.personal_loan = 'yes' THEN 'personal only'
        ELSE 'unsecured-free'
    END AS loan_profile,
    c.contact,
    c.last_contact_day,
    c.last_contact_month,
    CASE c.last_contact_month
        WHEN 'jan' THEN 1
        WHEN 'feb' THEN 2
        WHEN 'mar' THEN 3
        WHEN 'apr' THEN 4
        WHEN 'may' THEN 5
        WHEN 'jun' THEN 6
        WHEN 'jul' THEN 7
        WHEN 'aug' THEN 8
        WHEN 'sep' THEN 9
        WHEN 'oct' THEN 10
        WHEN 'nov' THEN 11
        WHEN 'dec' THEN 12
        ELSE 99
    END AS last_contact_month_number,
    c.last_contact_duration,
    c.campaign_contacts,
    c.days_since_last_contact,
    -- The source encodes "never contacted in a previous campaign" as -1.
    CASE WHEN c.days_since_last_contact < 0 THEN 1 ELSE 0 END AS is_first_campaign,
    c.previous_contacts,
    c.previous_outcome,
    c.subscribed,
    CASE WHEN c.subscribed = 'yes' THEN 1 ELSE 0 END AS subscribed_flag
FROM client_data c;

-- Reusable job-level conversion roll-up, handy for ad-hoc joins and BI tools.
CREATE VIEW v_segment_conversion AS
SELECT
    p.job,
    COUNT(*)                                            AS clients,
    SUM(p.subscribed_flag)                              AS subscriptions,
    ROUND(CAST(100.0 * SUM(p.subscribed_flag) / NULLIF(COUNT(*), 0) AS NUMERIC), 2) AS conversion_rate_pct,
    ROUND(CAST(SUM(p.balance) AS NUMERIC), 2)           AS total_balance,
    ROUND(CAST(AVG(p.balance) AS NUMERIC), 2)           AS avg_balance
FROM v_client_profile p
GROUP BY p.job;
