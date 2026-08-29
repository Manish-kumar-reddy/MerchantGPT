from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.services import analytics

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
async def dashboard(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await analytics.get_dashboard_summary(db, current_user.merchant_id)


@router.get("/revenue-leaks")
async def revenue_leaks(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    findings = await analytics.get_revenue_leaks(db, current_user.merchant_id)
    return {"findings": [f.__dict__ for f in findings]}


@router.get("/segments")
async def segments(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    customers = await analytics.get_customer_segments(db, current_user.merchant_id)
    summary: dict[str, dict] = {}
    for c in customers:
        bucket = summary.setdefault(c["segment"], {"segment": c["segment"], "customer_count": 0, "total_monetary": 0.0})
        bucket["customer_count"] += 1
        bucket["total_monetary"] += c["monetary"]
    return {"customers": customers, "summary": list(summary.values())}


@router.get("/churn")
async def churn(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return {"customers": await analytics.get_churn_risks(db, current_user.merchant_id)}


@router.get("/abandoned-carts")
async def abandoned_carts(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return {"carts": await analytics.get_abandoned_carts(db, current_user.merchant_id)}
