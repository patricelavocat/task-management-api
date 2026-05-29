import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

env_path = os.environ.get("ENV_PATH", ".env.test")
load_dotenv(dotenv_path=Path(__file__).parent / env_path)


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


class _AnyExceptNone:
    "A helper object that compares equal to everything except for None."

    def __eq__(self, other):
        return other is not None


NOT_NONE = _AnyExceptNone()
