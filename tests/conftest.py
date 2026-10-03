import json
import socket
from collections.abc import Callable
from io import BytesIO
from typing import Any
from urllib.parse import urlsplit
from urllib.request import Request

import pytest


@pytest.fixture(autouse=True)
def block_live_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked(*args: object, **kwargs: object) -> None:
        raise AssertionError(
            "Tests must supply a controlled registry response; live HTTP is disabled"
        )

    monkeypatch.setattr("company_bi.registry.urlopen", blocked)


@pytest.fixture(autouse=True)
def block_live_sockets(monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked(*args: object, **kwargs: object) -> None:
        raise AssertionError(
            "Tests must use controlled network transports; live sockets are disabled"
        )

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)


@pytest.fixture(autouse=True)
def block_live_research(monkeypatch: pytest.MonkeyPatch) -> None:
    async def blocked(*args: object, **kwargs: object) -> None:
        raise AssertionError("Tests must provide controlled research responses; live HTTP disabled")

    monkeypatch.setattr("pydantic_ai.models.ALLOW_MODEL_REQUESTS", False)
    monkeypatch.setattr("tavily.AsyncTavilyClient.search", blocked)
    monkeypatch.setattr("scrapling.fetchers.AsyncFetcher.get", blocked)
    monkeypatch.setattr("scrapling.fetchers.DynamicFetcher.async_fetch", blocked)


@pytest.fixture
def registry_subject() -> dict[str, Any]:
    return {
        "result": {
            "subject": {
                "name": '"ASSECO POLAND" SPÓŁKA AKCYJNA',
                "nip": "5220003782",
                "regon": "010334578",
                "krs": "0000033391",
                "workingAddress": "OLCHOWA 14, 35-322 RZESZÓW",
            }
        }
    }


@pytest.fixture
def mock_registry(
    monkeypatch: pytest.MonkeyPatch,
) -> Callable[[dict[str, dict[str, Any] | bytes | Exception]], None]:
    def install(responses: dict[str, dict[str, Any] | bytes | Exception]) -> None:
        def controlled(request: Request, timeout: float) -> BytesIO:
            nip = urlsplit(request.full_url).path.rsplit("/", 1)[-1]
            response = responses[nip]
            if isinstance(response, Exception):
                raise response
            body = response if isinstance(response, bytes) else json.dumps(response).encode("utf-8")
            return BytesIO(body)

        monkeypatch.setattr("company_bi.registry.urlopen", controlled)

    return install
