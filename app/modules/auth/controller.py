from fastapi import APIRouter, HTTPException, Request, Response, status

from app.modules.auth.dto import LoginDto, SessionDto

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/login", response_model=SessionDto)
async def login(payload: LoginDto, request: Request) -> SessionDto:
    client = request.client.host if request.client else "unknown"
    if not request.app.state.login_rate_limiter.allow(client):
        raise HTTPException(status_code=429, detail="Çok fazla giriş denemesi.")
    session = request.app.state.auth_service.authenticate(payload)
    if session is None:
        raise HTTPException(status_code=401, detail="E-posta veya şifre hatalı.")
    request.session["user"] = "admin"
    return session


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request) -> Response:
    request.session.clear()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/session", response_model=SessionDto)
async def session(request: Request) -> SessionDto:
    return request.app.state.auth_service.session()

