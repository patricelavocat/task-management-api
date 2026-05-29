# type: ignore
from app.models.task import Task
from app.repositories.base import BaseRepository


class _TaskRepository(BaseRepository[Task]):
    def __init__(self, model):
        super().__init__(model)


task_repository = _TaskRepository(model=Task)
