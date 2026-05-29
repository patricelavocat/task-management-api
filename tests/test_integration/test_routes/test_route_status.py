# pylint: disable=unused-argument
import pytest
from app.db.info import DB_AVAILABLE, DB_NOT_CONNECTED


@pytest.mark.asyncio
class TestRouterStatus:
    url = "status"
    response_keys = {"database", "startDate", "version"}

    async def test_ok(self, client, mocker) -> None:
        mocker.patch("app.db.info._is_available", return_value=DB_AVAILABLE)
        mocker.patch("app.db.info._migration_version", return_value="0001")
        resp = await client.get(self.url)
        assert resp.status_code == 200
        assert resp.json().keys() == self.response_keys
        assert resp.json()["database"].keys() == {"dbVersion", "status"}
        assert resp.json()["database"] == {
            "dbVersion": "0001",
            "status": DB_AVAILABLE,
        }

    async def test_error(self, client, mocker) -> None:
        mocker.patch("app.db.info._is_available", return_value=DB_NOT_CONNECTED)
        mocker.patch("app.db.info._migration_version", return_value="XXXX")

        resp = await client.get(self.url)
        assert resp.status_code == 500
        assert resp.json().keys() == self.response_keys
        assert resp.json()["database"] == {
            "dbVersion": "XXXX",
            "status": DB_NOT_CONNECTED,
        }
