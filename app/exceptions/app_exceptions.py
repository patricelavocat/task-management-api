from typing import Generic

from app.repositories.base import ModelType  # type: ignore


class ObjNotFoundException(Exception):
    def __init__(self, model_type: Generic[ModelType]) -> None:  # type: ignore
        super().__init__("Object Not Found: %s" % model_type)


class AuthenticationError(Exception):
    def __init__(self, msg: str) -> None:
        super().__init__("Authentication error: %s" % msg)
