from __future__ import annotations

import sqlite3
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from app.config import Settings, read_settings
from app.database import Database
from app.modules.apps.controller import router as apps_router
from app.modules.apps.service import AppService
from app.modules.aso.controller import router as aso_router
from app.modules.aso.service import AsoBeastError, AsoBeastService
from app.modules.auth.controller import router as auth_router
from app.modules.auth.service import AuthService, LoginRateLimiter
from app.modules.dashboard.controller import router as dashboard_router
from app.modules.dashboard.service import DashboardService


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or read_settings()
    database = Database(config.database_path)
    app_service = AppService(database)
    aso_service = AsoBeastService(str(config.asobeast_base_url), config.asobeast_api_token)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        database.close()

    app = FastAPI(title="Mobile App Manager Backend", version="1.0.0", lifespan=lifespan)
    app.state.settings = config
    app.state.database = database
    app.state.app_service = app_service
    app.state.aso_service = aso_service
    app.state.auth_service = AuthService(config)
    app.state.login_rate_limiter = LoginRateLimiter()
    app.state.dashboard_service = DashboardService(app_service, aso_service)

    @app.middleware("http")
    async def security_and_auth(request: Request, call_next):
        if (
            request.url.path.startswith("/v1/")
            and request.url.path != "/v1/auth/login"
            and request.method != "OPTIONS"
            and request.session.get("user") != "admin"
        ):
            return JSONResponse(status_code=401, content={"message": "Oturum gerekli."})
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, error: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "message": "Gönderilen alanları kontrol edin.",
                "issues": jsonable_encoder(error.errors()),
            },
        )

    @app.exception_handler(HTTPException)
    async def http_error(_: Request, error: HTTPException) -> JSONResponse:
        detail = error.detail if isinstance(error.detail, str) else "İstek başarısız oldu."
        return JSONResponse(status_code=error.status_code, content={"message": detail})

    @app.exception_handler(AsoBeastError)
    async def asobeast_error(_: Request, error: AsoBeastError) -> JSONResponse:
        if error.status_code is None:
            status_code = 503
        elif 400 <= error.status_code < 500:
            status_code = 422
        else:
            status_code = 502
        return JSONResponse(status_code=status_code, content={"message": str(error)})

    @app.exception_handler(sqlite3.IntegrityError)
    async def database_conflict(_: Request, __: sqlite3.IntegrityError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"message": "Bu slug zaten kullanılıyor."})

    @app.get("/health")
    async def health() -> dict[str, object]:
        return {"status": "ok", "asobeastConfigured": aso_service.configured}

    app.add_middleware(
        SessionMiddleware,
        secret_key=config.session_secret,
        session_cookie="mam_session",
        max_age=60 * 60 * 12,
        same_site="strict",
        https_only=config.node_env == "production",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(config.web_origin).rstrip("/")],
        allow_credentials=True,
        allow_methods=["GET", "HEAD", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Accept"],
    )

    app.include_router(auth_router)
    app.include_router(apps_router)
    app.include_router(dashboard_router)
    app.include_router(aso_router)
    return app
