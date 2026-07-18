"""Analytics endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import AnalyticsServiceDep
from app.api.serialization import serialize_item
from app.schemas.analytics import AnalyticsOverview

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
async def analytics_overview(
    service: AnalyticsServiceDep,
    top_n: int = Query(default=5, ge=1, le=20),
) -> AnalyticsOverview:
    """Aggregated wardrobe usage metrics for the analytics dashboard."""
    overview = await service.overview(top_n=top_n)
    # Resolve image URLs on the most/least-worn item lists.
    overview.most_worn = [serialize_item(i) for i in overview.most_worn]
    overview.least_worn = [serialize_item(i) for i in overview.least_worn]
    return overview
