from app.models.user import User
from app.repositories.base import BaseRepository


class _UserRepository(BaseRepository[User]):
    def __init__(self, model):
        super().__init__(model)

user_repository = _UserRepository(model=User)