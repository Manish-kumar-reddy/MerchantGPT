from pydantic import BaseModel


class DashboardSummary(BaseModel):
    revenue_30d: float
    orders_30d: int
    avg_order_value_30d: float
    refund_amount_30d: float
    refund_rate_30d: float
    active_customers_30d: int
    abandoned_cart_value_30d: float
    cart_abandonment_rate_30d: float
    revenue_by_day: list[dict]  # [{"date": "2026-08-01", "revenue": 123.45}, ...]
    top_products: list[dict]  # [{"name": "...", "revenue": 123.45, "units": 4}, ...]


class LeakFindingOut(BaseModel):
    leak_type: str
    severity: str
    title: str
    description: str
    estimated_monthly_impact: float
    recommendation: str


class CustomerSegmentOut(BaseModel):
    customer_id: str
    customer_name: str
    segment: str
    r_score: int
    f_score: int
    m_score: int
    recency_days: int
    frequency: int
    monetary: float


class SegmentSummaryOut(BaseModel):
    segment: str
    customer_count: int
    total_monetary: float


class ChurnRiskOut(BaseModel):
    customer_id: str
    customer_name: str
    risk_score: float
    risk_tier: str
    reason: str
    days_since_last_order: int
    total_orders: int
