from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status

from app.modules.apps.dto import CreateAppDto, ManagedAppDto, UpdateAppDto

router = APIRouter(prefix="/v1/apps", tags=["apps"])


@router.get("", response_model=list[ManagedAppDto])
async def list_apps(request: Request) -> list[ManagedAppDto]:
    return request.app.state.app_service.list()


@router.post("", response_model=ManagedAppDto, status_code=status.HTTP_201_CREATED)
async def create_app(payload: CreateAppDto, request: Request) -> ManagedAppDto:
    return request.app.state.app_service.create(payload)


@router.patch("/{app_id}", response_model=ManagedAppDto)
async def update_app(app_id: UUID, payload: UpdateAppDto, request: Request) -> ManagedAppDto:
    result = request.app.state.app_service.update(app_id, payload)
    if result is None:
        raise HTTPException(status_code=404, detail="Uygulama bulunamadı.")
    return result

