import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.schemas.status import DbInformation

logger = logging.getLogger(__name__)

DB_AVAILABLE = "AVAILABLE"
DB_NOT_CONNECTED = "NOT CONNECTED"


async def database_info(db_session: AsyncSession) -> DbInformation:
    """Summarize database information.
    Returns:
        DbInformation: The status of the database and its version
    """
    return DbInformation(
        status=await _is_available(db_session),
        db_version=await _migration_version(db_session),
    )


async def _migration_version(db_session: AsyncSession) -> str:
    """Check the actual alembic revision.
    Returns:
        str: The actual version stored in database (XXXX if error)
    """
    try:
        result = await db_session.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
        migration_version = result.scalar()
        return str(migration_version)  # type: ignore[index]
    except SQLAlchemyError as err:
        logger.error(err.args)
        return "XXXX"


async def _is_available(db_session: AsyncSession) -> str:
    """Check if a database is available or not
    Returns:
        str: the status of the database
    """
    try:
        await db_session.execute(text("SELECT 1"))
        return DB_AVAILABLE
    except SQLAlchemyError as err:
        logger.error(err.args)
        return DB_NOT_CONNECTED
