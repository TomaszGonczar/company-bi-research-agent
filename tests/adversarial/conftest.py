"""Synthetic, offline publication inputs independent of the frozen replay gold."""

import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from company_bi.evidence import build_profile
from company_bi.models import CompanyResearchRun
from company_bi.renderer import render_json, render_markdown


@pytest.fixture
def make_run() -> Callable[..., CompanyResearchRun]:
    def factory(
        content: str,
        *,
        identity_name: str = "Example sp. z o.o.",
        **draft_changes: Any,
    ) -> CompanyResearchRun:
        unknown = {"state": "unknown", "reason": "Not established in this synthetic case"}
        registry_ref = {"source_id": "registry", "excerpt": f'"{identity_name}"'}
        timestamp = datetime(2026, 10, 3, 12, tzinfo=UTC)
        draft = {
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
            "limitations": ["Synthetic adversarial case, not a real-company report"],
        }
        draft.update(draft_changes)
        return CompanyResearchRun.model_validate(
            {
                "identity": {
                    "nip": "1234563218",
                    "legal_name": {
                        "state": "supported",
                        "value": identity_name,
                        "evidence": [registry_ref],
                    },
                    **{
                        field: unknown
                        for field in (
                            "krs",
                            "regon",
                            "registered_city",
                            "registered_address",
                            "website",
                        )
                    },
                    "resolved_at": timestamp,
                },
                "draft": draft,
                "sources": [
                    {
                        "source": {
                            "source_id": source_id,
                            "url": f"https://{source_id}.example/",
                            "title": title,
                            "retrieved_at": timestamp,
                        },
                        "kind": kind,
                        "content": body,
                        "fetch_mode": mode,
                    }
                    for source_id, title, kind, body, mode in (
                        (
                            "registry",
                            "Synthetic registry",
                            "registry",
                            registry_ref["excerpt"],
                            "registry",
                        ),
                        ("page", "Synthetic company page", "full_page", content, "static"),
                    )
                ],
                "diagnostics": {
                    "model": "offline-adversarial-fixture",
                    "status": "completed",
                    "model_requests": 0,
                    "searches": 0,
                    "page_reads": 0,
                    "dynamic_reads": 0,
                    "output_retries": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "duration_seconds": 0,
                },
                "generated_at": timestamp,
            }
        )

    return factory


@pytest.fixture
def publish(tmp_path: Path) -> Callable[[CompanyResearchRun], dict[str, Any]]:
    def publication(run: CompanyResearchRun) -> dict[str, Any]:
        validated = CompanyResearchRun.model_validate_json(run.model_dump_json())
        profile = build_profile(validated)
        rendered = render_json(profile)
        (tmp_path / "profile.json").write_text(rendered, encoding="utf-8")
        (tmp_path / "profile.md").write_text(render_markdown(profile), encoding="utf-8")
        return json.loads(rendered)

    return publication
