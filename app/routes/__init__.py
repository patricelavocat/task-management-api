from fastapi import FastAPI

from app.routes import authentication, status, task


def add_app_routes(app: FastAPI) -> None:
    """Register routers to app."""
    app.include_router(authentication.router, tags=["Authentication"])
    app.include_router(status.router, tags=["Status"])
    app.include_router(task.router, tags=["Tasks"])
