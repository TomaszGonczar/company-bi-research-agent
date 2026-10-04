from __future__ import annotations

import json
import socket
from pathlib import Path
from typing import Any
from urllib.error import HTTPError

import pytest
from pydantic_ai.messages import ModelResponse, ToolCallPart
from pydantic_ai.models.function import FunctionModel

from company_bi.agent import research_company
from company_bi.cli import main

PAGE = (
    "Example Group sp. z o.o. reported standalone revenue of PLN 1.2 billion "
    "for 2025-01-01 to 2025-12-31."
)


def _draft() -> dict[str, Any]:
    unknown = {"state": "unknown", "reason": "No source established this fact"}
    return {
        "business_description": unknown,
        "products_services": unknown,
        "industries": unknown,
        "markets": unknown,
        "employees": unknown,
        "financials": [
            {
                "state": "supported",
                "metric": "revenue",
                "value": "1.2",
                "period": {"start": "2025-01-01", "end": "2025-12-31"},
                "currency": "PLN",
                "unit": "billions",
                "scope": "legal_entity",
                "evidence": [{"source_id": "S001", "excerpt": PAGE}],
            },
            {
                "state": "supported",
                "metric": "net_result",
                "value": "9.9",
                "period": {"start": "2025-01-01", "end": "2025-12-31"},
                "currency": "PLN",
                "unit": "billions",
                "scope": "legal_entity",
                "evidence": [{"source_id": "S001", "excerpt": PAGE}],
            },
        ],
        "recent_developments": [],
        "limitations": ["No source established this fact"],
    }


def _response(messages: Any, info: Any) -> ModelResponse:
    called_tools = {
        part.tool_name
        for message in messages
        for part in getattr(message, "parts", [])
        if isinstance(part, ToolCallPart)
    }
    if "search_web" not in called_tools:
        return ModelResponse(
            parts=[ToolCallPart("search_web", {"query": "Example Group annual report"}, "search")]
        )
    if "read_page" not in called_tools:
        return ModelResponse(parts=[ToolCallPart("read_page", {"source_id": "S001"}, "read")])
    return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, _draft(), "output")])


def test_cli_batch_uses_registry_research_gate_and_real_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mock_registry: Any,
    registry_subject: dict[str, Any],
) -> None:
    bad_nip = "5831014898"
    monkeypatch.setenv("TAVILY_API_KEY", "offline-fixture")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    def resolve_public(host: str, port: int, *args: Any, **kwargs: Any) -> list[Any]:
        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("93.184.216.34", port),
            )
        ]

    monkeypatch.setattr(socket, "getaddrinfo", resolve_public)

    async def search(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {
            "results": [
                {
                    "title": "Example Group annual report",
                    "url": "https://issuer.example/annual-report",
                    "content": "Discovery is not evidentiary full-page material",
                }
            ]
        }

    async def read_page(url: str, timeout: float) -> Any:
        from types import SimpleNamespace

        return SimpleNamespace(
            text=PAGE,
            url=url,
            published_on=None,
            title="Example Group annual report",
            redirect_chain=(),
        )

    monkeypatch.setattr("tavily.AsyncTavilyClient.search", search)
    monkeypatch.setattr("company_bi.fetch._static_read", read_page)

    registry_subject["result"]["subject"]["name"] = "Example Group sp. z o.o."

    mock_registry(
        {
            bad_nip: HTTPError("https://wl-api.mf.gov.pl/", 503, "unavailable", None, None),
            "5220003782": registry_subject,
        }
    )
    input_path = tmp_path / "nips.csv"
    input_path.write_text(f"nip\n{bad_nip}\n5220003782\n", encoding="utf-8")
    output_dir, runs_dir = tmp_path / "out", tmp_path / "runs"

    async def research(identity: Any, sources: Any, *, model: str) -> Any:
        return await research_company(identity, sources, model=FunctionModel(_response))

    monkeypatch.setattr("company_bi.batch.research_company", research)
    assert (
        main(
            [
                "batch",
                str(input_path),
                "--output-dir",
                str(output_dir),
                "--runs-dir",
                str(runs_dir),
            ]
        )
        == 1
    )

    results = json.loads((output_dir / "_batch_state.json").read_text(encoding="utf-8"))
    by_nip = {result["nip"]: result for result in results}
    assert by_nip[bad_nip]["error_code"] == "REGISTRY_HTTP_ERROR"
    assert by_nip["5220003782"]["status"] in {"complete", "partial"}
    report = json.loads((output_dir / "5220003782.json").read_text(encoding="utf-8"))
    revenue = next(fact for fact in report["financials"] if fact["metric"] == "revenue")
    net_result = next(fact for fact in report["financials"] if fact["metric"] == "net_result")
    assert report["identity"]["nip"] == "5220003782"
    assert revenue["state"] == "supported" and revenue["value"] == "1.2"
    assert net_result["state"] != "supported" and net_result["value"] is None
    full_page = next(source for source in report["sources"] if source["kind"] == "full_page")
    assert full_page["url"] == "https://issuer.example/annual-report"
    markdown = (output_dir / "5220003782.md").read_text(encoding="utf-8")
    assert "https://issuer.example/annual-report" in markdown
    assert "PLN 1.2 billion" in markdown
