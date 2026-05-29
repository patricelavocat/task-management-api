from datetime import datetime, timedelta, timezone
from typing import Annotated, Tuple

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.app_exceptions import (
    AuthenticationError,
)
from app.repositories.user_repository import user_repository  # type: ignore
from app.settings.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def authenticate_user(session: AsyncSession, email: str, password: str) -> bool:
    results = await user_repository.list(session, filters={"email": email})

    if not results:
        return False

    password_hash = PasswordHash.recommended()
    is_ok: bool = password_hash.verify(password, results[0].password)
    return is_ok


def create_token(data: dict, expires_delta_minutes: int) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return str(encoded_jwt)


def create_tokens(
    email: str, expires_access_delta_minutes: int, expires_refresh_delta_minutes: int
) -> Tuple[str, str]:
    access_token = create_token({"sub": email}, expires_access_delta_minutes)
    refresh_token = create_token({"sub": email, "type": "refresh"}, expires_refresh_delta_minutes)
    return access_token, refresh_token


def _validate_decoded_token(token: dict) -> str:
    email: str | None = token.get("sub")
    if email is None:
        raise AuthenticationError("Invalid token: missing subject")
    return email


def verify_access_token(token: dict) -> str:
    return _validate_decoded_token(token)


def verify_refresh_token(token: dict) -> str:
    token_type = token.get("type")
    if token_type != "refresh":  # noqa
        raise AuthenticationError("Invalid token: not a refresh token")
    return _validate_decoded_token(token)


def decode_token(token: str) -> dict:
    try:
        payload: dict = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except InvalidTokenError:
        raise AuthenticationError("Invalid or expired token")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> str:
    payload = decode_token(token)
    email = verify_access_token(payload)
    return email
