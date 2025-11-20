"""Application entrypoint."""

from __future__ import annotations

import os

import uvicorn
from fastapi import FastAPI, Request

from .routes import router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(title="ff-backend", version="0.1.0")
    application.include_router(router)

    @application.middleware("http")
    async def log_recommend_payload(request: Request, call_next):  # noqa: D401
        """Log request body for /recommend endpoints to debug 422s."""
        if request.url.path.startswith("/recommend"):
            body = await request.body()
            print(f"[REQUEST] {request.method} {request.url.path} body={body.decode(errors='ignore')}")
        response = await call_next(request)
        return response

    return application


app = create_app()


def run() -> None:
    """Run the uvicorn development server."""
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=True,
        factory=False,
    )


if __name__ == "__main__":
    run()
