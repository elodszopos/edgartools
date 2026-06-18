"""CIK and entity-id helpers (wire: CIKs are 10-digit zero-padded strings)."""

from __future__ import annotations

MAX_CIK = 9_999_999_999


def pad_cik(cik: int | str) -> str:
    """Normalize a CIK to the wire format: 10-digit zero-padded string."""
    if isinstance(cik, bool):
        raise TypeError(f"invalid CIK type: {cik!r}")
    if isinstance(cik, int):
        numeric = cik
    elif isinstance(cik, str):
        stripped = cik.strip()
        if not (stripped.isascii() and stripped.isdigit()):
            raise ValueError(f"invalid CIK: {cik!r}")
        numeric = int(stripped)
    else:
        raise TypeError(f"invalid CIK type: {type(cik).__name__}")
    if not 0 < numeric <= MAX_CIK:
        raise ValueError(f"CIK out of range: {cik!r}")
    return f"{numeric:010d}"


def parse_entity_id(value: str) -> int | str:
    """Route param `id`: all-digits -> CIK as int, anything else -> ticker passed through."""
    stripped = value.strip()
    if not stripped:
        raise ValueError("empty entity id")
    if stripped.isascii() and stripped.isdigit():
        cik = int(stripped)
        if not 0 < cik <= MAX_CIK:
            raise ValueError(f"CIK out of range: {value!r}")
        return cik
    return stripped
