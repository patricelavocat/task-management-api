import uuid
from datetime import datetime, timedelta, timezone

import pytest
from app.models.task import TaskStatus
from app.repositories.task_repository import task_repository


@pytest.mark.asyncio
class TestCreateTask:
    async def test_ok(self, db_session):
        due_date = datetime.now(timezone.utc)
        task = {
            "title": "title",
            "description": "description",
            "due_date": due_date,
            "status": TaskStatus.INCOMPLETE,
            "created_author": "author",
        }
        created_obj = await task_repository.create(db_session, task)
        assert created_obj.id
        assert created_obj.title == "title"
        assert created_obj.description == "description"
        assert created_obj.due_date == due_date
        assert created_obj.created_author == "author"
        assert created_obj.created_at

    async def test_invalid_key(self, db_session):
        task = {
            "wrong": "aName",
        }
        with pytest.raises(TypeError) as err:
            await task_repository.create(db_session, task)
        assert str(err.value) == "'wrong' is an invalid keyword argument for Task"

    async def test_already_present(self, db_session, task_factory):
        existent_task = await task_factory()
        task = {
            "title": existent_task.title,
            "description": "description",
            "due_date": datetime.now(timezone.utc),
            "created_author": "author",
        }
        with pytest.raises(Exception) as err:
            await task_repository.create(db_session, task)
        assert 'duplicate key value violates unique constraint "task_title_key"' in str(err.value)


@pytest.mark.asyncio
class TestGetTask:
    async def test_ok(self, db_session, task_factory) -> None:
        existent_task = await task_factory()
        get_task = await task_repository.get(db_session, existent_task.id)
        assert get_task == existent_task

    async def test_ko_non_existent(self, db_session, task_factory) -> None:
        _ = await task_factory()
        get_task = await task_repository.get(db_session, uuid.uuid4())
        assert not get_task


@pytest.mark.asyncio
class TestListTask:
    async def test_ok_all(self, db_session, task_factory) -> None:
        for _ in range(10):
            _ = await task_factory(title=str(uuid.uuid4()))
        all_tasks = await task_repository.list(db_session)
        assert len(all_tasks) == 10

    async def test_ok_with_filters(self, db_session, task_factory) -> None:
        existent_task_1 = await task_factory(title="title_1")
        _ = await task_factory(title=str(uuid.uuid4()))
        _ = await task_factory(title=str(uuid.uuid4()))
        all_tasks = await task_repository.list(db_session, filters={"title": "title_1"})
        assert all_tasks == [existent_task_1]

    async def test_ok_no_results(self, db_session, task_factory) -> None:
        _ = await task_factory(title="title_1")
        _ = await task_factory(title=str(uuid.uuid4()))
        _ = await task_factory(title=str(uuid.uuid4()))
        all_tasks = await task_repository.list(db_session, filters={"title": "other"})
        assert all_tasks == []

    async def test_ok_skip_limit(self, db_session, task_factory) -> None:
        task_1 = await task_factory(title="title_1")
        task_2 = await task_factory(title=str(uuid.uuid4()))
        task_3 = await task_factory(title=str(uuid.uuid4()))
        all_tasks = await task_repository.list(db_session, skip=0, limit=1)
        assert all_tasks == [task_1]
        all_tasks = await task_repository.list(db_session, skip=1, limit=1)
        assert all_tasks == [task_2]
        all_tasks = await task_repository.list(db_session, skip=2, limit=1)
        assert all_tasks == [task_3]


@pytest.mark.asyncio
class TestDeleteTask:
    async def test_ok(self, db_session, task_factory) -> None:
        existent_task = await task_factory()
        deleted = await task_repository.delete(db_session, existent_task.id)
        assert deleted

    async def test_ko_non_existent(self, db_session) -> None:
        deleted = await task_repository.delete(db_session, uuid.uuid4())
        assert not deleted


@pytest.mark.asyncio
class TestUpdateTask:
    async def test_ok(self, db_session, task_factory):
        old_due_date = datetime.now(timezone.utc)
        existent_task = await task_factory(
            title="old_title",
            description="old_description",
            due_date=old_due_date,
            status=TaskStatus.INCOMPLETE,
        )
        assert existent_task.title == "old_title"
        assert existent_task.description == "old_description"
        assert existent_task.due_date == old_due_date
        assert existent_task.status == TaskStatus.INCOMPLETE

        new_title = "new_title"
        new_description = "new_description"
        new_due_date = old_due_date + timedelta(days=1)
        new_status = TaskStatus.COMPLETE

        task = {
            "title": new_title,
            "description": new_description,
            "due_date": new_due_date,
            "status": new_status,
            "modified_author": "author",
        }
        updated_obj = await task_repository.update(db_session, existent_task, task)
        assert updated_obj.id
        assert updated_obj.title == new_title
        assert updated_obj.description == new_description
        assert updated_obj.due_date == new_due_date
        assert updated_obj.status == new_status
        assert updated_obj.created_author == "author"
        assert updated_obj.created_at
        assert updated_obj.modified_author == "author"
        assert updated_obj.modified_at

    async def test_already_present(self, db_session, task_factory):
        existent_task_1 = await task_factory(title="title_1")
        existent_task_2 = await task_factory(title="title_2")
        task = {
            "title": existent_task_1.title,
        }
        with pytest.raises(Exception) as err:
            await task_repository.update(db_session, existent_task_2, task)
        assert 'duplicate key value violates unique constraint "task_title_key"' in str(err.value)
