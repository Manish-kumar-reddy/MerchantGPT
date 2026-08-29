"""
Revenue leak detection: a set of independent, rule-based detectors that each
scan one signal (refund concentration, thin margins, cart abandonment,
month-over-month decline) and emit explainable findings. Each detector is a
pure function over plain data so it's directly unit-testable without a
database; app/services/analytics.py fetches the real aggregates and calls
into these.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class LeakFinding:
    leak_type: str
    severity: str  # "low" | "medium" | "high"
    title: str
    description: str
    estimated_monthly_impact: float
    recommendation: str


# ---------------------------------------------------------------------------
# High refund-rate products
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ProductRefundStats:
    product_id: str
    product_name: str
    revenue: float
    refund_amount: float
    order_count: int


def detect_high_refund_products(
    stats: list[ProductRefundStats], *, rate_threshold: float = 0.15, min_orders: int = 5
) -> list[LeakFinding]:
    findings = []
    for s in stats:
        if s.order_count < min_orders or s.revenue <= 0:
            continue
        rate = s.refund_amount / s.revenue
        if rate < rate_threshold:
            continue
        severity = "high" if rate >= 0.30 else "medium"
        findings.append(
            LeakFinding(
                leak_type="high_refund_rate",
                severity=severity,
                title=f"{s.product_name} has a {rate:.0%} refund rate",
                description=(
                    f"${s.refund_amount:,.2f} refunded out of ${s.revenue:,.2f} in revenue "
                    f"across {s.order_count} orders."
                ),
                estimated_monthly_impact=round(s.refund_amount, 2),
                recommendation=(
                    f"Investigate quality, sizing, or listing-accuracy issues for {s.product_name} -- "
                    "a refund rate this high usually has one fixable root cause rather than being general returns."
                ),
            )
        )
    return findings


# ---------------------------------------------------------------------------
# Low / negative margin products
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ProductMarginStats:
    product_id: str
    product_name: str
    price: float
    cost: float
    units_sold: int


def detect_low_margin_products(
    stats: list[ProductMarginStats], *, margin_threshold: float = 0.15
) -> list[LeakFinding]:
    findings = []
    for s in stats:
        if s.price <= 0:
            continue
        margin = (s.price - s.cost) / s.price
        if margin >= margin_threshold:
            continue
        severity = "high" if margin < 0 else "medium"
        impact = abs((s.price - s.cost) * s.units_sold)
        findings.append(
            LeakFinding(
                leak_type="low_margin_product",
                severity=severity,
                title=f"{s.product_name} is selling at {margin:.0%} margin",
                description=(
                    f"Price ${s.price:.2f}, cost ${s.cost:.2f}, {s.units_sold} units sold this period."
                ),
                estimated_monthly_impact=round(impact, 2),
                recommendation=(
                    f"Reprice {s.product_name} or renegotiate supplier cost -- its margin is below your "
                    f"{margin_threshold:.0%} healthy-margin bar"
                    + (", and it is currently selling at a loss." if margin < 0 else ".")
                ),
            )
        )
    return findings


# ---------------------------------------------------------------------------
# Cart abandonment
# ---------------------------------------------------------------------------
def detect_cart_abandonment_leak(
    *,
    abandoned_value_30d: float,
    completed_revenue_30d: float,
    abandonment_rate: float,
    rate_threshold: float = 0.65,
) -> list[LeakFinding]:
    if abandonment_rate < rate_threshold or abandoned_value_30d <= 0:
        return []
    severity = "high" if abandonment_rate >= 0.8 else "medium"
    # Conservative: a competent recovery sequence typically recovers roughly 8-12% of abandoned value.
    estimated_recoverable = abandoned_value_30d * 0.10
    return [
        LeakFinding(
            leak_type="cart_abandonment",
            severity=severity,
            title=f"{abandonment_rate:.0%} of carts are abandoned",
            description=(
                f"${abandoned_value_30d:,.2f} in cart value abandoned in the last 30 days, against "
                f"${completed_revenue_30d:,.2f} in completed revenue over the same period."
            ),
            estimated_monthly_impact=round(estimated_recoverable, 2),
            recommendation=(
                "Launch an automated cart recovery sequence (see the Abandoned Cart Recovery tool). "
                "A typical 2-3 message sequence recovers roughly 8-12% of abandoned cart value."
            ),
        )
    ]


# ---------------------------------------------------------------------------
# Month-over-month revenue decline
# ---------------------------------------------------------------------------
def detect_revenue_decline(
    monthly_revenue: list[tuple[str, float]], *, decline_threshold: float = 0.10
) -> list[LeakFinding]:
    """`monthly_revenue` is [(month_label, revenue), ...] sorted chronologically, most recent last."""
    if len(monthly_revenue) < 2:
        return []
    _, prev = monthly_revenue[-2]
    label, curr = monthly_revenue[-1]
    if prev <= 0:
        return []
    change = (curr - prev) / prev
    if change > -decline_threshold:
        return []
    severity = "high" if change <= -0.25 else "medium"
    return [
        LeakFinding(
            leak_type="revenue_decline",
            severity=severity,
            title=f"Revenue dropped {abs(change):.0%} month-over-month",
            description=f"{label}: ${curr:,.2f} vs ${prev:,.2f} the prior month.",
            estimated_monthly_impact=round(prev - curr, 2),
            recommendation=(
                "Check for a specific, fixable cause first -- a top product going out of stock, a paused ad "
                "campaign, or a normal seasonal dip -- before assuming a broad demand problem."
            ),
        )
    ]


def aggregate_leak_findings(*finding_lists: list[LeakFinding]) -> list[LeakFinding]:
    all_findings = [f for group in finding_lists for f in group]
    severity_rank = {"high": 0, "medium": 1, "low": 2}
    return sorted(all_findings, key=lambda f: (severity_rank.get(f.severity, 3), -f.estimated_monthly_impact))
