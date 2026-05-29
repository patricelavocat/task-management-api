from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.settings.config import settings
from app.routes import add_app_routes
from app.routes.errors_handler import add_all_errors_handlers

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
)

add_app_routes(app)
add_all_errors_handlers(app)

Instrumentator().instrument(app).expose(app)
