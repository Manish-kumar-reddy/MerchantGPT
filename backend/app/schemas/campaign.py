from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class GenerateCampaignRequest(BaseModel):
    campaign_type: str  # "cart_recovery" | "win_back" | "segment_promo"
    target_segment: str | None = None  # required for win_back / segment_promo


class CampaignOut(BaseModel):
    id: UUID
    name: str
    campaign_type: str
    status: str
    target_segment: str
    audience_size: int
    subject_line: str
    body: str
    created_at: datetime

    class Config:
        from_attributes = True


class WeeklyReportOut(BaseModel):
    id: UUID
    period_start: date
    period_end: date
    metrics: dict
    narrative: str
    created_at: datetime

    class Config:
        from_attributes = True
