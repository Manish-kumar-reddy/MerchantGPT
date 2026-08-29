from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Campaign, Report, User
from app.schemas.campaign import CampaignOut, GenerateCampaignRequest, WeeklyReportOut
from app.services.campaign import generate_cart_recovery_campaign, generate_segment_campaign
from app.services.report import generate_weekly_report

router = APIRouter(tags=["campaigns"])


@router.get("/campaigns", response_model=list[CampaignOut])
async def list_campaigns(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(Campaign).where(Campaign.merchant_id == current_user.merchant_id).order_by(Campaign.created_at.desc())
        )
    ).scalars().all()
    return list(rows)


@router.post("/campaigns/generate", response_model=CampaignOut, status_code=status.HTTP_201_CREATED)
async def generate_campaign(
    payload: GenerateCampaignRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        if payload.campaign_type == "cart_recovery":
            campaign = await generate_cart_recovery_campaign(db, current_user.merchant_id)
        elif payload.campaign_type in ("win_back", "segment_promo"):
            if not payload.target_segment:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="target_segment is required for this campaign type."
                )
            campaign = await generate_segment_campaign(db, current_user.merchant_id, segment=payload.target_segment)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown campaign_type: {payload.campaign_type}")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return campaign


@router.get("/reports/weekly", response_model=list[WeeklyReportOut])
async def list_weekly_reports(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(Report).where(Report.merchant_id == current_user.merchant_id).order_by(Report.created_at.desc())
        )
    ).scalars().all()
    return list(rows)


@router.post("/reports/weekly/generate", response_model=WeeklyReportOut, status_code=status.HTTP_201_CREATED)
async def create_weekly_report(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    report = await generate_weekly_report(db, current_user.merchant_id)
    return report
