-- Core schema for the client book.
--
-- The table mirrors the UCI "Bank Marketing" client dataset (bank-full.csv) with
-- explicit, self-documenting column names. The DDL is deliberately written to the
-- common subset of SQLite and PostgreSQL so the same file bootstraps either engine.

CREATE TABLE IF NOT EXISTS client_data (
    client_id               INTEGER PRIMARY KEY,
    age                     INTEGER NOT NULL,
    job                     VARCHAR(50),
    marital                 VARCHAR(20),
    education               VARCHAR(20),
    default_status          VARCHAR(10),
    balance                 NUMERIC NOT NULL,
    housing_loan            VARCHAR(10),
    personal_loan           VARCHAR(10),
    contact                 VARCHAR(20),
    last_contact_day        INTEGER,
    last_contact_month      VARCHAR(10),
    last_contact_duration   INTEGER,
    campaign_contacts       INTEGER,
    days_since_last_contact INTEGER,
    previous_contacts       INTEGER,
    previous_outcome        VARCHAR(20),
    subscribed              VARCHAR(10) NOT NULL,
    CONSTRAINT ck_client_data_age CHECK (age >= 0),
    CONSTRAINT ck_client_data_subscribed CHECK (subscribed IN ('yes', 'no')),
    CONSTRAINT ck_client_data_default CHECK (default_status IN ('yes', 'no')),
    CONSTRAINT ck_client_data_housing CHECK (housing_loan IN ('yes', 'no')),
    CONSTRAINT ck_client_data_personal CHECK (personal_loan IN ('yes', 'no'))
);

-- Indexes chosen for the access patterns in sql/analysis: segment roll-ups,
-- month-ordered trends and balance-ranked concentration reports.
CREATE INDEX IF NOT EXISTS ix_client_data_job ON client_data (job);
CREATE INDEX IF NOT EXISTS ix_client_data_subscribed ON client_data (subscribed);
CREATE INDEX IF NOT EXISTS ix_client_data_balance ON client_data (balance);
CREATE INDEX IF NOT EXISTS ix_client_data_month ON client_data (last_contact_month);
CREATE INDEX IF NOT EXISTS ix_client_data_campaign ON client_data (campaign_contacts);
