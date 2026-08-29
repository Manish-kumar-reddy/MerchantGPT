export interface UserOut {
  id: string;
  name: string;
  email: string;
  role: string;
  merchant_id: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserOut;
}

export interface RevenueByDay {
  date: string;
  revenue: number;
}

export interface TopProduct {
  name: string;
  revenue: number;
  units: number;
}

export interface DashboardSummary {
  revenue_30d: number;
  orders_30d: number;
  avg_order_value_30d: number;
  refund_amount_30d: number;
  refund_rate_30d: number;
  active_customers_30d: number;
  abandoned_cart_value_30d: number;
  cart_abandonment_rate_30d: number;
  revenue_by_day: RevenueByDay[];
  top_products: TopProduct[];
}

export type LeakSeverity = "low" | "medium" | "high";

export interface LeakFinding {
  leak_type: string;
  severity: LeakSeverity;
  title: string;
  description: string;
  estimated_monthly_impact: number;
  recommendation: string;
}

export interface CustomerSegment {
  customer_id: string;
  customer_name: string;
  segment: string;
  r_score: number;
  f_score: number;
  m_score: number;
  recency_days: number;
  frequency: number;
  monetary: number;
}

export interface SegmentSummary {
  segment: string;
  customer_count: number;
  total_monetary: number;
}

export type RiskTier = "low" | "medium" | "high";

export interface ChurnRisk {
  customer_id: string;
  customer_name: string;
  risk_score: number;
  risk_tier: RiskTier;
  reason: string;
  days_since_last_order: number;
  total_orders: number;
}

export interface CartItemInfo {
  product_name: string;
  quantity: number;
  unit_price: number;
}

export interface AbandonedCart {
  cart_id: string;
  customer_id: string;
  customer_name: string;
  customer_email: string;
  total_amount: number;
  hours_since_abandoned: number;
  items: CartItemInfo[];
}

export type CampaignType = "cart_recovery" | "win_back" | "segment_promo";
export type CampaignStatus = "draft" | "ready" | "sent";

export interface Campaign {
  id: string;
  name: string;
  campaign_type: CampaignType;
  status: CampaignStatus;
  target_segment: string;
  audience_size: number;
  subject_line: string;
  body: string;
  created_at: string;
}

export interface WeeklyReport {
  id: string;
  period_start: string;
  period_end: string;
  metrics: Record<string, unknown>;
  narrative: string;
  created_at: string;
}

export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface SendMessageResponse {
  session_id: string;
  reply: string;
  tool_calls_made: string[];
}
