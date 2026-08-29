"""
Tool definitions for the Claude chat agent, following Anthropic's Messages API
tool-use schema exactly (`name` / `description` / `input_schema`). Every tool
maps 1:1 to a read-only function in app.services.analytics -- the agent can
query the merchant's real data, but cannot write to it. That's a deliberate
boundary: a chat agent that can silently mutate revenue data on a
misinterpreted request is a much worse failure mode than one that can only
read and recommend.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services import analytics

TOOLS = [
    {
        "name": "get_dashboard_summary",
        "description": (
            "Get the merchant's core business metrics for the last 30 days: revenue, order count, average "
            "order value, refund amount/rate, active customers, abandoned cart value/rate, daily revenue "
            "series, and top 5 products by revenue. Use this for any general 'how is the business doing' "
            "or 'what's our revenue' question."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_revenue_leaks",
        "description": (
            "Get a ranked list of detected revenue leaks: products with high refund rates, products selling "
            "at thin or negative margin, high cart abandonment, and month-over-month revenue decline. Each "
            "finding includes severity, estimated monthly dollar impact, and a specific recommendation. Use "
            "this for 'where are we losing money' or 'why did revenue drop' questions."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_customer_segments",
        "description": (
            "Get RFM-based customer segments (Champions, Loyal Customers, Big Spenders, At Risk, New "
            "Customers, Lost, Needs Attention) for every customer, with their recency/frequency/monetary "
            "stats. Use this for 'who are our best customers' or 'how many customers are at risk' questions."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_churn_risks",
        "description": (
            "Get churn risk scores (0-1) for every customer with at least one order, ranked highest-risk "
            "first, based on how overdue each customer is relative to their own normal ordering cadence. Use "
            "this for 'who is about to churn' or 'which customers should we win back' questions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "risk_tier": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Optional -- only return customers at this risk tier.",
                },
                "limit": {"type": "integer", "description": "Max customers to return. Defaults to 20."},
            },
            "required": [],
        },
    },
    {
        "name": "get_abandoned_carts",
        "description": (
            "Get the merchant's currently abandoned carts (not yet recovered or converted), with customer "
            "info, cart value, items, and hours since abandoned. Use this for 'how many abandoned carts do "
            "we have' or when the merchant asks to draft a cart recovery campaign."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"limit": {"type": "integer", "description": "Max carts to return. Defaults to 20."}},
            "required": [],
        },
    },
]


async def execute_tool(tool_name: str, tool_input: dict, db: AsyncSession, merchant_id: UUID) -> dict:
    if tool_name == "get_dashboard_summary":
        return await analytics.get_dashboard_summary(db, merchant_id)

    if tool_name == "get_revenue_leaks":
        findings = await analytics.get_revenue_leaks(db, merchant_id)
        return {"findings": [f.__dict__ for f in findings]}

    if tool_name == "get_customer_segments":
        segments = await analytics.get_customer_segments(db, merchant_id)
        counts: dict[str, int] = {}
        for s in segments:
            counts[s["segment"]] = counts.get(s["segment"], 0) + 1
        return {"segment_counts": counts, "customers": segments[:50]}

    if tool_name == "get_churn_risks":
        risks = await analytics.get_churn_risks(db, merchant_id)
        risk_tier = tool_input.get("risk_tier")
        if risk_tier:
            risks = [r for r in risks if r["risk_tier"] == risk_tier]
        limit = tool_input.get("limit", 20)
        return {"customers": risks[:limit], "total_matching": len(risks)}

    if tool_name == "get_abandoned_carts":
        limit = tool_input.get("limit", 20)
        carts = await analytics.get_abandoned_carts(db, merchant_id, limit=limit)
        return {"carts": carts}

    return {"error": f"Unknown tool: {tool_name}"}
