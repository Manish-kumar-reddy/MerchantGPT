from datetime import date, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Report
from app.services import analytics
from app.services.campaign import generate_weekly_report_narrative


async def generate_weekly_report(db: AsyncSession, merchant_id: UUID) -> Report:
    metrics = await analytics.get_dashboard_summary(db, merchant_id)
    findings = await analytics.get_revenue_leaks(db, merchant_id)
    findings_summary = [f"{f.title} (${f.estimated_monthly_impact:,.0f}/mo est. impact)" for f in findings[:3]]

    narrative = await generate_weekly_report_narrative(metrics=metrics, findings_summary=findings_summary)

    today = date.today()
    report = Report(
        merchant_id=merchant_id,
        period_start=today - timedelta(days=7),
        period_end=today,
        metrics={**metrics, "top_leak_findings": findings_summary},
        narrative=narrative,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report
