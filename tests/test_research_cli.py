from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.error import HTTPError

import pytest
from pydantic_ai.models.test import TestModel as PydanticTestModel

from company_bi.agent import research_company as run_research
from company_bi.cli import main
from company_bi.models import CompanyResearchRun


@pytest.mark.parametrize("nip", ["123", "5220003783"])
def test_research_rejects_invalid_nip_before_external_lookup(tmp_path: Path, nip: str) -> None:
    output = tmp_path / "research.json"
    assert main(["research", nip, "--output", str(output)]) == 2
    assert not output.exists()


@pytest.mark.parametrize(
    ("response", "code"),
    [
        ({"result": {"subject": None}}, "COMPANY_NOT_FOUND"),
        (
            HTTPError("https://wl-api.mf.gov.pl/", 503, "unavailable", None, None),
            "REGISTRY_HTTP_ERROR",
        ),
    ],
)
def test_research_does_not_create_a_draft_without_trusted_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mock_registry: Callable[[dict[str, dict[str, Any] | bytes | Exception]], None],
    capsys: pytest.CaptureFixture[str],
    response: dict[str, Any] | Exception,
    code: str,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "offline-fixture")
    monkeypatch.setenv("TAVILY_API_KEY", "offline-fixture")
    mock_registry({"1234563218": response})
    output = tmp_path / "research.json"
    assert main(["research", "1234563218", "--output", str(output)]) == 2
    assert not output.exists()
    assert capsys.readouterr().err.startswith(f"{code}:")


def test_missing_research_credentials_fail_before_registry_lookup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    output = tmp_path / "research.json"
    assert main(["research", "5220003782", "--output", str(output)]) == 2
    assert not output.exists()


def test_codex_cli_default_does_not_require_openai_api_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mock_registry: Callable[[dict[str, dict[str, Any] | bytes | Exception]], None],
    registry_subject: dict[str, Any],
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("COMPANY_BI_MODEL", raising=False)
    monkeypatch.setenv("TAVILY_API_KEY", "offline-fixture")
    mock_registry({"5220003782": registry_subject})

    async def offline_research(identity: Any, sources: Any, *, model: str) -> Any:
        unknown = {"state": "unknown", "reason": "No source established this fact"}
        output = {
            "business_description": unknown,
            "products_services": unknown,
            "industries": unknown,
            "markets": unknown,
            "employees": unknown,
            "financials": [
                {**unknown, "metric": "revenue"},
                {**unknown, "metric": "net_result"},
            ],
            "recent_developments": [],
            "limitations": ["No source established this fact"],
        }
        return await run_research(
            identity,
            sources,
            model=PydanticTestModel(call_tools=[], custom_output_args=output),
            max_seconds=10,
        )

    monkeypatch.setattr("company_bi.cli.research_company", offline_research)
    output_path = tmp_path / "research.json"

    assert main(["research", "5220003782", "--output", str(output_path)]) == 0
    run = CompanyResearchRun.model_validate_json(output_path.read_bytes())
    assert run.identity.nip == "5220003782"
    assert run.diagnostics.status == "completed"
    assert {fact.metric for fact in run.draft.financials} == {"revenue", "net_result"}
