# pylint: disable=unused-argument
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from app.models.task import TaskStatus

TASK_KEYS = {
    "id",
    "title",
    "description",
    "dueDate",
    "status",
    "createdAuthor",
    "modifiedAuthor",
    "createdAt",
    "modifiedAt",
}
PAGE_KEYS = {"items", "total", "skip", "limit"}


@pytest.mark.asyncio
class TestListTasks:
    url = "tasks"

    async def test_ok_empty(self, client) -> None:
        resp = await client.get(self.url)
        assert resp.status_code == 200
        body = resp.json()
        assert body.keys() == PAGE_KEYS
        assert body == {"items": [], "total": 0, "skip": 0, "limit": 1000}

    async def test_ok_all(self, client, task_factory) -> None:
        for _ in range(10):
            await task_factory(title=str(uuid.uuid4()))

        resp = await client.get(self.url)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 10
        assert len(body["items"]) == 10
        assert body["items"][0].keys() == TASK_KEYS

    async def test_ok_skip_limit(self, client, task_factory) -> None:
        for _ in range(5):
            await task_factory(title=str(uuid.uuid4()))

        resp = await client.get(self.url, params={"skip": 2, "limit": 2})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 5  # total ignores pagination
        assert len(body["items"]) == 2
        assert body["skip"] == 2
        assert body["limit"] == 2

    async def test_ok_filter_title(self, client, task_factory) -> None:
        await task_factory(title="wanted")
        await task_factory(title=str(uuid.uuid4()))
        await task_factory(title=str(uuid.uuid4()))

        resp = await client.get(self.url, params={"title": "wanted"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert [item["title"] for item in body["items"]] == ["wanted"]

    async def test_ok_filter_title_multiple(self, client, task_factory) -> None:
        await task_factory(title="a")
        await task_factory(title="b")
        await task_factory(title="c")

        resp = await client.get(self.url, params={"title": ["a", "b"]})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        assert {item["title"] for item in body["items"]} == {"a", "b"}

    async def test_ok_filter_status(self, client, task_factory) -> None:
        await task_factory(title=str(uuid.uuid4()), status=TaskStatus.COMPLETE)
        await task_factory(title=str(uuid.uuid4()), status=TaskStatus.INCOMPLETE)
        await task_factory(title=str(uuid.uuid4()), status=TaskStatus.INCOMPLETE)

        resp = await client.get(self.url, params={"status": TaskStatus.INCOMPLETE.value})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        assert all(item["status"] == TaskStatus.INCOMPLETE.value for item in body["items"])

    async def test_ok_filter_due_range(self, client, task_factory) -> None:
        now = datetime.now(timezone.utc)
        await task_factory(title="past", due_date=now - timedelta(days=5))
        await task_factory(title="present", due_date=now)
        await task_factory(title="future", due_date=now + timedelta(days=5))

        resp = await client.get(
            self.url,
            params={
                "due_after": (now - timedelta(days=1)).isoformat(),
                "due_before": (now + timedelta(days=1)).isoformat(),
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert [item["title"] for item in body["items"]] == ["present"]


@pytest.mark.asyncio
class TestGetTask:
    url = "tasks"

    async def test_ok(self, client, task_factory) -> None:
        task = await task_factory()

        resp = await client.get(f"{self.url}/{task.id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body.keys() == TASK_KEYS
        assert body["id"] == str(task.id)
        assert body["title"] == task.title
        assert body["createdAuthor"] == task.created_author

    async def test_ko_not_found(self, client) -> None:
        resp = await client.get(f"{self.url}/{uuid.uuid4()}")
        assert resp.status_code == 404
        assert resp.json() == {"error": "Object not found"}

    async def test_ko_invalid_uuid(self, client) -> None:
        resp = await client.get(f"{self.url}/not-a-uuid")
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestCreateTask:
    url = "tasks"

    async def test_ok(self, client) -> None:
        due_date = datetime.now(timezone.utc)
        payload = {
            "title": "new task",
            "description": "a description",
            "dueDate": due_date.isoformat(),
        }
        resp = await client.post(self.url, json=payload)
        assert resp.status_code == 201
        body = resp.json()
        assert body.keys() == TASK_KEYS
        assert body["id"]
        assert body["title"] == "new task"
        assert body["description"] == "a description"
        assert body["status"] == TaskStatus.INCOMPLETE.value
        assert body["createdAuthor"] == "current_user"
        assert body["createdAt"]

    async def test_ok_without_description(self, client) -> None:
        payload = {
            "title": "no description",
            "dueDate": datetime.now(timezone.utc).isoformat(),
        }
        resp = await client.post(self.url, json=payload)
        assert resp.status_code == 201
        assert resp.json()["description"] is None

    async def test_ko_missing_required(self, client) -> None:
        resp = await client.post(self.url, json={"description": "no title"})
        assert resp.status_code == 422

    async def test_ko_extra_field(self, client) -> None:
        payload = {
            "title": "with extra",
            "dueDate": datetime.now(timezone.utc).isoformat(),
            "unexpected": "value",
        }
        resp = await client.post(self.url, json=payload)
        assert resp.status_code == 422

    async def test_ko_duplicate_title(self, client, task_factory) -> None:
        existing = await task_factory(title="dup")
        payload = {
            "title": existing.title,
            "dueDate": datetime.now(timezone.utc).isoformat(),
        }
        resp = await client.post(self.url, json=payload)
        assert resp.status_code == 400


@pytest.mark.asyncio
class TestUpdateTask:
    url = "tasks"

    async def test_ok_full(self, client, task_factory) -> None:
        task = await task_factory(
            title="old",
            description="old desc",
            status=TaskStatus.INCOMPLETE,
        )
        payload = {
            "title": "updated",
            "description": "updated desc",
            "status": TaskStatus.COMPLETE.value,
        }
        resp = await client.patch(f"{self.url}/{task.id}", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["title"] == "updated"
        assert body["description"] == "updated desc"
        assert body["status"] == TaskStatus.COMPLETE.value
        assert body["modifiedAuthor"] == "current_user"
        assert body["modifiedAt"]

    async def test_ok_partial(self, client, task_factory) -> None:
        task = await task_factory(title="keep", description="keep desc")
        resp = await client.patch(f"{self.url}/{task.id}", json={"title": "renamed"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["title"] == "renamed"
        assert body["description"] == "keep desc"  # untouched

    async def test_ko_not_found(self, client) -> None:
        resp = await client.patch(f"{self.url}/{uuid.uuid4()}", json={"title": "x"})
        assert resp.status_code == 404
        assert resp.json() == {"error": "Object not found"}

    async def test_ko_extra_field(self, client, task_factory) -> None:
        task = await task_factory()
        resp = await client.patch(f"{self.url}/{task.id}", json={"unexpected": "value"})
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestDeleteTask:
    url = "tasks"

    async def test_ok(self, client, task_factory) -> None:
        task = await task_factory()
        resp = await client.delete(f"{self.url}/{task.id}")
        assert resp.status_code == 204
        assert not resp.content

        # confirm it is gone
        get_resp = await client.get(f"{self.url}/{task.id}")
        assert get_resp.status_code == 404

    async def test_ko_not_found(self, client) -> None:
        resp = await client.delete(f"{self.url}/{uuid.uuid4()}")
        assert resp.status_code == 404
        assert resp.json() == {"error": "Object not found"}
