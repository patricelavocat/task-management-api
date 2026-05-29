from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models import BaseModel


class TaskStatus(StrEnum):
    INCOMPLETE = "incomplete"
    COMPLETE = "complete"
    ERROR = "error"


class Task(BaseModel):
    __tablename__ = "task"

    title: Mapped[str] = mapped_column(String(), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(), nullable=True)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(
            TaskStatus.INCOMPLETE,
            TaskStatus.COMPLETE,
            TaskStatus.ERROR,
            name="task_status_enum",
        ),
        nullable=False,
        default=TaskStatus.INCOMPLETE,
    )
