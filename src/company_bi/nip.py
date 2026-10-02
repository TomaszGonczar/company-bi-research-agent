"""Normalize permitted NIP formatting; never infer or repair an identifier."""

import re

_WEIGHTS = (6, 5, 7, 2, 3, 4, 5, 6, 7)


class InvalidNIP(ValueError):
    """The input does not contain a checksum-valid Polish NIP."""


def validate_nip(value: object) -> str:
    """Accept text or an exact Excel integer; return ten ASCII digits."""
    if value is None:
        raise InvalidNIP("NIP is required")
    if isinstance(value, str):
        text = value.strip()
    elif isinstance(value, int) and not isinstance(value, bool):
        text = str(value)
    else:
        raise InvalidNIP(
            "NIP must be text or an exact integer cell; formulas/floats are not inferred"
        )
    if text[:2].upper() == "PL":
        text = text[2:]
    nip = re.sub(r"[\s-]", "", text)
    if not nip:
        raise InvalidNIP("NIP is required")
    if re.fullmatch(r"[0-9]+", nip) is None:
        raise InvalidNIP(
            "NIP must contain only ASCII digits after removing PL, whitespace and hyphens"
        )
    if len(nip) != 10:
        raise InvalidNIP("NIP must contain exactly 10 digits")
    checksum = (
        sum(int(digit) * weight for digit, weight in zip(nip[:9], _WEIGHTS, strict=True)) % 11
    )
    if checksum == 10 or checksum != int(nip[-1]):
        raise InvalidNIP("Invalid Polish NIP checksum")
    return nip
