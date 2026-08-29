import uuid
from datetime import date, datetime

from sqlalchemy import String, DateTime, Date, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Customer(Base):
    """An end-shopper of a merchant (not a MerchantGPT login account)."""

    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    first_order_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    merchant: Mapped["Merchant"] = relationship(back_populates="customers")
    orders: Mapped[list["Order"]] = relationship(back_populates="customer", cascade="all, delete-orphan")
    carts: Mapped[list["Cart"]] = relationship(back_populates="customer", cascade="all, delete-orphan")

    __table_args__ = ({"comment": "One row per (merchant, shopper)."},)
