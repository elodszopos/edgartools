"""U58 wire model: EFFECT -> kind=effect.

An EFFECT filing is the SEC's notification that a registration statement (S-1, S-3, POS AM,
etc.) has been declared effective. The filing itself is tiny: the effective date, the filer
identity, the source registration's form type and accession number, and the SEC file number.
The `get_source_filing()` cross-entity resolver is NOT mapped (requires a Company lookup).
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.models.common import CIK_PATTERN, WireModel


class EffectData(WireModel):
    kind: Literal["effect"] = "effect"
    form: str | None
    cik: str | None = Field(pattern=CIK_PATTERN)
    submission_type: str | None
    is_live: bool
    schema_version: str | None
    effective_date: str | None
    entity: str | None
    source_submission_type: str | None
    source_accession_no: str | None
    source_file_number: str | None
