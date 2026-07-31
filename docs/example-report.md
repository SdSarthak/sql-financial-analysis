# Financial analysis report

> Example output of `python -m sqlfin report`, produced from a 5,000-row synthetic
> book (`python -m sqlfin sample --rows 5000`). The numbers are illustrative only -
> no real client data is stored in this repository.

Generated 2026-07-31 08:30.
Source: `sqlite:///data/financial.db`.

## Contents

- [Client book overview](#book-overview)
- [Deposit concentration by occupation](#balance-by-job)
- [Conversion lift by occupation and education](#conversion-lift-by-segment)
- [Campaign contact efficiency](#campaign-efficiency)
- [Deposit concentration by balance decile](#balance-deciles)
- [Month-over-month campaign trend](#monthly-campaign-trend)
- [Credit risk exposure by loan profile](#credit-risk-exposure)
- [Balance and conversion by age cohort](#age-cohort-profile)
- [Effectiveness of re-contacting prior prospects](#recontact-effectiveness)

## Client book overview

Headline balance and campaign KPIs for the entire client book.

`book_overview` - 1 row(s)

| clients | total_balance | avg_balance | min_balance | max_balance | overdrawn_clients | overdrawn_pct | overdrawn_exposure | clients_in_default | subscriptions | conversion_rate_pct | avg_campaign_contacts | avg_contact_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5,000 | 5,675,443 | 1,135.09 | -1,745 | 35,672 | 405 | 8.10 | -86,243 | 94 | 758 | 15.16 | 2.35 | 266.43 |

## Deposit concentration by occupation

How much of the deposit book each occupation holds, with its share of total balances, conversion rate and balance rank.

`balance_by_job` - 12 row(s)

| job | clients | total_balance | avg_balance | pct_of_book | pct_of_clients | subscriptions | conversion_rate_pct | balance_rank |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| management | 1,029 | 1,509,147 | 1,466.62 | 26.59 | 20.58 | 158 | 15.35 | 1 |
| blue-collar | 1,106 | 1,066,630 | 964.40 | 18.79 | 22.12 | 154 | 13.92 | 2 |
| technician | 819 | 776,224 | 947.77 | 13.68 | 16.38 | 122 | 14.90 | 3 |
| admin. | 523 | 501,473 | 958.84 | 8.84 | 10.46 | 83 | 15.87 | 4 |
| services | 445 | 458,478 | 1,030.29 | 8.08 | 8.90 | 72 | 16.18 | 5 |
| retired | 273 | 419,491 | 1,536.60 | 7.39 | 5.46 | 43 | 15.75 | 6 |
| self-employed | 223 | 393,960 | 1,766.64 | 6.94 | 4.46 | 33 | 14.80 | 7 |
| housemaid | 163 | 146,614 | 899.47 | 2.58 | 3.26 | 22 | 13.50 | 8 |
| student | 110 | 133,202 | 1,210.93 | 2.35 | 2.20 | 15 | 13.64 | 9 |
| entrepreneur | 135 | 121,731 | 901.71 | 2.14 | 2.70 | 24 | 17.78 | 10 |
| unemployed | 136 | 114,123 | 839.14 | 2.01 | 2.72 | 24 | 17.65 | 11 |
| unknown | 38 | 34,370 | 904.47 | 0.61 | 0.76 | 8 | 21.05 | 12 |

## Conversion lift by occupation and education

Subscription rate of each job x education cell against the book-wide rate, in percentage points and as a multiplicative lift. Cells with few clients are statistically noisy, so the client count is always shown.

`conversion_lift_by_segment` - 48 row(s)

| job | education | clients | subscriptions | conversion_rate_pct | book_rate_pct | lift_pp | lift_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| student | unknown | 2 | 1 | 50 | 15.16 | 34.84 | 3.30 |
| entrepreneur | unknown | 3 | 1 | 33.33 | 15.16 | 18.17 | 2.20 |
| unknown | secondary | 22 | 6 | 27.27 | 15.16 | 12.11 | 1.80 |
| retired | unknown | 12 | 3 | 25 | 15.16 | 9.84 | 1.65 |
| unemployed | unknown | 8 | 2 | 25 | 15.16 | 9.84 | 1.65 |
| entrepreneur | tertiary | 39 | 9 | 23.08 | 15.16 | 7.92 | 1.52 |
| technician | unknown | 32 | 7 | 21.88 | 15.16 | 6.72 | 1.44 |
| unemployed | secondary | 70 | 15 | 21.43 | 15.16 | 6.27 | 1.41 |
| admin. | primary | 89 | 19 | 21.35 | 15.16 | 6.19 | 1.41 |
| entrepreneur | primary | 24 | 5 | 20.83 | 15.16 | 5.67 | 1.37 |
| self-employed | primary | 30 | 6 | 20 | 15.16 | 4.84 | 1.32 |
| services | primary | 71 | 14 | 19.72 | 15.16 | 4.56 | 1.30 |
| student | secondary | 58 | 11 | 18.97 | 15.16 | 3.81 | 1.25 |
| retired | primary | 40 | 7 | 17.50 | 15.16 | 2.34 | 1.15 |
| services | unknown | 23 | 4 | 17.39 | 15.16 | 2.23 | 1.15 |
| self-employed | tertiary | 64 | 11 | 17.19 | 15.16 | 2.03 | 1.13 |
| management | primary | 177 | 30 | 16.95 | 15.16 | 1.79 | 1.12 |
| retired | tertiary | 77 | 13 | 16.88 | 15.16 | 1.72 | 1.11 |
| housemaid | secondary | 78 | 13 | 16.67 | 15.16 | 1.51 | 1.10 |
| admin. | tertiary | 131 | 21 | 16.03 | 15.16 | 0.87 | 1.06 |
| management | secondary | 493 | 78 | 15.82 | 15.16 | 0.66 | 1.04 |
| services | tertiary | 142 | 22 | 15.49 | 15.16 | 0.33 | 1.02 |
| technician | secondary | 418 | 64 | 15.31 | 15.16 | 0.15 | 1.01 |
| services | secondary | 209 | 32 | 15.31 | 15.16 | 0.15 | 1.01 |
| blue-collar | secondary | 533 | 81 | 15.20 | 15.16 | 0.04 | 1.00 |
| unemployed | tertiary | 34 | 5 | 14.71 | 15.16 | -0.45 | 0.97 |
| admin. | secondary | 284 | 41 | 14.44 | 15.16 | -0.72 | 0.95 |
| technician | primary | 139 | 20 | 14.39 | 15.16 | -0.77 | 0.95 |
| blue-collar | primary | 174 | 25 | 14.37 | 15.16 | -0.79 | 0.95 |
| unknown | primary | 7 | 1 | 14.29 | 15.16 | -0.87 | 0.94 |
| management | tertiary | 312 | 44 | 14.10 | 15.16 | -1.06 | 0.93 |
| retired | secondary | 144 | 20 | 13.89 | 15.16 | -1.27 | 0.92 |
| technician | tertiary | 230 | 31 | 13.48 | 15.16 | -1.68 | 0.89 |
| entrepreneur | secondary | 69 | 9 | 13.04 | 15.16 | -2.12 | 0.86 |
| management | unknown | 47 | 6 | 12.77 | 15.16 | -2.39 | 0.84 |
| self-employed | secondary | 118 | 15 | 12.71 | 15.16 | -2.45 | 0.84 |
| housemaid | unknown | 8 | 1 | 12.50 | 15.16 | -2.66 | 0.82 |
| unknown | tertiary | 8 | 1 | 12.50 | 15.16 | -2.66 | 0.82 |
| blue-collar | tertiary | 359 | 44 | 12.26 | 15.16 | -2.90 | 0.81 |
| student | primary | 25 | 3 | 12 | 15.16 | -3.16 | 0.79 |
| housemaid | tertiary | 51 | 6 | 11.76 | 15.16 | -3.40 | 0.78 |
| admin. | unknown | 19 | 2 | 10.53 | 15.16 | -4.63 | 0.69 |
| blue-collar | unknown | 40 | 4 | 10 | 15.16 | -5.16 | 0.66 |
| self-employed | unknown | 11 | 1 | 9.09 | 15.16 | -6.07 | 0.60 |
| unemployed | primary | 24 | 2 | 8.33 | 15.16 | -6.83 | 0.55 |
| housemaid | primary | 26 | 2 | 7.69 | 15.16 | -7.47 | 0.51 |
| student | tertiary | 25 | 0 | 0 | 15.16 | -15.16 | 0 |
| unknown | unknown | 1 | 0 | 0 | 15.16 | -15.16 | 0 |

## Campaign contact efficiency

Marginal and cumulative return on repeated calls. Shows where extra contact attempts stop paying for themselves.

`campaign_efficiency` - 6 row(s)

| contact_bucket | clients | subscriptions | conversion_rate_pct | cumulative_clients | cumulative_subscriptions | cumulative_conversion_pct | talk_minutes_per_subscription |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 call | 2,158 | 383 | 17.75 | 2,158 | 383 | 17.75 | 25.23 |
| 2 calls | 1,208 | 199 | 16.47 | 3,366 | 582 | 17.29 | 26.19 |
| 3 calls | 672 | 83 | 12.35 | 4,038 | 665 | 16.47 | 36.25 |
| 4-5 calls | 641 | 74 | 11.54 | 4,679 | 739 | 15.79 | 38.79 |
| 6-10 calls | 305 | 19 | 6.23 | 4,984 | 758 | 15.21 | 71.60 |
| 11+ calls | 16 | 0 | 0 | 5,000 | 758 | 15.16 | - |

## Deposit concentration by balance decile

Splits clients into ten equal cohorts by balance and reports each cohort's share of total deposits plus the cumulative (Lorenz) curve.

`balance_deciles` - 10 row(s)

| decile | clients | min_balance | max_balance | avg_balance | total_balance | pct_of_book | cumulative_pct_of_book | conversion_rate_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 500 | -1,745 | 64 | -164.45 | -82,224 | -1.45 | -1.45 | 13.40 |
| 2 | 500 | 64 | 166 | 115.81 | 57,903 | 1.02 | -0.43 | 14.40 |
| 3 | 500 | 166 | 277 | 220.60 | 110,300 | 1.94 | 1.51 | 15.80 |
| 4 | 500 | 278 | 411 | 342.49 | 171,243 | 3.02 | 4.53 | 17.40 |
| 5 | 500 | 411 | 565 | 489.05 | 244,523 | 4.31 | 8.84 | 16 |
| 6 | 500 | 566 | 788 | 672.47 | 336,234 | 5.92 | 14.76 | 15.20 |
| 7 | 500 | 789 | 1,098 | 936.24 | 468,121 | 8.25 | 23.01 | 14.60 |
| 8 | 500 | 1,098 | 1,611 | 1,334.15 | 667,077 | 11.75 | 34.77 | 14 |
| 9 | 500 | 1,613 | 2,725 | 2,070.08 | 1,035,041 | 18.24 | 53 | 15.80 |
| 10 | 500 | 2,726 | 35,672 | 5,334.45 | 2,667,225 | 47 | 100 | 15 |

## Month-over-month campaign trend

Calendar-ordered contact volume and conversions with period-over-period growth and a running subscription total.

`monthly_campaign_trend` - 12 row(s)

| month | contacts | subscriptions | conversion_rate_pct | avg_contact_seconds | prev_month_subscriptions | subscriptions_growth_pct | running_subscriptions | running_contacts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| jan | 163 | 28 | 17.18 | 271.75 | - | - | 28 | 163 |
| feb | 309 | 48 | 15.53 | 264.38 | 28 | 71.43 | 76 | 472 |
| mar | 96 | 10 | 10.42 | 231.11 | 48 | -79.17 | 86 | 568 |
| apr | 298 | 47 | 15.77 | 274.96 | 10 | 370 | 133 | 866 |
| may | 1,485 | 216 | 14.55 | 252.11 | 47 | 359.57 | 349 | 2,351 |
| jun | 644 | 96 | 14.91 | 268.66 | 216 | -55.56 | 445 | 2,995 |
| jul | 723 | 114 | 15.77 | 270.65 | 96 | 18.75 | 559 | 3,718 |
| aug | 688 | 104 | 15.12 | 276.06 | 114 | -8.77 | 663 | 4,406 |
| sep | 92 | 17 | 18.48 | 280.24 | 104 | -83.65 | 680 | 4,498 |
| oct | 151 | 21 | 13.91 | 278.54 | 17 | 23.53 | 701 | 4,649 |
| nov | 311 | 50 | 16.08 | 292.61 | 21 | 138.10 | 751 | 4,960 |
| dec | 40 | 7 | 17.50 | 255.15 | 50 | -86 | 758 | 5,000 |

## Credit risk exposure by loan profile

Overdraft exposure and default incidence for each combination of secured/unsecured lending, ordered by the size of the negative balance the bank is carrying.

`credit_risk_exposure` - 8 row(s)

| default_state | loan_profile | clients | pct_of_clients | avg_balance | total_balance | overdrawn_clients | overdrawn_pct | overdrawn_exposure | pct_of_overdrawn_exposure | conversion_rate_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| current | housing only | 2,345 | 46.90 | 1,137.46 | 2,667,334 | 195 | 8.32 | -45,214 | 52.43 | 16.29 |
| current | unsecured-free | 1,766 | 35.32 | 1,150.25 | 2,031,341 | 133 | 7.53 | -28,106 | 32.59 | 14.10 |
| current | housing + personal | 443 | 8.86 | 999.51 | 442,785 | 37 | 8.35 | -6,737 | 7.81 | 14.22 |
| current | personal only | 352 | 7.04 | 1,193.18 | 419,998 | 28 | 7.95 | -4,513 | 5.23 | 13.07 |
| in default | unsecured-free | 26 | 0.52 | 1,085.58 | 28,225 | 4 | 15.38 | -796 | 0.92 | 15.38 |
| in default | housing only | 54 | 1.08 | 1,433.65 | 77,417 | 6 | 11.11 | -754 | 0.87 | 25.93 |
| in default | housing + personal | 11 | 0.22 | 575.55 | 6,331 | 2 | 18.18 | -123 | 0.14 | 0 |
| in default | personal only | 3 | 0.06 | 670.67 | 2,012 | 0 | 0 | 0 | 0 | 0 |

## Balance and conversion by age cohort

Average holdings and subscription rate per age band, indexed against the book average (100 = same as the book).

`age_cohort_profile` - 6 row(s)

| age_band | clients | avg_balance | total_balance | pct_of_book | avg_balance_index | subscriptions | conversion_rate_pct | avg_contact_seconds | avg_campaign_contacts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 18-24 | 363 | 1,047.58 | 380,270 | 6.70 | 92.30 | 70 | 19.28 | 265.78 | 2.45 |
| 25-34 | 1,087 | 992.66 | 1,079,019 | 19.01 | 87.50 | 146 | 13.43 | 265.65 | 2.34 |
| 35-44 | 1,743 | 1,179.83 | 2,056,442 | 36.23 | 103.90 | 279 | 16.01 | 264.60 | 2.35 |
| 45-54 | 1,297 | 1,154.04 | 1,496,792 | 26.37 | 101.70 | 180 | 13.88 | 268.03 | 2.34 |
| 55-64 | 439 | 1,255.98 | 551,377 | 9.72 | 110.70 | 71 | 16.17 | 268.79 | 2.36 |
| 65+ | 71 | 1,571.03 | 111,543 | 1.97 | 138.40 | 12 | 16.90 | 282.87 | 2.30 |

## Effectiveness of re-contacting prior prospects

Conversion by previous campaign outcome and by how long ago the client was last reached, with lift against the never-contacted baseline.

`recontact_effectiveness` - 13 row(s)

| previous_outcome | recency_band | clients | subscriptions | conversion_rate_pct | never_contacted_rate_pct | lift_pp | pct_of_clients |
| --- | --- | --- | --- | --- | --- | --- | --- |
| success | 3_181-365d | 38 | 25 | 65.79 | 14.27 | 51.52 | 0.76 |
| success | 2_91-180d | 18 | 11 | 61.11 | 14.27 | 46.84 | 0.36 |
| success | 4_365d+ | 84 | 43 | 51.19 | 14.27 | 36.92 | 1.68 |
| success | 1_0-90d | 12 | 5 | 41.67 | 14.27 | 27.40 | 0.24 |
| other | 4_365d+ | 98 | 18 | 18.37 | 14.27 | 4.10 | 1.96 |
| never contacted | 0_never | 4,135 | 590 | 14.27 | 14.27 | 0 | 82.70 |
| failure | 3_181-365d | 124 | 17 | 13.71 | 14.27 | -0.56 | 2.48 |
| other | 3_181-365d | 39 | 5 | 12.82 | 14.27 | -1.45 | 0.78 |
| other | 2_91-180d | 16 | 2 | 12.50 | 14.27 | -1.77 | 0.32 |
| failure | 1_0-90d | 66 | 8 | 12.12 | 14.27 | -2.15 | 1.32 |
| failure | 4_365d+ | 293 | 31 | 10.58 | 14.27 | -3.69 | 5.86 |
| failure | 2_91-180d | 57 | 3 | 5.26 | 14.27 | -9.01 | 1.14 |
| other | 1_0-90d | 20 | 0 | 0 | 14.27 | -14.27 | 0.40 |
