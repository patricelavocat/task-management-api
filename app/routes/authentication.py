from app.services.authentication import (
    authenticate_user,
    create_tokens,
    decode_token,
    verify_refresh_token,
)
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status
from starlette.requests import Request

from app.db.session import SessionDep
from app.exceptions.app_exceptions import AuthenticationError
from app.repositories.user_repository import user_repository
from app.schemas.token import Token, TokenRefreshRequest
from app.schemas.user import UserCreate, UserRead
from app.settings.config import settings

router = APIRouter(prefix="/auth")


@router.post("/login")
async def login(
        request: Request,
        db_session: SessionDep,
        form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    is_authenticated = await authenticate_user(db_session, form_data.username, form_data.password)
    if not is_authenticated:
        raise AuthenticationError("Wrong credentials")

    access_token, refresh_token = create_tokens(
        email=form_data.username,
        expires_access_delta_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        expires_refresh_delta_minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
    )
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")  # noqa


@router.post("/refresh")
async def refresh(request: Request, token_refresh_req: TokenRefreshRequest) -> Token:
    decoded_token = decode_token(token_refresh_req.refresh_token)
    username = verify_refresh_token(decoded_token)
    access_token, refresh_token = create_tokens(
        email=username,
        expires_access_delta_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        expires_refresh_delta_minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
    )
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")  # noqa


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
        db_session: SessionDep,
        create_user: UserCreate,
) -> UserRead:
    user = user_repository.create(db_session, {
        'email': create_user.email,
        'password_hash': create_user.hash_password,
    })
    return UserRead.model_validate(user)
