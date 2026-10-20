from fastapi import APIRouter, Request

from app.modules.dashboard.dto import DashboardDto

router = APIRouter(prefix="/v1/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardDto)
async def dashboard(request: Request) -> DashboardDto:
    return await request.app.state.dashboard_service.get()

