import enum
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Text, Integer, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CampaignType(str, enum.Enum):
    CART_RECOVERY = "cart_recovery"
    WIN_BACK = "win_back"
    SEGMENT_PROMO = "segment_promo"


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    READY = "ready"
    SENT = "sent"


class Campaign(Base):
    """An AI-generated, human-reviewable marketing campaign. Nothing is ever
    actually sent to a real customer by this app -- `status` moving to SENT is
    a manual action the merchant takes after reviewing the generated copy."""

    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    campaign_type: Mapped[CampaignType] = mapped_column(Enum(CampaignType, name="campaign_type"), nullable=False)
    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus, name="campaign_status"), nullable=False, default=CampaignStatus.DRAFT
    )
    target_segment: Mapped[str] = mapped_column(String(60), nullable=False)
    audience_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    subject_line: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
