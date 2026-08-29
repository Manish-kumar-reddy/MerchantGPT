# API Reference

Base URL: `{API_URL}/api/v1`. All endpoints except `/auth/register` and `/auth/login` require `Authorization: Bearer <token>`. Interactive Swagger docs are also served at `{API_URL}/docs`.

Every endpoint is scoped to the authenticated user's `merchant_id` -- there is no cross-merchant data access.

## Auth

### `POST /auth/register`
```json
{ "merchant_name": "string", "name": "string", "email": "user@example.com", "password": "string (8-72 chars)", "industry": "string?" }
```
Creates a new merchant + owner user. Returns `TokenResponse`.

### `POST /auth/login`
```json
{ "email": "user@example.com", "password": "string" }
```
Returns `TokenResponse`: `{ access_token, token_type: "bearer", user }`.

### `GET /auth/me`
Returns the current `UserOut`.

## Analytics

### `GET /analytics/dashboard`
30-day summary: `revenue_30d`, `orders_30d`, `avg_order_value_30d`, `refund_amount_30d`, `refund_rate_30d`, `active_customers_30d`, `abandoned_cart_value_30d`, `cart_abandonment_rate_30d`, `revenue_by_day: [{date, revenue}]`, `top_products: [{name, revenue, units}]`.

### `GET /analytics/revenue-leaks`
`{ "findings": [{ leak_type, severity, title, description, estimated_monthly_impact, recommendation }] }`. Detectors: high refund rate per product, thin/negative margin per product, cart abandonment rate, month-over-month revenue decline.

### `GET /analytics/segments`
`{ "customers": [{ customer_id, customer_name, segment, r_score, f_score, m_score, recency_days, frequency, monetary }], "summary": [{ segment, customer_count, total_monetary }] }`. Segments: Champions, Loyal Customers, Big Spenders, At Risk, New Customers, Lost, Needs Attention.

### `GET /analytics/churn`
`{ "customers": [{ customer_id, customer_name, risk_score, risk_tier, reason, days_since_last_order, total_orders }] }`. `risk_tier` is `low` / `medium` / `high`.

### `GET /analytics/abandoned-carts`
`{ "carts": [{ cart_id, customer_id, customer_name, customer_email, total_amount, hours_since_abandoned, items: [{product_name, quantity, unit_price}] }] }`.

## Chat

### `GET /chat/sessions`
`[{ id, title, created_at }]`, most recent first.

### `GET /chat/sessions/{session_id}/messages`
`[{ id, role: "user"|"assistant", content, created_at }]`, oldest first.

### `POST /chat/messages`
```json
{ "session_id": "uuid?", "message": "string" }
```
Omit `session_id` to start a new conversation. Returns `{ session_id, reply, tool_calls_made: string[] }`. If `ANTHROPIC_API_KEY` is not configured, `reply` explains this and `tool_calls_made` is empty -- the call still succeeds (200) and the turn is persisted.

## Campaigns

### `GET /campaigns`
`[CampaignOut]`, most recent first.

### `POST /campaigns/generate`
```json
{ "campaign_type": "cart_recovery" | "win_back" | "segment_promo", "target_segment": "string?" }
```
`target_segment` is required for `win_back` and `segment_promo` (400 if missing, 400 if the segment currently has no customers). Returns the created `CampaignOut`: `{ id, name, campaign_type, status, target_segment, audience_size, subject_line, body, created_at }`.

## Reports

### `GET /reports/weekly`
`[WeeklyReportOut]`, most recent first.

### `POST /reports/weekly/generate`
Generates a report for the trailing 7 days. Returns `{ id, period_start, period_end, metrics, narrative, created_at }`, where `metrics` includes `revenue_30d`, `orders_30d`, `top_products`, `revenue_by_day`, `refund_rate_30d`, `top_leak_findings`, etc.

## Health

### `GET /api/health`
`{ "status": "ok" }`. Not versioned, no auth required.
