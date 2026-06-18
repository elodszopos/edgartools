"""Typed `data` for the DRS draft registration statement (edgar `DraftRegistrationStatement`).

A DRS is a confidential draft registration (JOBS Act) that becomes public once the issuer proceeds.
EDGAR metadata only says "DRS"/"DRS/A"; the underlying form (S-1/F-1/S-3/S-4/20-F/Form 10/...) is
detected from the cover text. edgar builds a delegated `underlying_object` ONLY for S-1/F-1
(RegistrationS1) and S-3 (RegistrationS3); every other underlying form carries underlying_object=None.
So this model wraps the DRS metadata (underlying_form, amendment number, the 377- draft registration
number) around the embedded U53a/U54 payload, reusing those exact models as a nested discriminated
union on their own `kind`. Drafts predate the fee filing, so the embedded fee_table is typically None
or an empty shell. `company_name` (a duplicate of `company`) and the `filing` back-reference are
excluded; see the parity gate.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from app.models.common import WireModel
from app.models.forms.registration_s1 import RegistrationS1Data
from app.models.forms.registration_s3 import RegistrationS3Data

# the delegated registration payload edgar builds for an S-1/F-1 or S-3 draft (None for the other
# underlying forms); reuses the U53a/U54 models verbatim, discriminated on their own `kind`
DRSUnderlying = Annotated[RegistrationS1Data | RegistrationS3Data, Field(discriminator="kind")]


class DRSData(WireModel):
    """filing.obj() for a DRS / DRS/A -- the edgar DraftRegistrationStatement, full fidelity."""

    kind: Literal["drs"] = "drs"
    form: str  # "DRS" or "DRS/A"
    company: str | None
    filing_date: str | None
    accession_number: str | None
    underlying_form: str  # detected from cover text: "S-1"/"F-1"/"S-3"/"S-4"/"20-F"/"Form 10"/"Unknown"
    is_amendment: bool
    amendment_number: int | None  # "Amendment No. N" parsed from the cover; null when absent/unparsed
    registration_number: str | None  # the DRS draft registration number (377-XXXXXX prefix)
    underlying_object: DRSUnderlying | None  # embedded S-1/S-3 payload; null for S-4/20-F/Form 10/Unknown
