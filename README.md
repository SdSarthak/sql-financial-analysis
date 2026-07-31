# SQL Financial Analysis

A SQL-first analytics project over a retail bank's client book: deposit concentration,
credit exposure, campaign efficiency and conversion lift, expressed as plain, portable
SQL and driven by a small zero-dependency Python runner.

The analysis lives in `sql/` — nine documented queries built on CTEs, window functions
and a shared reporting view. The `sqlfin` package is only the harness: it creates the
schema, loads a CSV extract, executes the queries against **SQLite or PostgreSQL** and
renders the results as terminal tables, CSV or a Markdown report pack.

No data is committed to this repository. See [Getting the data](#getting-the-data).

## Quickstart

```bash
git clone https://github.com/SdSarthak/sql-financial-analysis.git
cd sql-financial-analysis
python -m pip install -r requirements-dev.txt   # only needed to run the tests

# 1. Generate a synthetic extract (or point step 3 at the real dataset)
python -m sqlfin sample --rows 5000 --out data/sample_clients.csv

# 2. Create the table, indexes and reporting views
python -m sqlfin init-db

# 3. Load the extract
python -m sqlfin load data/sample_clients.csv

# 4. Explore
python -m sqlfin list
python -m sqlfin run campaign_efficiency
python -m sqlfin report            # writes reports/report.md + one CSV per analysis
```

Nothing above needs a database server: the default connection URL is
`sqlite:///data/financial.db`, and `data/` is git-ignored.

Example output from `python -m sqlfin run campaign_efficiency` on a 3,000-row synthetic
book — repeated calls show clear diminishing returns:

```
contact_bucket  clients  subscriptions  conversion_rate_pct  cumulative_conversion_pct  talk_minutes_per_subscription
--------------  -------  -------------  -------------------  -------------------------  -----------------------------
1 call          1,309    242            18.49                18.49                      24.32
2 calls         720      110            15.28                17.35                      27.20
3 calls         408      52             12.75                16.58                      35.32
4-5 calls       388      53             13.66                16.18                      33.71
6-10 calls      166      8              4.82                 15.55                      85.18
11+ calls       9        0              0                    15.50                      -
```

## The analyses

| Name | Question it answers |
| --- | --- |
| `book_overview` | Headline KPIs: balances, overdraft exposure, defaults, conversion. |
| `balance_by_job` | Which occupations hold the deposit book, and their share of it. |
| `conversion_lift_by_segment` | Which job x education cells beat the book-wide conversion rate. |
| `campaign_efficiency` | Marginal and cumulative return on each extra call. |
| `balance_deciles` | Deposit concentration and the cumulative (Lorenz) curve. |
| `monthly_campaign_trend` | Calendar-ordered volume, period-over-period growth, running totals. |
| `credit_risk_exposure` | Overdraft exposure and default incidence per lending profile. |
| `age_cohort_profile` | Balances and conversion per age band, indexed to the book average. |
| `recontact_effectiveness` | Value of re-contacting prospects, by prior outcome and recency. |

Every file in `sql/analysis/` is a single self-describing statement:

```sql
-- name: campaign_efficiency
-- title: Campaign contact efficiency
-- description: Marginal and cumulative return on repeated calls.
WITH bucketed AS (...)
SELECT ...
```

The runner parses that header, so adding an analysis is just dropping a new `.sql` file
into the directory — no Python change required. Print any query with
`python -m sqlfin show <name>`.

## Getting the data

The schema mirrors the **UCI Bank Marketing** dataset (Moro, Cortez & Rita), a public
extract of a Portuguese bank's term-deposit campaigns:

1. Download `bank+marketing.zip` from
   <https://archive.ics.uci.edu/dataset/222/bank+marketing>.
2. Unzip and take `bank-full.csv` (45,211 rows, semicolon separated).
3. Put it somewhere git-ignored, e.g. `data/bank-full.csv`.
4. `python -m sqlfin load data/bank-full.csv`

The loader accepts the raw headers (`default`, `housing`, `loan`, `day`, `month`,
`duration`, `campaign`, `pdays`, `previous`, `poutcome`, `y`) and maps them onto the long
column names in `sql/schema.sql`; it also accepts files that already use the long names.
Delimiters are detected automatically, values are type-checked, and `--skip-bad-rows`
turns a hard failure into a per-row report.

If you would rather not download anything, `python -m sqlfin sample` generates a
deterministic synthetic book with the same shape and realistic signal (conversion driven
by call duration, prior outcome and balance, with diminishing returns on repeat calls).

## Configuration

All configuration is environment based — no credentials in code.

| Variable | Default | Purpose |
| --- | --- | --- |
| `SQLFIN_DATABASE_URL` | `sqlite:///data/financial.db` | Connection URL. |
| `SQLFIN_REPORT_DIR` | `reports` | Output directory for `report`. |

Copy `.env.example` to `.env` (git-ignored) and the runner will pick it up; real
environment variables always win over the file, and `--database-url` wins over both.
Credentials embedded in a PostgreSQL URL are redacted before anything is printed or
written into a report.

### PostgreSQL

```bash
pip install "psycopg[binary]>=3.1"
export SQLFIN_DATABASE_URL="postgresql://analyst:***@localhost:5432/bank"
python -m sqlfin init-db && python -m sqlfin load data/bank-full.csv
```

The schema, views and every analysis are written to the common subset of SQLite and
PostgreSQL (portable `ROUND(CAST(x AS NUMERIC), 2)`, `NULLIF`-guarded denominators,
`DROP VIEW IF EXISTS` + `CREATE VIEW`), so the same SQL runs unchanged on both.

## Command reference

| Command | Description |
| --- | --- |
| `init-db [--reset]` | Create table, indexes and views (`--reset` drops them first). |
| `load CSV [--truncate] [--skip-bad-rows] [--delimiter D] [--batch-size N]` | Load an extract. |
| `sample [--rows N] [--seed N] [--out PATH]` | Write a synthetic extract. |
| `list` | List available analyses. |
| `show NAME` | Print an analysis query. |
| `run [NAME] [--limit N] [--format table\|markdown\|csv] [--out PATH]` | Run one analysis, or all of them. |
| `report [--out DIR] [--no-csv]` | Write `report.md` plus one CSV per analysis. |
| `status` | Show the connection, row count and analysis count. |

A global `--database-url` may precede any command. Installing the project
(`pip install -e .`) also exposes the same interface as a `sqlfin` executable.

## Schema

`client_data` holds one row per contacted client (see `sql/schema.sql`): demographics
(`age`, `job`, `marital`, `education`), position data (`balance`, `default_status`,
`housing_loan`, `personal_loan`), campaign contact history (`contact`,
`last_contact_day/month/duration`, `campaign_contacts`) and prior-campaign context
(`days_since_last_contact`, `previous_contacts`, `previous_outcome`), plus the outcome
flag `subscribed`. Check constraints reject anything but `yes`/`no` in the flag columns.

`sql/views.sql` adds the derived layer every analysis reads:

- `v_client_profile` — age bands, balance tiers, loan profile, numeric month ordering,
  first-campaign flag and the 0/1 `subscribed_flag`, so banding rules are defined once.
- `v_segment_conversion` — a reusable per-occupation conversion roll-up for BI tools.

## Testing

```bash
python -m pytest
```

83 tests, no network and no database server required. They run against an in-memory
SQLite database seeded from `tests/fixtures/sample_clients.csv` — ten synthetic clients
whose totals (23,000 in balances, two overdrawn accounts totalling -600, one client in
default, five subscriptions) are hand-computed, so the SQL is checked by value and not
merely for "it executed". The suite also asserts the whole pack survives an empty book,
which is what the `NULLIF` guards are there for.

## Project layout

```
sql/
  schema.sql                 table, constraints, indexes
  views.sql                  v_client_profile, v_segment_conversion
  analysis/*.sql             one self-describing query per file
sqlfin/
  cli.py                     python -m sqlfin
  config.py  db.py           env-driven settings, SQLite/PostgreSQL wrapper
  loader.py  sampledata.py   CSV ingestion, synthetic data generator
  analysis.py  report.py     query discovery/execution, table + Markdown rendering
  schema.py  sqltext.py      bootstrap helpers, SQL parsing helpers
tests/                       pytest suite + tiny synthetic fixture
```

## Limitations

- The PostgreSQL path is written to the portable SQL subset and exercised through the
  same code path as SQLite, but CI here only runs the SQLite backend.
- `run --limit` truncates in Python after the query completes, so window functions stay
  correct; it is not a substitute for a `LIMIT` on a very large book.
- The synthetic generator is a plausible stand-in for demos and tests. Do not read
  business conclusions out of it.

## License

MIT
