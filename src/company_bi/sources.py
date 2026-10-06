"""Host-owned research material and bounded operation accounting."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from pydantic import HttpUrl

from company_bi.models import (
    CompanyIdentity,
    OperationalFailure,
    RetrievedSource,
    SearchHit,
    Source,
    _normalized_source_url,
    validate_source_lineage,
)


@dataclass
class ResearchBudget:
    max_seconds: float = 180
    max_searches: int = 6
    max_page_reads: int = 10
    max_dynamic_reads: int = 2
    searches: int = 0
    page_reads: int = 0
    dynamic_reads: int = 0
    notes: list[str] = field(default_factory=list)
    started_at: float = field(default_factory=time.monotonic)
    failures: list[OperationalFailure] = field(default_factory=list)

    def remaining(self) -> float:
        return max(0.0, self.max_seconds - (time.monotonic() - self.started_at))

    def note(self, message: str) -> None:
        if message and message not in self.notes:
            self.notes.append(message)

    def consume(self, kind: Literal["search", "page", "dynamic"]) -> bool:
        if self.remaining() <= 0:
            self.record_failure(
                OperationalFailure(
                    code="RESOURCE_LIMIT",
                    stage="resource_limit",
                    reason="Research deadline reached",
                )
            )
            return False
        attr, maximum = {
            "search": ("searches", self.max_searches),
            "page": ("page_reads", self.max_page_reads),
            "dynamic": ("dynamic_reads", self.max_dynamic_reads),
        }[kind]
        if getattr(self, attr) >= maximum:
            self.record_failure(
                OperationalFailure(
                    code="RESOURCE_LIMIT",
                    stage="resource_limit",
                    reason=f"Research {kind} budget exhausted",
                )
            )
            return False
        setattr(self, attr, getattr(self, attr) + 1)
        return True

    def record_failure(self, failure: OperationalFailure) -> None:
        self.failures.append(failure)
        self.note(failure.reason)


class SourceStore:
    """Run-local stable host source IDs with separately retained discovery materials."""

    def __init__(self, identity: CompanyIdentity, registry_sources: list[Source]) -> None:
        self._by_url: dict[str, str] = {}
        self._sources: dict[str, Source] = {}
        self._pages: dict[str, RetrievedSource] = {}
        self._snippets: list[RetrievedSource] = []
        self._registry: list[RetrievedSource] = []
        self._next_id = 1
        for source in registry_sources:
            if source.publication_blocked_reason is not None:
                raise ValueError("SourceStore cannot write publication-blocked registry material")
            fields: list[str] = []
            for name in (
                "legal_name",
                "krs",
                "regon",
                "registered_city",
                "registered_address",
                "website",
            ):
                fact = getattr(identity, name)
                if fact.state == "supported":
                    fields.append(f"{name}: {fact.value}")
                elif fact.state == "uncertain":
                    fields.append(f"{name}: uncertain; {fact.reason}")
                elif fact.reason:
                    fields.append(f"{name}: unknown; {fact.reason}")
                fields.extend(
                    f"{name} evidence from {ref.source_id}: {ref.excerpt}" for ref in fact.evidence
                )
            fields.append(f"NIP: {identity.nip}")
            self._registry.append(
                RetrievedSource(
                    source=source,
                    kind="registry",
                    content="MF VAT register identity material (not a raw registry response):\n"
                    + "\n".join(fields),
                    fetch_mode="registry",
                )
            )

    def _source_for(self, title: str, url: HttpUrl, retrieved_at: datetime) -> Source:
        normalized = _normalized_source_url(url)
        source_id = self._by_url.get(normalized)
        if source_id is None:
            source_id = f"S{self._next_id:03d}"
            self._next_id += 1
            self._by_url[normalized] = source_id
            self._sources[source_id] = Source(
                source_id=source_id, url=url, title=title, retrieved_at=retrieved_at
            )
        return self._sources[source_id]

    def add_search(
        self,
        *,
        title: str,
        url: HttpUrl,
        content: str,
        score: float | None,
        retrieved_at: datetime,
    ) -> SearchHit:
        source = self._source_for(title, url, retrieved_at)
        hit_source = source.model_copy(update={"title": title, "retrieved_at": retrieved_at})
        hit = SearchHit(
            source_id=source.source_id, title=title, url=url, content=content, score=score
        )
        self._snippets.append(
            RetrievedSource(
                source=hit_source, kind="search_snippet", content=content, fetch_mode="tavily"
            )
        )
        return hit

    def get(self, source_id: str) -> RetrievedSource | None:
        if source_id in self._pages:
            return self._pages[source_id]
        for material in reversed(self._snippets):
            if material.source.source_id == source_id:
                return material
        return next((item for item in self._registry if item.source.source_id == source_id), None)

    def store_page(self, material: RetrievedSource) -> None:
        source_id = material.source.source_id
        if material.source.publication_blocked_reason is not None:
            raise ValueError("SourceStore cannot write publication-blocked material")
        if source_id not in self._sources:
            raise ValueError("Cannot store a page for an unknown source ID")
        if material.kind != "full_page":
            raise ValueError("Stored page material must have kind='full_page'")
        validate_source_lineage(
            [
                *self._snippets,
                *(page for page in self._pages.values() if page.source.source_id != source_id),
                material,
            ]
        )
        self._pages[source_id] = material

    def known_ids(self) -> set[str]:
        return set(self._sources) | {item.source.source_id for item in self._registry}

    def snapshots(self) -> list[RetrievedSource]:
        return [*self._registry, *self._snippets, *self._pages.values()]
