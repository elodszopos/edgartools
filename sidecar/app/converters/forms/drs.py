"""edgar `DraftRegistrationStatement` (DRS / DRS/A) -> `DRSData`, explicit field-by-field.

The DRS metadata fields pass through the serialize coercers. `underlying_object` delegates to the
U53a/U54 converters by concrete type: a RegistrationS1 underlying -> registration_s1_data, a
RegistrationS3 underlying -> registration_s3_data, anything else (None) -> None. `company_name`
(a duplicate of company) and the `filing` back-reference are not mapped (they duplicate
envelope-level fields).
"""

from __future__ import annotations

from typing import Any

from edgar.offerings.drs import DraftRegistrationStatement
from edgar.offerings.registration_s1 import RegistrationS1
from edgar.offerings.registration_s3 import RegistrationS3

from app.converters.forms.registration_s1 import registration_s1_data
from app.converters.forms.registration_s3 import registration_s3_data
from app.models.forms.drs import DRSData, DRSUnderlying
from app.serialize import to_int, to_iso_str, to_str


def _underlying(obj: Any) -> DRSUnderlying | None:
    # edgar only constructs RegistrationS1 (S-1/F-1) or RegistrationS3 (S-3); else None
    if isinstance(obj, RegistrationS1):
        return registration_s1_data(obj)
    if isinstance(obj, RegistrationS3):
        return registration_s3_data(obj)
    return None


def drs_data(obj: DraftRegistrationStatement) -> DRSData:
    return DRSData(
        form=obj.form,
        company=to_str(obj.company),
        filing_date=to_iso_str(obj.filing_date),
        accession_number=to_str(obj.accession_number),
        underlying_form=to_str(obj.underlying_form) or "Unknown",
        is_amendment=bool(obj.is_amendment),
        amendment_number=to_int(obj.amendment_number),
        registration_number=to_str(obj.registration_number),
        underlying_object=_underlying(obj.underlying_object),
    )
