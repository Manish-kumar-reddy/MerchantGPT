"""
Churn risk scoring.

Explicitly a heuristic, not a trained classifier: there is no historical
labeled "did this customer actually churn" dataset available to train or
validate a real model against, and shipping one anyway -- however good the
demo numbers look -- would be fabricated rigor. Instead this scores risk as
"how overdue is this customer relative to their own normal ordering cadence",
which is transparent, immediately explainable to a merchant, and requires no
training data. `risk_score` and `reason` are always derivable by hand from
the same three inputs, which is the point.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ChurnInput:
    customer_id: str
    days_since_last_order: int
    total_orders: int
    avg_days_between_orders: float | None  # None when total_orders < 2


@dataclass(frozen=True)
class ChurnResult:
    customer_id: str
    risk_score: float  # 0.0 (safe) - 1.0 (high risk)
    risk_tier: str  # "low" | "medium" | "high"
    reason: str


def compute_churn_risk(data: ChurnInput, *, fallback_interval_days: float = 30.0) -> ChurnResult:
    interval = data.avg_days_between_orders if data.avg_days_between_orders and data.avg_days_between_orders > 0 else fallback_interval_days

    ratio = data.days_since_last_order / interval
    # 1x the normal interval overdue -> 0.5 risk; 2x or more -> capped at 1.0 risk.
    risk_score = min(1.0, max(0.0, ratio / 2.0))

    if risk_score >= 0.66:
        tier = "high"
    elif risk_score >= 0.33:
        tier = "medium"
    else:
        tier = "low"

    basis = "their own order history" if data.avg_days_between_orders else "the store average (single-order customer)"
    reason = (
        f"Last ordered {data.days_since_last_order} days ago against a typical "
        f"{interval:.0f}-day gap based on {basis} -- {ratio:.1f}x overdue."
    )

    return ChurnResult(
        customer_id=data.customer_id,
        risk_score=round(risk_score, 2),
        risk_tier=tier,
        reason=reason,
    )


def compute_churn_risk_batch(
    items: list[ChurnInput], *, fallback_interval_days: float = 30.0
) -> list[ChurnResult]:
    return [compute_churn_risk(item, fallback_interval_days=fallback_interval_days) for item in items]
