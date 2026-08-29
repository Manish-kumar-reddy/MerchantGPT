from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order, OrderItem, Product, Refund, Cart, CartItem, Customer, OrderStatus, CartStatus
from app.services import revenue_leaks as leaks
from app.services import segmentation as seg
from app.services import churn as churn_svc

UTC_NOW = lambda: datetime.now(timezone.utc)  # noqa: E731


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
async def get_dashboard_summary(db: AsyncSession, merchant_id: UUID) -> dict:
    since_30d = UTC_NOW() - timedelta(days=30)

    revenue_row = (
        await db.execute(
            select(func.coalesce(func.sum(Order.total_amount), 0), func.count(Order.id))
            .where(Order.merchant_id == merchant_id, Order.created_at >= since_30d)
            .where(Order.status != OrderStatus.CANCELLED)
        )
    ).one()
    revenue_30d, orders_30d = float(revenue_row[0]), int(revenue_row[1])
    avg_order_value = revenue_30d / orders_30d if orders_30d else 0.0

    refund_row = (
        await db.execute(
            select(func.coalesce(func.sum(Refund.amount), 0))
            .where(Refund.merchant_id == merchant_id, Refund.created_at >= since_30d)
        )
    ).scalar_one()
    refund_amount_30d = float(refund_row)
    refund_rate_30d = (refund_amount_30d / revenue_30d) if revenue_30d else 0.0

    active_customers = (
        await db.execute(
            select(func.count(func.distinct(Order.customer_id)))
            .where(Order.merchant_id == merchant_id, Order.created_at >= since_30d)
        )
    ).scalar_one()

    cart_rows = (
        await db.execute(
            select(Cart.status, func.coalesce(func.sum(Cart.total_amount), 0), func.count(Cart.id))
            .where(Cart.merchant_id == merchant_id, Cart.created_at >= since_30d)
            .group_by(Cart.status)
        )
    ).all()
    abandoned_value = 0.0
    abandoned_count = 0
    total_carts = 0
    for status, total, count in cart_rows:
        total_carts += count
        if status in (CartStatus.ABANDONED, CartStatus.RECOVERED):
            abandoned_value += float(total)
            abandoned_count += count
    abandonment_rate = (abandoned_count / total_carts) if total_carts else 0.0

    revenue_by_day_rows = (
        await db.execute(
            select(func.date(Order.created_at), func.coalesce(func.sum(Order.total_amount), 0))
            .where(Order.merchant_id == merchant_id, Order.created_at >= since_30d)
            .where(Order.status != OrderStatus.CANCELLED)
            .group_by(func.date(Order.created_at))
            .order_by(func.date(Order.created_at))
        )
    ).all()
    revenue_by_day = [{"date": str(d), "revenue": float(r)} for d, r in revenue_by_day_rows]

    top_products_rows = (
        await db.execute(
            select(
                Product.name,
                func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0),
                func.coalesce(func.sum(OrderItem.quantity), 0),
            )
            .join(OrderItem, OrderItem.product_id == Product.id)
            .join(Order, Order.id == OrderItem.order_id)
            .where(Order.merchant_id == merchant_id, Order.created_at >= since_30d)
            .where(Order.status != OrderStatus.CANCELLED)
            .group_by(Product.id, Product.name)
            .order_by(func.sum(OrderItem.quantity * OrderItem.unit_price).desc())
            .limit(5)
        )
    ).all()
    top_products = [{"name": name, "revenue": float(rev), "units": int(units)} for name, rev, units in top_products_rows]

    return {
        "revenue_30d": round(revenue_30d, 2),
        "orders_30d": orders_30d,
        "avg_order_value_30d": round(avg_order_value, 2),
        "refund_amount_30d": round(refund_amount_30d, 2),
        "refund_rate_30d": round(refund_rate_30d, 4),
        "active_customers_30d": int(active_customers),
        "abandoned_cart_value_30d": round(abandoned_value, 2),
        "cart_abandonment_rate_30d": round(abandonment_rate, 4),
        "revenue_by_day": revenue_by_day,
        "top_products": top_products,
    }


# ---------------------------------------------------------------------------
# Revenue leaks
# ---------------------------------------------------------------------------
async def get_revenue_leaks(db: AsyncSession, merchant_id: UUID) -> list[leaks.LeakFinding]:
    since_90d = UTC_NOW() - timedelta(days=90)
    since_30d = UTC_NOW() - timedelta(days=30)

    refund_stats_rows = (
        await db.execute(
            select(
                Product.id,
                Product.name,
                func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0),
                func.coalesce(func.sum(Refund.amount), 0),
                func.count(func.distinct(Order.id)),
            )
            .select_from(Product)
            .join(OrderItem, OrderItem.product_id == Product.id)
            .join(Order, Order.id == OrderItem.order_id)
            .outerjoin(Refund, Refund.order_id == Order.id)
            .where(Product.merchant_id == merchant_id, Order.created_at >= since_90d)
            .group_by(Product.id, Product.name)
        )
    ).all()
    refund_stats = [
        leaks.ProductRefundStats(
            product_id=str(pid), product_name=name, revenue=float(rev), refund_amount=float(ref), order_count=int(cnt)
        )
        for pid, name, rev, ref, cnt in refund_stats_rows
    ]

    margin_rows = (
        await db.execute(
            select(
                Product.id,
                Product.name,
                Product.price,
                Product.cost,
                func.coalesce(func.sum(OrderItem.quantity), 0),
            )
            .select_from(Product)
            .join(OrderItem, OrderItem.product_id == Product.id)
            .join(Order, Order.id == OrderItem.order_id)
            .where(Product.merchant_id == merchant_id, Order.created_at >= since_90d)
            .where(Order.status != OrderStatus.CANCELLED)
            .group_by(Product.id, Product.name, Product.price, Product.cost)
        )
    ).all()
    margin_stats = [
        leaks.ProductMarginStats(product_id=str(pid), product_name=name, price=float(p), cost=float(c), units_sold=int(u))
        for pid, name, p, c, u in margin_rows
    ]

    cart_rows = (
        await db.execute(
            select(Cart.status, func.coalesce(func.sum(Cart.total_amount), 0), func.count(Cart.id))
            .where(Cart.merchant_id == merchant_id, Cart.created_at >= since_30d)
            .group_by(Cart.status)
        )
    ).all()
    abandoned_value, abandoned_count, total_carts, converted_value = 0.0, 0, 0, 0.0
    for status, total, count in cart_rows:
        total_carts += count
        if status in (CartStatus.ABANDONED, CartStatus.RECOVERED):
            abandoned_value += float(total)
            abandoned_count += count
        elif status == CartStatus.CONVERTED:
            converted_value += float(total)
    abandonment_rate = (abandoned_count / total_carts) if total_carts else 0.0

    month_label = func.to_char(Order.created_at, "YYYY-MM")
    monthly_rows = (
        await db.execute(
            select(month_label, func.coalesce(func.sum(Order.total_amount), 0))
            .where(Order.merchant_id == merchant_id, Order.status != OrderStatus.CANCELLED)
            .group_by(month_label)
            .order_by(month_label)
        )
    ).all()
    monthly_revenue = [(label, float(rev)) for label, rev in monthly_rows]

    findings = leaks.aggregate_leak_findings(
        leaks.detect_high_refund_products(refund_stats),
        leaks.detect_low_margin_products(margin_stats),
        leaks.detect_cart_abandonment_leak(
            abandoned_value_30d=abandoned_value, completed_revenue_30d=converted_value, abandonment_rate=abandonment_rate
        ),
        leaks.detect_revenue_decline(monthly_revenue),
    )
    return findings


# ---------------------------------------------------------------------------
# Customer RFM helper (shared by segmentation + churn)
# ---------------------------------------------------------------------------
async def _fetch_customer_order_stats(db: AsyncSession, merchant_id: UUID) -> list[dict]:
    rows = (
        await db.execute(
            select(
                Customer.id,
                Customer.name,
                func.max(Order.created_at),
                func.count(Order.id),
                func.coalesce(func.sum(Order.total_amount), 0),
                func.min(Order.created_at),
            )
            .select_from(Customer)
            .join(Order, Order.customer_id == Customer.id)
            .where(Customer.merchant_id == merchant_id, Order.status != OrderStatus.CANCELLED)
            .group_by(Customer.id, Customer.name)
        )
    ).all()

    now = UTC_NOW()
    results = []
    for customer_id, name, last_order, order_count, total_spent, first_order in rows:
        recency_days = (now - last_order).days if last_order else 9999
        span_days = (last_order - first_order).days if last_order and first_order else 0
        avg_interval = (span_days / (order_count - 1)) if order_count and order_count > 1 else None
        results.append(
            {
                "customer_id": str(customer_id),
                "customer_name": name,
                "recency_days": recency_days,
                "frequency": int(order_count),
                "monetary": float(total_spent),
                "avg_days_between_orders": avg_interval,
            }
        )
    return results


async def get_customer_segments(db: AsyncSession, merchant_id: UUID) -> list[dict]:
    stats = await _fetch_customer_order_stats(db, merchant_id)
    rfm_inputs = [
        seg.CustomerRFM(customer_id=s["customer_id"], recency_days=s["recency_days"], frequency=s["frequency"], monetary=s["monetary"])
        for s in stats
    ]
    segmented = seg.segment_customers(rfm_inputs)
    by_id = {s["customer_id"]: s for s in stats}

    return [
        {
            "customer_id": r.customer_id,
            "customer_name": by_id[r.customer_id]["customer_name"],
            "segment": r.segment,
            "r_score": r.r_score,
            "f_score": r.f_score,
            "m_score": r.m_score,
            "recency_days": by_id[r.customer_id]["recency_days"],
            "frequency": by_id[r.customer_id]["frequency"],
            "monetary": by_id[r.customer_id]["monetary"],
        }
        for r in segmented
    ]


async def get_abandoned_carts(db: AsyncSession, merchant_id: UUID, *, limit: int = 50) -> list[dict]:
    rows = (
        await db.execute(
            select(Cart, Customer.name, Customer.email)
            .join(Customer, Customer.id == Cart.customer_id)
            .where(Cart.merchant_id == merchant_id, Cart.status == CartStatus.ABANDONED)
            .order_by(Cart.abandoned_at.desc())
            .limit(limit)
        )
    ).all()

    now = UTC_NOW()
    results = []
    for cart, customer_name, customer_email in rows:
        abandoned_at = cart.abandoned_at or cart.created_at
        hours_since = (now - abandoned_at).total_seconds() / 3600

        item_rows = (
            await db.execute(
                select(Product.name, CartItem.quantity, CartItem.unit_price)
                .join(Product, Product.id == CartItem.product_id)
                .where(CartItem.cart_id == cart.id)
            )
        ).all()
        items = [
            {"product_name": name, "quantity": int(qty), "unit_price": float(price)} for name, qty, price in item_rows
        ]

        results.append(
            {
                "cart_id": str(cart.id),
                "customer_id": str(cart.customer_id),
                "customer_name": customer_name,
                "customer_email": customer_email,
                "total_amount": float(cart.total_amount),
                "hours_since_abandoned": round(hours_since, 1),
                "items": items,
            }
        )
    return results


async def get_churn_risks(db: AsyncSession, merchant_id: UUID) -> list[dict]:
    stats = await _fetch_customer_order_stats(db, merchant_id)
    inputs = [
        churn_svc.ChurnInput(
            customer_id=s["customer_id"],
            days_since_last_order=s["recency_days"],
            total_orders=s["frequency"],
            avg_days_between_orders=s["avg_days_between_orders"],
        )
        for s in stats
    ]
    results = churn_svc.compute_churn_risk_batch(inputs)
    by_id = {s["customer_id"]: s for s in stats}

    out = [
        {
            "customer_id": r.customer_id,
            "customer_name": by_id[r.customer_id]["customer_name"],
            "risk_score": r.risk_score,
            "risk_tier": r.risk_tier,
            "reason": r.reason,
            "days_since_last_order": by_id[r.customer_id]["recency_days"],
            "total_orders": by_id[r.customer_id]["frequency"],
        }
        for r in results
    ]
    out.sort(key=lambda x: -x["risk_score"])
    return out
