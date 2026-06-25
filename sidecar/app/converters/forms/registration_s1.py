"""edgar `RegistrationS1` (S-1 / F-1 family) -> `RegistrationS1Data`, explicit field-by-field.

Cover-page bools pass through directly (pydantic already typed them bool|None); strings pass through
`to_str`. The fee table and the four own-document table sections (selling stockholders, dilution,
capitalization, underwriting) delegate to the shared `offering.py` converters. `offering_type` is the
edgar S1OfferingType enum's `.value`. Convenience scalars (registration_number, ein, sic_code,
state_of_incorporation, total_offering, net_fee, securities) map from the edgar object directly.
Cross-entity lifecycle properties (takedowns, related_filings, effective_date, is_effective) are set
to None -- they require cross-filing SEC fetches served at separate endpoints.
"""

from __future__ import annotations

from typing import Any

from edgar.offerings.registration_s1 import RegistrationS1

from app.converters.forms.offering import (
    fee_security,
    capitalization,
    dilution,
    fee_table,
    selling_stockholders,
    underwriting,
)
from app.models.forms.registration_s1 import RegistrationS1Data, S1CoverPage
from app.serialize import to_date, to_float, to_iso_str, to_str


def _cover_page(cp: Any) -> S1CoverPage:
    return S1CoverPage(
        company_name=to_str(cp.company_name) or "",  # edgar requires it; never blank in practice
        registration_number=to_str(cp.registration_number),
        state_of_incorporation=to_str(cp.state_of_incorporation),
        sic_code=to_str(cp.sic_code),
        ein=to_str(cp.ein),
        is_large_accelerated_filer=cp.is_large_accelerated_filer,
        is_accelerated_filer=cp.is_accelerated_filer,
        is_non_accelerated_filer=cp.is_non_accelerated_filer,
        is_smaller_reporting_company=cp.is_smaller_reporting_company,
        is_emerging_growth_company=cp.is_emerging_growth_company,
        is_rule_415=bool(cp.is_rule_415),
        is_rule_462b=bool(cp.is_rule_462b),
        is_rule_462e=bool(cp.is_rule_462e),
        security_description=to_str(cp.security_description),
        confidence=to_str(cp.confidence) or "low",
    )


def registration_s1_data(obj: RegistrationS1) -> RegistrationS1Data:
    return RegistrationS1Data(
        form=obj.form,
        company=to_str(obj.company),
        filing_date=to_iso_str(obj.filing_date),
        accession_number=to_str(obj.accession_number),
        is_amendment=bool(obj.is_amendment),
        offering_type=obj.offering_type.value,
        registration_number=to_str(obj.registration_number),
        ein=to_str(obj.ein),
        sic_code=to_str(obj.sic_code),
        state_of_incorporation=to_str(obj.state_of_incorporation),
        total_offering=to_float(obj.total_offering),
        net_fee=to_float(obj.net_fee),
        securities=[fee_security(s) for s in obj.securities],
        cover_page=_cover_page(obj.cover_page),
        fee_table=fee_table(obj.fee_table),
        selling_stockholders=selling_stockholders(obj.selling_stockholders),
        dilution=dilution(obj.dilution),
        capitalization=capitalization(obj.capitalization),
        underwriting=underwriting(obj.underwriting),
        is_effective=None,  # cross-entity fetch, served separately
        effective_date=None,  # cross-entity fetch, served separately
        related_filings=None,  # cross-entity fetch, served separately
        takedowns=None,  # cross-entity fetch, served separately
    )
