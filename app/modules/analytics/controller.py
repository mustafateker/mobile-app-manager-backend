from __future__ import annotations

from fastapi import APIRouter, Query, Request

from app.modules.analytics.dto import (
    AnalyticsOverviewDto,
    DeleteTrinkowUserDto,
    PostHogConfigDto,
    TrinkowUsersListDto,
    UpdatePostHogConfigDto,
    UpdateTrinkowUserStatusDto,
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


@router.get("/trinkow/users", response_model=TrinkowUsersListDto)
async def get_trinkow_users(
    request: Request,
    q: str | None = Query(default=None),
    filter: str | None = Query(default=None, pattern="^(all|today|premium|suspended)?$"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> TrinkowUsersListDto:
    service = request.app.state.trinkow_admin_service
    return await service.list_users(search=q, filter_type=filter, page=page, limit=limit)


@router.patch("/trinkow/users/{user_id}/status")
async def update_trinkow_user_status(
    user_id: str,
    payload: UpdateTrinkowUserStatusDto,
    request: Request,
) -> dict[str, object]:
    service = request.app.state.trinkow_admin_service
    return await service.update_user_status(user_id=user_id, askida=payload.askida)


@router.delete("/trinkow/users/{user_id}")
async def delete_trinkow_user(
    user_id: str,
    payload: DeleteTrinkowUserDto,
    request: Request,
) -> dict[str, str]:
    service = request.app.state.trinkow_admin_service
    return await service.delete_user(user_id=user_id, admin_password=payload.admin_password)

