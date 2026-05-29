from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.db.session import SessionDep
from app.exceptions.app_exceptions import ObjNotFoundException
from app.models import Task
from app.repositories.task_repository import task_repository
from app.schemas.pagination import Page, Pagination
from app.schemas.task import TaskQuery, TaskRead, TaskCreate, TaskPatch
from app.services.authentication import get_current_user

router = APIRouter(prefix="/tasks", dependencies=[Depends(get_current_user)])


@router.get("")
async def list_tasks(
    db_session: SessionDep,
    pagination: Pagination = Depends(),
    query: TaskQuery = Depends(),
) -> Page[TaskRead]:
    filters = query.model_to_filters()
    results = await task_repository.list(
        db_session,
        skip=pagination.skip,
        limit=pagination.limit,
        filters=filters,
    )
    total = await task_repository.count(db_session, filters=filters)

    return Page(
        items=[TaskRead.model_validate(task) for task in results],
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get("/{task_id}")
async def get_task(
    db_session: SessionDep,
    task_id: UUID,
) -> TaskRead:
    result = await task_repository.get(db_session, str(task_id))
    if not result:
        raise ObjNotFoundException(Task)

    return TaskRead.model_validate(result)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_task(
    db_session: SessionDep,
    create_obj: TaskCreate,
) -> TaskRead:
    created = await task_repository.create(
        db_session,
        {
            **create_obj.model_dump(exclude_none=True),
            "created_author": "current_user",
        },
    )
    return TaskRead.model_validate(created)


@router.patch("/{task_id}")
async def update_task(
    db_session: SessionDep,
    task_id: UUID,
    patch_obj: TaskPatch,
) -> TaskRead:
    task = await task_repository.get(db_session, str(task_id))
    if not task:
        raise ObjNotFoundException(Task)

    updated = await task_repository.update(
        db_session,
        task,
        {
            **patch_obj.model_dump(exclude_unset=True),
            "modified_author": "current_user",
        },
    )
    return TaskRead.model_validate(updated)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    db_session: SessionDep,
    task_id: UUID,
) -> None:
    deleted = await task_repository.delete(db_session, str(task_id))
    if not deleted:
        raise ObjNotFoundException(Task)