from __future__ import annotations

from fastapi import APIRouter, Query, Request

from app.modules.analytics.dto import (
    AnalyticsOverviewDto,
    PostHogConfigDto,
    UpdatePostHogConfigDto,
)

router = APIRouter(prefix="/v1/analytics", tags=["analytics"])


@router.get("/trinkow", response_model=AnalyticsOverviewDto)
async def get_trinkow_analytics(
    request: Request,
    time_range: str = Query(default="7d", pattern="^(24h|7d|30d)$"),
) -> AnalyticsOverviewDto:
    service = request.app.state.analytics_service
    return await service.get_overview(time_range=time_range)


@router.get("/config", response_model=PostHogConfigDto)
async def get_analytics_config(request: Request) -> PostHogConfigDto:
    service = request.app.state.analytics_service
    return service.config_status()


@router.post("/config", response_model=PostHogConfigDto)
async def update_analytics_config(
    payload: UpdatePostHogConfigDto, request: Request
) -> PostHogConfigDto:
    service = request.app.state.analytics_service
    service.update_key(payload.personal_api_key, payload.project_id)
    return service.config_status()

