from app.services.revenue_leaks import (
    ProductRefundStats,
    ProductMarginStats,
    LeakFinding,
    detect_high_refund_products,
    detect_low_margin_products,
    detect_cart_abandonment_leak,
    detect_revenue_decline,
    aggregate_leak_findings,
)


def test_high_refund_rate_is_flagged():
    stats = [ProductRefundStats(product_id="p1", product_name="Widget", revenue=1000.0, refund_amount=200.0, order_count=10)]
    findings = detect_high_refund_products(stats, rate_threshold=0.15)
    assert len(findings) == 1
    assert findings[0].leak_type == "high_refund_rate"
    assert findings[0].severity == "medium"  # 20% is >= 15% but < 30%


def test_very_high_refund_rate_is_high_severity():
    stats = [ProductRefundStats(product_id="p1", product_name="Widget", revenue=1000.0, refund_amount=400.0, order_count=10)]
    findings = detect_high_refund_products(stats, rate_threshold=0.15)
    assert findings[0].severity == "high"


def test_low_order_count_products_are_ignored_even_with_bad_refund_rate():
    """A product with 1 order and 1 refund is a 100% rate but not statistically
    meaningful -- min_orders should suppress noise like this."""
    stats = [ProductRefundStats(product_id="p1", product_name="Widget", revenue=50.0, refund_amount=50.0, order_count=1)]
    findings = detect_high_refund_products(stats, rate_threshold=0.15, min_orders=5)
    assert findings == []


def test_healthy_refund_rate_produces_no_finding():
    stats = [ProductRefundStats(product_id="p1", product_name="Widget", revenue=1000.0, refund_amount=20.0, order_count=10)]
    assert detect_high_refund_products(stats, rate_threshold=0.15) == []


def test_negative_margin_product_is_high_severity():
    stats = [ProductMarginStats(product_id="p1", product_name="Loss Leader", price=10.0, cost=12.0, units_sold=100)]
    findings = detect_low_margin_products(stats, margin_threshold=0.15)
    assert len(findings) == 1
    assert findings[0].severity == "high"
    assert findings[0].estimated_monthly_impact == 200.0  # abs((10-12)*100)
    # regression guard for the tuple-vs-string bug: recommendation must be a plain string
    assert isinstance(findings[0].recommendation, str)
    assert "loss" in findings[0].recommendation.lower()


def test_thin_but_positive_margin_is_medium_severity():
    stats = [ProductMarginStats(product_id="p1", product_name="Thin Margin Item", price=100.0, cost=90.0, units_sold=10)]
    findings = detect_low_margin_products(stats, margin_threshold=0.15)
    assert findings[0].severity == "medium"
    assert isinstance(findings[0].recommendation, str)


def test_healthy_margin_produces_no_finding():
    stats = [ProductMarginStats(product_id="p1", product_name="Good Item", price=100.0, cost=50.0, units_sold=10)]
    assert detect_low_margin_products(stats, margin_threshold=0.15) == []


def test_cart_abandonment_below_threshold_is_not_flagged():
    findings = detect_cart_abandonment_leak(
        abandoned_value_30d=500.0, completed_revenue_30d=5000.0, abandonment_rate=0.4, rate_threshold=0.65
    )
    assert findings == []


def test_cart_abandonment_above_threshold_is_flagged_with_conservative_estimate():
    findings = detect_cart_abandonment_leak(
        abandoned_value_30d=1000.0, completed_revenue_30d=2000.0, abandonment_rate=0.7, rate_threshold=0.65
    )
    assert len(findings) == 1
    assert findings[0].severity == "medium"
    assert findings[0].estimated_monthly_impact == 100.0  # 10% of 1000


def test_severe_cart_abandonment_is_high_severity():
    findings = detect_cart_abandonment_leak(
        abandoned_value_30d=1000.0, completed_revenue_30d=500.0, abandonment_rate=0.85, rate_threshold=0.65
    )
    assert findings[0].severity == "high"


def test_revenue_decline_detected():
    findings = detect_revenue_decline([("2026-06", 10000.0), ("2026-07", 8000.0)], decline_threshold=0.10)
    assert len(findings) == 1
    assert findings[0].estimated_monthly_impact == 2000.0


def test_revenue_growth_is_not_flagged_as_decline():
    findings = detect_revenue_decline([("2026-06", 8000.0), ("2026-07", 10000.0)], decline_threshold=0.10)
    assert findings == []


def test_revenue_decline_needs_at_least_two_months():
    assert detect_revenue_decline([("2026-07", 10000.0)]) == []
    assert detect_revenue_decline([]) == []


def test_aggregate_sorts_high_severity_and_higher_impact_first():
    findings = aggregate_leak_findings(
        [LeakFinding("a", "low", "t", "d", 50.0, "r")],
        [LeakFinding("b", "high", "t", "d", 100.0, "r")],
        [LeakFinding("c", "high", "t", "d", 500.0, "r")],
        [LeakFinding("d", "medium", "t", "d", 9999.0, "r")],
    )
    assert [f.leak_type for f in findings] == ["c", "b", "d", "a"]
