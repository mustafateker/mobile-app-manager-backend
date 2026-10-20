from __future__ import annotations

from typing import Annotated
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Query, Request, Response

from app.modules.maps.dto import CreateMapsJobDto

router = APIRouter(prefix="/v1/maps", tags=["maps"])


@router.get("/status")
async def status(request: Request) -> dict[str, object]:
    service = request.app.state.maps_service
    if not service.configured:
        return {"configured": False, "connected": False}
    try:
        details = await service.health()
        return {"configured": True, "connected": bool(details.get("healthy")), "details": details}
    except Exception as error:
        return {"configured": True, "connected": False, "error": str(error)}


@router.post("/jobs", status_code=202)
async def create_job(payload: CreateMapsJobDto, request: Request) -> object:
    return await request.app.state.maps_service.json_request(
        "POST", "/jobs", json=payload.model_dump()
    )


@router.get("/jobs")
async def list_jobs(
    request: Request,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> object:
    params = {"limit": limit, "offset": offset}
    if status_filter:
        params["status"] = status_filter
    return await request.app.state.maps_service.json_request("GET", "/jobs", params=params)


@router.get("/jobs/{job_id}")
async def get_job(job_id: UUID, request: Request) -> object:
    return await request.app.state.maps_service.json_request("GET", f"/jobs/{job_id}")


@router.delete("/jobs/{job_id}", status_code=204)
async def delete_job(job_id: UUID, request: Request) -> Response:
    await request.app.state.maps_service.request("DELETE", f"/jobs/{job_id}")
    return Response(status_code=204)


@router.get("/jobs/{job_id}/results")
async def get_results(
    job_id: UUID,
    request: Request,
    limit: Annotated[int, Query(ge=1, le=1_000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> object:
    return await request.app.state.maps_service.json_request(
        "GET", f"/jobs/{job_id}/results", params={"limit": limit, "offset": offset}
    )


@router.get("/jobs/{job_id}/results.csv")
async def download_results(job_id: UUID, request: Request) -> Response:
    upstream = await request.app.state.maps_service.request(
        "GET", f"/jobs/{quote(str(job_id), safe='')}/results.csv"
    )
    disposition = upstream.headers.get(
        "content-disposition", f'attachment; filename="maps-{job_id}.csv"'
    )
    return Response(
        content=upstream.content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": disposition},
    )
