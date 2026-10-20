"""Projeyi ``python3 main.py`` komutuyla başlatan giriş noktası."""

from __future__ import annotations

import os

import uvicorn
from dotenv import load_dotenv

from app.config import read_settings


def main() -> None:
    load_dotenv()
    settings = read_settings()
    uvicorn.run(
        "app.main:create_app",
        factory=True,
        host=os.getenv("HOST", "0.0.0.0"),
        port=settings.port,
        reload=settings.node_env == "development",
        proxy_headers=True,
    )


if __name__ == "__main__":
    main()

