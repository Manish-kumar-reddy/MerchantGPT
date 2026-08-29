"""
RFM (Recency / Frequency / Monetary) customer segmentation.

Deliberately not a trained ML model: RFM is a well-established, fully
explainable retail analytics technique that needs no training data or labels,
which is the honest choice given this app has no real historical dataset to
train a classifier on. Every function here is pure (no DB, no I/O) so it's
directly unit-testable; `compute_segments_for_merchant` in
app/services/analytics.py is the thin async wrapper that fetches real rows
and calls into this module.
"""

from dataclasses import dataclass
from statistics import quantiles


@dataclass(frozen=True)
class CustomerRFM:
    customer_id: str
    recency_days: int  # days since last order (lower = more recent = better)
    frequency: int  # number of completed orders
    monetary: float  # total amount spent


@dataclass(frozen=True)
class CustomerSegment:
    customer_id: str
    segment: str
    r_score: int
    f_score: int
    m_score: int
    rfm_total: int


SEGMENT_CHAMPIONS = "Champions"
SEGMENT_LOYAL = "Loyal Customers"
SEGMENT_BIG_SPENDERS = "Big Spenders"
SEGMENT_AT_RISK = "At Risk"
SEGMENT_NEW = "New Customers"
SEGMENT_LOST = "Lost"
SEGMENT_NEEDS_ATTENTION = "Needs Attention"


def _score_from_thresholds(value: float, low: float, high: float, *, invert: bool = False) -> int:
    """Maps a value into a 1-3 score against two population thresholds (33rd/66th
    percentile). `invert=True` for recency, where a *smaller* value is better."""
    if invert:
        if value <= low:
            return 3
        if value <= high:
            return 2
        return 1
    if value >= high:
        return 3
    if value >= low:
        return 2
    return 1


def _thresholds(values: list[float]) -> tuple[float, float]:
    if len(values) < 2:
        only = values[0] if values else 0.0
        return only, only
    q = quantiles(values, n=3)  # [33rd percentile, 66th percentile]
    return q[0], q[1]


def _segment_from_scores(r: int, f: int, m: int) -> str:
    total = r + f + m
    if r >= 3 and f >= 3 and m >= 3:
        return SEGMENT_CHAMPIONS
    if f >= 3 and total >= 7:
        return SEGMENT_LOYAL
    if m == 3 and r <= 2:
        return SEGMENT_BIG_SPENDERS
    if r == 1 and f >= 2:
        return SEGMENT_AT_RISK
    if r == 3 and f == 1:
        return SEGMENT_NEW
    if r == 1 and f == 1 and m == 1:
        return SEGMENT_LOST
    return SEGMENT_NEEDS_ATTENTION


def segment_customers(customers: list[CustomerRFM]) -> list[CustomerSegment]:
    """Scores every customer 1-3 on each RFM dimension relative to the given
    population's own distribution (not fixed absolute cutoffs, since "frequent"
    means something different for a boutique store vs. a high-volume one), then
    maps the score triple onto a named segment."""
    if not customers:
        return []

    recency_low, recency_high = _thresholds([c.recency_days for c in customers])
    freq_low, freq_high = _thresholds([c.frequency for c in customers])
    monetary_low, monetary_high = _thresholds([c.monetary for c in customers])

    results = []
    for c in customers:
        r = _score_from_thresholds(c.recency_days, recency_low, recency_high, invert=True)
        f = _score_from_thresholds(c.frequency, freq_low, freq_high)
        m = _score_from_thresholds(c.monetary, monetary_low, monetary_high)
        results.append(
            CustomerSegment(
                customer_id=c.customer_id,
                segment=_segment_from_scores(r, f, m),
                r_score=r,
                f_score=f,
                m_score=m,
                rfm_total=r + f + m,
            )
        )
    return results
