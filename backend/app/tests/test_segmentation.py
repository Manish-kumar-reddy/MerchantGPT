from app.services.segmentation import (
    CustomerRFM,
    segment_customers,
    SEGMENT_CHAMPIONS,
    SEGMENT_LOST,
    SEGMENT_NEW,
)


def make_population() -> list[CustomerRFM]:
    """A hand-crafted population where each customer's intended segment is
    obvious by construction, so the test is checking the algorithm's actual
    behavior rather than restating fixture numbers."""
    return [
        # Champions: recent, frequent, big spender
        CustomerRFM(customer_id="champion", recency_days=2, frequency=20, monetary=5000.0),
        # Lost: long gone, ordered once, spent little
        CustomerRFM(customer_id="lost", recency_days=400, frequency=1, monetary=20.0),
        # New: very recent, exactly one order
        CustomerRFM(customer_id="new", recency_days=1, frequency=1, monetary=60.0),
        # A handful of "middle of the pack" customers so the population has real quantiles
        CustomerRFM(customer_id="mid1", recency_days=30, frequency=5, monetary=300.0),
        CustomerRFM(customer_id="mid2", recency_days=45, frequency=6, monetary=350.0),
        CustomerRFM(customer_id="mid3", recency_days=60, frequency=4, monetary=250.0),
    ]


def test_segment_customers_empty_returns_empty():
    assert segment_customers([]) == []


def test_champion_gets_top_scores_on_every_dimension():
    results = {r.customer_id: r for r in segment_customers(make_population())}
    champion = results["champion"]

    assert champion.r_score == 3
    assert champion.f_score == 3
    assert champion.m_score == 3
    assert champion.segment == SEGMENT_CHAMPIONS


def test_lost_customer_scores_low_on_every_dimension():
    results = {r.customer_id: r for r in segment_customers(make_population())}
    lost = results["lost"]

    assert lost.r_score == 1
    assert lost.f_score == 1
    assert lost.m_score == 1
    assert lost.segment == SEGMENT_LOST


def test_single_order_recent_customer_is_segmented_new():
    results = {r.customer_id: r for r in segment_customers(make_population())}
    new_customer = results["new"]

    assert new_customer.r_score == 3
    assert new_customer.f_score == 1
    assert new_customer.segment == SEGMENT_NEW


def test_every_customer_gets_exactly_one_segment():
    population = make_population()
    results = segment_customers(population)

    assert len(results) == len(population)
    assert all(r.segment for r in results)


def test_scores_are_relative_to_the_given_population_not_absolute():
    """The same recency (10 days) should score differently depending on who
    else is in the population -- RFM is a population-relative technique, not
    a fixed absolute cutoff."""
    fast_moving_shop = [
        CustomerRFM(customer_id="a", recency_days=1, frequency=10, monetary=100.0),
        CustomerRFM(customer_id="b", recency_days=3, frequency=10, monetary=100.0),
        CustomerRFM(customer_id="target", recency_days=10, frequency=10, monetary=100.0),
    ]
    slow_moving_shop = [
        CustomerRFM(customer_id="c", recency_days=200, frequency=10, monetary=100.0),
        CustomerRFM(customer_id="d", recency_days=180, frequency=10, monetary=100.0),
        CustomerRFM(customer_id="target", recency_days=10, frequency=10, monetary=100.0),
    ]

    fast_result = next(r for r in segment_customers(fast_moving_shop) if r.customer_id == "target")
    slow_result = next(r for r in segment_customers(slow_moving_shop) if r.customer_id == "target")

    assert fast_result.r_score < slow_result.r_score
