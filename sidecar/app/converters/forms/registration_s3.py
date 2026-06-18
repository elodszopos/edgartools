"""edgar `RegistrationS3` (S-3 / F-3 shelf family) -> `RegistrationS3Data`, explicit field-by-field.

Cover-page bools pass through directly (pydantic already typed them bool|None); strings pass through
`to_str`. The fee table delegates to the shared `offering.py` converter (the same RegistrationFeeTable
the S-1 uses). `offering_type` is the edgar S3OfferingType enum's `.value`; `is_auto_shelf` is edgar's
derived auto-shelf flag (S-3ASR / fee-deferred). Convenience scalars (registration_number, ein,
state_of_incorporation, total_offering, net_fee, fee_deferred, securities) map from the edgar object
directly. Cross-entity lifecycle properties (takedowns, related_filings) are set to None -- they
require cross-filing SEC fetches served at separate endpoints.
"""

from __future__ import annotations

from typing import Any

from edgar.offerings.registration_s3 import RegistrationS3

from app.converters.forms.offering import _fee_security, fee_table
from app.models.forms.registration_s3 import RegistrationS3Data, S3CoverPage
from app.serialize import to_date, to_float, to_str


def _date_str(value: Any) -> str | None:
    if isinstance(value, str):
        return to_str(value)
    parsed = to_date(value)
    return parsed.isoformat() if parsed is not None else None


def _cover_page(cp: Any) -> S3CoverPage:
    return S3CoverPage(
        company_name=to_str(cp.company_name) or "",  # edgar requires it; never blank in practice
        registration_number=to_str(cp.registration_number),
        state_of_incorporation=to_str(cp.state_of_incorporation),
        ein=to_str(cp.ein),
        is_large_accelerated_filer=cp.is_large_accelerated_filer,
        is_accelerated_filer=cp.is_accelerated_filer,
        is_non_accelerated_filer=cp.is_non_accelerated_filer,
        is_smaller_reporting_company=cp.is_smaller_reporting_company,
        is_emerging_growth_company=cp.is_emerging_growth_company,
        is_rule_415=bool(cp.is_rule_415),
        is_rule_462b=bool(cp.is_rule_462b),
        is_rule_462e=bool(cp.is_rule_462e),
        confidence=to_str(cp.confidence) or "low",
    )


def registration_s3_data(obj: RegistrationS3) -> RegistrationS3Data:
    return RegistrationS3Data(
        form=obj.form,
        company=to_str(obj.company),
        filing_date=_date_str(obj.filing_date),
        accession_number=to_str(obj.accession_number),
        is_amendment=bool(obj.is_amendment),
        is_auto_shelf=bool(obj.is_auto_shelf),
        offering_type=obj.offering_type.value,
        registration_number=to_str(obj.registration_number),
        ein=to_str(obj.ein),
        state_of_incorporation=to_str(obj.state_of_incorporation),
        total_offering=to_float(obj.total_offering),
        net_fee=to_float(obj.net_fee),
        fee_deferred=bool(obj.fee_deferred),
        securities=[_fee_security(s) for s in obj.securities],
        cover_page=_cover_page(obj.cover_page),
        fee_table=fee_table(obj.fee_table),
        related_filings=None,  # cross-entity fetch, served separately
        takedowns=None,  # cross-entity fetch, served separately
    )
