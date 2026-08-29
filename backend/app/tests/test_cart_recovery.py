from app.services.cart_recovery import CartItemInfo, build_recovery_message


def make_items():
    return [CartItemInfo(product_name="Ceramic Mug", quantity=2, unit_price=15.0)]


def test_fresh_abandonment_has_no_discount():
    msg = build_recovery_message(customer_name="Priya Sharma", items=make_items(), cart_total=30.0, hours_since_abandoned=2)
    assert msg.discount_suggested is False
    assert msg.discount_percent is None
    assert "Priya" in msg.subject
    assert "30.00" in msg.body


def test_medium_delay_still_has_no_discount_but_offers_help():
    msg = build_recovery_message(customer_name="Priya Sharma", items=make_items(), cart_total=30.0, hours_since_abandoned=48)
    assert msg.discount_suggested is False
    assert "reply" in msg.body.lower()


def test_long_delay_triggers_discount():
    msg = build_recovery_message(customer_name="Priya Sharma", items=make_items(), cart_total=100.0, hours_since_abandoned=96)
    assert msg.discount_suggested is True
    assert msg.discount_percent == 10
    assert "90.00" in msg.body  # 100 - 10%


def test_boundary_hours_are_exclusive_on_the_lower_bound():
    # exactly 24h should fall into the 24-72h tier, not the <24h tier
    msg = build_recovery_message(customer_name="Alex", items=make_items(), cart_total=30.0, hours_since_abandoned=24)
    assert msg.discount_suggested is False
    assert "reply" in msg.body.lower()


def test_customer_with_no_name_falls_back_gracefully():
    msg = build_recovery_message(customer_name="", items=make_items(), cart_total=30.0, hours_since_abandoned=1)
    assert "there" in msg.subject.lower() or "there" in msg.body.lower()


def test_multiple_items_all_appear_in_body():
    items = [
        CartItemInfo(product_name="Ceramic Mug", quantity=2, unit_price=15.0),
        CartItemInfo(product_name="Wool Scarf", quantity=1, unit_price=40.0),
    ]
    msg = build_recovery_message(customer_name="Sam", items=items, cart_total=70.0, hours_since_abandoned=1)
    assert "Ceramic Mug" in msg.body
    assert "Wool Scarf" in msg.body
