from fastapi import FastAPI

from app.routes import status


def add_app_routes(app: FastAPI) -> None:
    """Register routers to app."""
    app.include_router(status.router, tags=["Status"])
