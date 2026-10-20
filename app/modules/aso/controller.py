from __future__ import annotations

import asyncio
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/v1", tags=["asobeast"])


@router.get("/aso/status")
async def status(request: Request) -> dict[str, object]:
    aso = request.app.state.aso_service
    if not aso.configured:
        return {"configured": False, "connected": False}
    try:
        return {"configured": True, "connected": True, "details": await aso.status()}
    except Exception as error:
        return {"configured": True, "connected": False, "error": str(error)}


@router.get("/apps/{app_id}/aso")
async def app_details(app_id: UUID, request: Request) -> dict[str, object]:
    managed = request.app.state.app_service.find(app_id)
    if managed is None:
        raise HTTPException(status_code=404, detail="Uygulama bulunamadı.")
    if not managed.asobeast_app_id:
        return {"linked": False}
    aso = request.app.state.aso_service
    summary, audit, keywords = await asyncio.gather(
        aso.summary(managed.asobeast_app_id),
        aso.audit(managed.asobeast_app_id),
        aso.keywords(managed.asobeast_app_id),
    )
    return {"linked": True, "summary": summary, "audit": audit, "keywords": keywords}


@router.post("/apps/{app_id}/aso/import")
async def import_app(app_id: UUID, request: Request) -> dict[str, object]:
    app_service = request.app.state.app_service
    managed = app_service.find(app_id)
    if managed is None:
        raise HTTPException(status_code=404, detail="Uygulama bulunamadı.")
    url = managed.app_store_url or managed.play_store_url
    if url is None:
        raise HTTPException(status_code=422, detail="Önce en az bir mağaza bağlantısı ekleyin.")
    imported = await request.app.state.aso_service.import_app(str(url))
    remote_id = imported.get("id")
    if isinstance(remote_id, str):
        app_service.link_asobeast(app_id, remote_id)
    return {"imported": imported, "app": app_service.find(app_id)}


@router.post("/apps/{app_id}/aso/run")
async def run_daily(app_id: UUID, request: Request) -> dict[str, object]:
    managed = request.app.state.app_service.find(app_id)
    if managed is None or not managed.asobeast_app_id:
        raise HTTPException(status_code=422, detail="Uygulama AsoBeast ile bağlı değil.")
    return await request.app.state.aso_service.run_daily(managed.asobeast_app_id)

