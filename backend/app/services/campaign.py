"""
Marketing campaign generation. Every campaign type has a deterministic,
rule-based draft that works with zero external dependencies -- if
ANTHROPIC_API_KEY is configured, that draft is polished into more natural
copy by a single (non-tool-calling) Claude completion, but a missing/failing
API key degrades to the rule-based draft rather than failing the request.
"""

from uuid import UUID

import anthropic
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import Campaign, CampaignType
from app.services import analytics
from app.services.cart_recovery import build_recovery_message, CartItemInfo

settings = get_settings()

POLISH_SYSTEM_PROMPT = (
    "You are a direct-response e-commerce copywriter. You will be given a draft subject line and email body. "
    "Rewrite them to be more natural, persuasive, and concise while keeping every factual claim (prices, "
    "discounts, product names) exactly as given -- never invent an offer or detail that wasn't in the draft. "
    "Respond with exactly two lines: the first line is the subject, the second line is the full body with \\n "
    "for line breaks. No preamble, no explanation."
)


async def _polish_with_claude(subject: str, body: str) -> tuple[str, str]:
    if not settings.anthropic_api_key:
        return subject, body
    try:
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        response = await client.messages.create(
            model=settings.anthropic_model,
            max_tokens=600,
            system=POLISH_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Subject: {subject}\n\nBody:\n{body}"}],
        )
        text = "".join(block.text for block in response.content if block.type == "text").strip()
        lines = text.split("\n", 1)
        if len(lines) == 2 and lines[0].strip():
            polished_subject = lines[0].replace("Subject:", "").strip()
            polished_body = lines[1].replace("Body:", "").strip()
            return polished_subject, polished_body
    except Exception:
        pass  # Fall back to the rule-based draft below -- never fail campaign generation over a copy polish.
    return subject, body


async def generate_cart_recovery_campaign(db: AsyncSession, merchant_id: UUID) -> Campaign:
    carts = await analytics.get_abandoned_carts(db, merchant_id, limit=100)
    if not carts:
        raise ValueError("No abandoned carts to build a recovery campaign from.")

    # Use the most-abandoned (oldest, highest-value) cart as the representative template.
    template_cart = max(carts, key=lambda c: c["total_amount"])
    items = [CartItemInfo(product_name=i["product_name"], quantity=i["quantity"], unit_price=i["unit_price"]) for i in template_cart["items"]]
    draft = build_recovery_message(
        customer_name=template_cart["customer_name"],
        items=items,
        cart_total=template_cart["total_amount"],
        hours_since_abandoned=template_cart["hours_since_abandoned"],
    )
    subject, body = await _polish_with_claude(draft.subject, draft.body)

    campaign = Campaign(
        merchant_id=merchant_id,
        name=f"Cart Recovery -- {len(carts)} abandoned carts",
        campaign_type=CampaignType.CART_RECOVERY,
        target_segment="abandoned_cart",
        audience_size=len(carts),
        subject_line=subject,
        body=body,
        meta={"discount_suggested": draft.discount_suggested, "discount_percent": draft.discount_percent},
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return campaign


async def generate_segment_campaign(db: AsyncSession, merchant_id: UUID, *, segment: str) -> Campaign:
    all_segments = await analytics.get_customer_segments(db, merchant_id)
    matching = [s for s in all_segments if s["segment"] == segment]
    if not matching:
        raise ValueError(f"No customers currently in the '{segment}' segment.")

    campaign_type = CampaignType.WIN_BACK if segment in ("At Risk", "Lost") else CampaignType.SEGMENT_PROMO
    subject, body = _draft_for_segment(segment)
    subject, body = await _polish_with_claude(subject, body)

    campaign = Campaign(
        merchant_id=merchant_id,
        name=f"{segment} -- {campaign_type.value.replace('_', ' ').title()}",
        campaign_type=campaign_type,
        target_segment=segment,
        audience_size=len(matching),
        subject_line=subject,
        body=body,
        meta={"avg_monetary": round(sum(s["monetary"] for s in matching) / len(matching), 2)},
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return campaign


def _draft_for_segment(segment: str) -> tuple[str, str]:
    if segment == "At Risk":
        subject = "We miss you -- here's 15% off your next order"
        body = (
            "Hi there,\n\nIt's been a while since your last order, and we wanted to check in. "
            "Here's 15% off to welcome you back -- no strings attached.\n\n"
            "Use code WELCOME15 at checkout."
        )
    elif segment == "Lost":
        subject = "One more try: 20% off, on us"
        body = (
            "Hi there,\n\nWe haven't seen you in a while. If something didn't work out last time, "
            "we'd genuinely like to know -- just reply to this email. Otherwise, here's 20% off if you'd "
            "like to give us another shot.\n\nUse code COMEBACK20 at checkout."
        )
    elif segment == "Champions":
        subject = "You're one of our best customers -- early access inside"
        body = (
            "Hi there,\n\nAs one of our most loyal customers, you're getting early access to our newest "
            "arrivals before anyone else. Take a look before they're gone."
        )
    elif segment == "New Customers":
        subject = "Welcome! Here's what to try next"
        body = (
            "Hi there,\n\nThanks for your first order with us. Based on what you bought, we think you'll "
            "love a few other things too -- take a look and let us know what you think."
        )
    else:
        subject = "Something new, just for you"
        body = "Hi there,\n\nWe put together a few recommendations we think you'll like. Take a look and see what's new."
    return subject, body


async def generate_weekly_report_narrative(*, metrics: dict, findings_summary: list[str]) -> str:
    """Turns computed metrics (always correct, deterministic) into a readable
    executive narrative. Falls back to a template if Claude isn't configured
    -- the report still generates, just with plainer prose."""
    if not settings.anthropic_api_key:
        return _template_narrative(metrics, findings_summary)

    try:
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        prompt = (
            "Write a concise executive summary (150-200 words) for an e-commerce merchant's weekly report. "
            "Use only the numbers given below -- never invent a figure. Be direct about both wins and problems. "
            f"\n\nMetrics: {metrics}\n\nTop issues: {findings_summary}"
        )
        response = await client.messages.create(
            model=settings.anthropic_model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(block.text for block in response.content if block.type == "text").strip()
        if text:
            return text
    except Exception:
        pass
    return _template_narrative(metrics, findings_summary)


def _template_narrative(metrics: dict, findings_summary: list[str]) -> str:
    lines = [
        f"Revenue over the period was ${metrics.get('revenue_30d', 0):,.2f} across {metrics.get('orders_30d', 0)} "
        f"orders (avg order value ${metrics.get('avg_order_value_30d', 0):,.2f}).",
        f"Refunds totaled ${metrics.get('refund_amount_30d', 0):,.2f} "
        f"({metrics.get('refund_rate_30d', 0) * 100:.1f}% of revenue).",
        f"Cart abandonment rate was {metrics.get('cart_abandonment_rate_30d', 0) * 100:.1f}%, representing "
        f"${metrics.get('abandoned_cart_value_30d', 0):,.2f} in at-risk revenue.",
    ]
    if findings_summary:
        lines.append("Top issues this period: " + "; ".join(findings_summary) + ".")
    else:
        lines.append("No major revenue leaks were detected this period.")
    return " ".join(lines)
