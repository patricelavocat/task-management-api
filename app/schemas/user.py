from datetime import datetime
from uuid import UUID

from pwdlib import PasswordHash
from pydantic import EmailStr, Field

from app.schemas.base import CamelModel


class UserRead(CamelModel):
    id: UUID
    email: EmailStr
    created_at: datetime


class UserCreate(CamelModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

    @property
    def hash_password(self) -> str:
        password_hash = PasswordHash.recommended()
        hashed: str = password_hash.hash(self.password)
        return hashed
