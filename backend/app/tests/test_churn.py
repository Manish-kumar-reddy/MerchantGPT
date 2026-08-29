from app.services.churn import ChurnInput, compute_churn_risk, compute_churn_risk_batch


def test_customer_on_schedule_is_low_risk():
    result = compute_churn_risk(
        ChurnInput(customer_id="c1", days_since_last_order=15, total_orders=5, avg_days_between_orders=30.0)
    )
    assert result.risk_tier == "low"
    assert 0.0 <= result.risk_score < 0.33


def test_customer_exactly_on_time_is_medium_boundary():
    # days_since == avg_interval -> ratio 1.0 -> risk_score 0.5 -> "medium"
    result = compute_churn_risk(
        ChurnInput(customer_id="c2", days_since_last_order=30, total_orders=5, avg_days_between_orders=30.0)
    )
    assert result.risk_score == 0.5
    assert result.risk_tier == "medium"


def test_customer_way_overdue_is_high_risk_and_capped_at_one():
    result = compute_churn_risk(
        ChurnInput(customer_id="c3", days_since_last_order=300, total_orders=10, avg_days_between_orders=30.0)
    )
    assert result.risk_tier == "high"
    assert result.risk_score == 1.0  # capped, not 5.0


def test_single_order_customer_uses_fallback_interval():
    result = compute_churn_risk(
        ChurnInput(customer_id="c4", days_since_last_order=45, total_orders=1, avg_days_between_orders=None),
        fallback_interval_days=30.0,
    )
    assert "store average" in result.reason
    assert result.risk_score == 0.75  # ratio 45/30 = 1.5 -> /2 = 0.75


def test_zero_days_since_last_order_is_zero_risk():
    result = compute_churn_risk(
        ChurnInput(customer_id="c5", days_since_last_order=0, total_orders=3, avg_days_between_orders=20.0)
    )
    assert result.risk_score == 0.0
    assert result.risk_tier == "low"


def test_batch_preserves_order_and_count():
    inputs = [
        ChurnInput(customer_id="a", days_since_last_order=5, total_orders=2, avg_days_between_orders=10.0),
        ChurnInput(customer_id="b", days_since_last_order=100, total_orders=2, avg_days_between_orders=10.0),
    ]
    results = compute_churn_risk_batch(inputs)
    assert [r.customer_id for r in results] == ["a", "b"]
    assert results[1].risk_score > results[0].risk_score
