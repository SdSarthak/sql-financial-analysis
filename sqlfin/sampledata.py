"""Deterministic synthetic client data.

The real UCI dataset is not redistributed with this repository, so this module generates
a statistically plausible stand-in: balances are skewed, conversion is driven by call
duration, prior outcome and balance, and repeated calls show diminishing returns. Given
the same seed it always produces the same file, which keeps demos and tests reproducible.
"""

from __future__ import annotations

import csv
import math
import random
from pathlib import Path
from typing import Any, Iterator

#: Header names of the raw dataset, in source order.
RAW_HEADER = (
    "age", "job", "marital", "education", "default", "balance", "housing", "loan",
    "contact", "day", "month", "duration", "campaign", "pdays", "previous", "poutcome", "y",
)

JOBS = (
    ("management", 0.21), ("technician", 0.17), ("blue-collar", 0.21), ("admin.", 0.11),
    ("services", 0.09), ("retired", 0.05), ("self-employed", 0.04), ("entrepreneur", 0.03),
    ("unemployed", 0.03), ("housemaid", 0.03), ("student", 0.02), ("unknown", 0.01),
)
MARITAL = (("married", 0.60), ("single", 0.28), ("divorced", 0.12))
EDUCATION = (("secondary", 0.51), ("tertiary", 0.29), ("primary", 0.16), ("unknown", 0.04))
CONTACT = (("cellular", 0.65), ("telephone", 0.07), ("unknown", 0.28))
MONTHS = (
    ("jan", 0.03), ("feb", 0.06), ("mar", 0.02), ("apr", 0.06), ("may", 0.30), ("jun", 0.12),
    ("jul", 0.15), ("aug", 0.14), ("sep", 0.02), ("oct", 0.03), ("nov", 0.06), ("dec", 0.01),
)
PREVIOUS_OUTCOME = (("failure", 0.11), ("other", 0.04), ("success", 0.03), ("unknown", 0.82))


def _pick(rng: random.Random, weighted: tuple[tuple[str, float], ...]) -> str:
    values = [value for value, _ in weighted]
    weights = [weight for _, weight in weighted]
    return rng.choices(values, weights=weights, k=1)[0]


def _balance(rng: random.Random, job: str, age: int) -> int:
    """Skewed balance: mostly small, a long right tail, a minority overdrawn."""

    seniority = 1.0 + max(0, age - 25) / 60.0
    premium = 1.6 if job in {"management", "retired", "self-employed"} else 1.0
    amount = rng.lognormvariate(6.1, 1.15) * seniority * premium
    if rng.random() < 0.08:
        return -int(rng.lognormvariate(5.0, 0.9))
    return int(amount)


def _subscription_probability(
    duration: int, balance: int, campaign_contacts: int, previous_outcome: str, age: int
) -> float:
    score = -3.4
    score += 1.9 * math.log1p(duration) / math.log1p(600)
    score += 0.35 * math.log1p(max(balance, 0)) / math.log1p(5000)
    score -= 0.22 * (campaign_contacts - 1)
    if previous_outcome == "success":
        score += 2.1
    elif previous_outcome == "failure":
        score -= 0.3
    if age >= 60 or age <= 25:
        score += 0.5
    return 1.0 / (1.0 + math.exp(-score))


def generate_rows(rows: int = 5000, seed: int = 20240131) -> Iterator[dict[str, Any]]:
    """Yield ``rows`` synthetic records using the raw dataset's column names."""

    if rows < 0:
        raise ValueError("rows must be non-negative")
    rng = random.Random(seed)
    for _ in range(rows):
        age = max(18, min(95, int(rng.gauss(41, 11))))
        job = _pick(rng, JOBS)
        balance = _balance(rng, job, age)
        campaign_contacts = min(30, 1 + int(rng.expovariate(1 / 1.8)))
        duration = max(5, min(3600, int(rng.expovariate(1 / 258.0))))
        previous_outcome = _pick(rng, PREVIOUS_OUTCOME)
        if previous_outcome == "unknown":
            previous_contacts = 0
            pdays = -1
        else:
            previous_contacts = 1 + int(rng.expovariate(1 / 1.5))
            pdays = rng.randint(1, 800)
        probability = _subscription_probability(
            duration, balance, campaign_contacts, previous_outcome, age
        )
        yield {
            "age": age,
            "job": job,
            "marital": _pick(rng, MARITAL),
            "education": _pick(rng, EDUCATION),
            "default": "yes" if rng.random() < 0.018 else "no",
            "balance": balance,
            "housing": "yes" if rng.random() < 0.56 else "no",
            "loan": "yes" if rng.random() < 0.16 else "no",
            "contact": _pick(rng, CONTACT),
            "day": rng.randint(1, 28),
            "month": _pick(rng, MONTHS),
            "duration": duration,
            "campaign": campaign_contacts,
            "pdays": pdays,
            "previous": previous_contacts,
            "poutcome": previous_outcome,
            "y": "yes" if rng.random() < probability else "no",
        }


def write_sample_csv(
    path: Path | str, rows: int = 5000, seed: int = 20240131, delimiter: str = ";"
) -> Path:
    """Write a synthetic extract that mirrors the raw dataset's shape."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(RAW_HEADER), delimiter=delimiter)
        writer.writeheader()
        for row in generate_rows(rows=rows, seed=seed):
            writer.writerow(row)
    return target
