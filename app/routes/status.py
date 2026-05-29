from fastapi import APIRouter, Depends, Response
from starlette import status

from app.settings.config import settings
from app.schemas.status import Status
from app.db.info import DB_AVAILABLE, database_info
from app.db.session import SessionDep

router = APIRouter()


@router.get("/status")
async def get_status(
    response: Response,
    db_session: SessionDep,
) -> Status:
    """Return the status of the API."""
    db_info = await database_info(db_session)

    if db_info.status != DB_AVAILABLE:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return Status(
        version=settings.VERSION,
        start_date=settings.START_API_DATE,
        database=db_info,
    )
