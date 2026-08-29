"""
Abandoned cart recovery message generation.

`build_recovery_message` is a pure, deterministic, template-based generator
that works with zero external dependencies -- it never fails and never needs
an API key. `app/services/campaign.py` can optionally rewrite this draft
into more natural marketing copy via Claude, but the template output is
already a complete, usable message on its own, which matters because the
Claude call can fail (rate limit, missing key, network) and the feature must
still work when it does.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CartItemInfo:
    product_name: str
    quantity: int
    unit_price: float


@dataclass(frozen=True)
class RecoveryMessage:
    subject: str
    body: str
    discount_suggested: bool
    discount_percent: int | None


def _format_item_list(items: list[CartItemInfo]) -> str:
    lines = [f"  - {i.quantity} x {i.product_name} (${i.unit_price:.2f} each)" for i in items]
    return "\n".join(lines)


def build_recovery_message(
    *,
    customer_name: str,
    items: list[CartItemInfo],
    cart_total: float,
    hours_since_abandoned: float,
) -> RecoveryMessage:
    """
    Message tone/offer escalates with how long the cart has sat abandoned:
      - under 24h: a plain, no-discount reminder (most recoverable carts convert here)
      - 24-72h: a soft nudge, no discount yet
      - over 72h: a discount incentive, since a plain reminder likely already failed
    """
    first_name = customer_name.split(" ")[0] if customer_name else "there"
    item_list = _format_item_list(items)

    if hours_since_abandoned < 24:
        subject = f"{first_name}, you left something in your cart"
        body = (
            f"Hi {first_name},\n\n"
            f"You still have these items waiting in your cart:\n{item_list}\n\n"
            f"Total: ${cart_total:.2f}\n\n"
            "Complete your order whenever you're ready -- your cart will be saved for you."
        )
        return RecoveryMessage(subject=subject, body=body, discount_suggested=False, discount_percent=None)

    if hours_since_abandoned < 72:
        subject = f"Still thinking it over, {first_name}?"
        body = (
            f"Hi {first_name},\n\n"
            f"Your cart is still here:\n{item_list}\n\n"
            f"Total: ${cart_total:.2f}\n\n"
            "If anything's unclear about sizing, shipping, or the product itself, just reply to this email -- "
            "happy to help before you decide."
        )
        return RecoveryMessage(subject=subject, body=body, discount_suggested=False, discount_percent=None)

    discount_percent = 10
    discounted_total = cart_total * (1 - discount_percent / 100)
    subject = f"{first_name}, here's {discount_percent}% off to complete your order"
    body = (
        f"Hi {first_name},\n\n"
        f"Your cart is still waiting:\n{item_list}\n\n"
        f"Original total: ${cart_total:.2f}\n"
        f"With {discount_percent}% off: ${discounted_total:.2f}\n\n"
        "This offer is valid for the next 48 hours. Complete your order below."
    )
    return RecoveryMessage(subject=subject, body=body, discount_suggested=True, discount_percent=discount_percent)
