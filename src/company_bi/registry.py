"""One MF VAT-register lookup: authoritative fields, no name search or inference."""

import json
from datetime import UTC, date, datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import BaseModel, Field, HttpUrl, StrictStr, ValidationError

from company_bi.models import NIP, CompanyIdentity, EvidenceRef, Fact, Source
from company_bi.nip import validate_nip

_API = "https://wl-api.mf.gov.pl/api/search/nip"
_TIMEOUT_SECONDS = 10


class RegistryLookupError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class _Subject(BaseModel):
    name: StrictStr
    nip: NIP
    regon: StrictStr | None = None
    krs: StrictStr | None = None
    working_address: StrictStr | None = Field(default=None, alias="workingAddress")


class _Result(BaseModel):
    subject: _Subject | None


class _Response(BaseModel):
    result: _Result


def _field_fact(value: str | None, source_id: str, missing_reason: str) -> Fact[str]:
    if value is None or not value.strip():
        return Fact[str](state="unknown", reason=missing_reason)
    return Fact[str](
        state="supported",
        value=value,
        evidence=[EvidenceRef(source_id=source_id, excerpt=json.dumps(value, ensure_ascii=False))],
    )


def lookup_company(nip: str, as_of: date) -> tuple[CompanyIdentity | None, Source]:
    nip = validate_nip(nip)
    url = f"{_API}/{nip}?date={as_of.isoformat()}"
    request = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            body = response.read()
    except HTTPError as error:
        raise RegistryLookupError(
            "REGISTRY_HTTP_ERROR", f"MF registry returned HTTP {error.code}"
        ) from error
    except (URLError, TimeoutError, OSError) as error:
        raise RegistryLookupError(
            "REGISTRY_NETWORK_ERROR", "MF registry request failed due to a network or timeout error"
        ) from error
    retrieved_at = datetime.now(UTC)
    try:
        result = _Response.model_validate_json(body).result
    except ValidationError as error:
        raise RegistryLookupError(
            "REGISTRY_INVALID_RESPONSE", "MF registry returned invalid JSON or identity structure"
        ) from error
    source = Source(
        source_id=f"mf-vat-{nip}-{retrieved_at.strftime('%Y%m%dT%H%M%S%fZ')}",
        url=HttpUrl(url),
        title="Ministerstwo Finansów — Wykaz podatników VAT",
        retrieved_at=retrieved_at,
    )
    subject = result.subject
    if subject is None:
        return None, source
    if subject.nip != nip:
        raise RegistryLookupError(
            "REGISTRY_IDENTITY_MISMATCH",
            "MF registry returned a different NIP; no identity selected",
        )
    try:
        identity = CompanyIdentity(
            nip=subject.nip,
            legal_name=_field_fact(
                subject.name, source.source_id, "Registry did not provide a legal name"
            ),
            krs=_field_fact(subject.krs, source.source_id, "Registry did not provide KRS"),
            regon=_field_fact(subject.regon, source.source_id, "Registry did not provide REGON"),
            registered_address=_field_fact(
                subject.working_address,
                source.source_id,
                "Registry did not provide a registration address",
            ),
            registered_city=Fact[str](
                state="unknown",
                reason="Registry provides no separate city field; no city inferred from address",
            ),
            website=Fact[HttpUrl](
                state="unknown",
                reason="This registry supplies no website; no website verification performed",
            ),
            resolved_at=datetime.now(UTC),
        )
    except ValidationError as error:
        raise RegistryLookupError(
            "REGISTRY_INVALID_RESPONSE", "MF registry returned invalid legal identity fields"
        ) from error
    return identity, source
