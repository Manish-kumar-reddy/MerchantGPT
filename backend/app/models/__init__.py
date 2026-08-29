"""
Importing every model module here ensures SQLAlchemy's declarative registry
can resolve the string-based forward references used in relationship()
type hints (e.g. Mapped["Customer"]) regardless of import order elsewhere --
this module must be imported before Base.metadata.create_all() runs.
"""

from app.models.merchant import Merchant
from app.models.user import User
from app.models.customer import Customer
from app.models.product import Product
from app.models.order import Order, OrderItem, OrderStatus
from app.models.cart import Cart, CartItem, CartStatus
from app.models.refund import Refund
from app.models.chat import ChatSession, ChatMessage
from app.models.campaign import Campaign, CampaignType, CampaignStatus
from app.models.report import Report

__all__ = [
    "Merchant",
    "User",
    "Customer",
    "Product",
    "Order",
    "OrderItem",
    "OrderStatus",
    "Cart",
    "CartItem",
    "CartStatus",
    "Refund",
    "ChatSession",
    "ChatMessage",
    "Campaign",
    "CampaignType",
    "CampaignStatus",
    "Report",
]
