"""edgartools Company/EntityData -> wire models, explicit field-by-field.

Profile policy: serve ONLY what the submissions JSON carries plus in-memory derivations
(is_company/is_individual/is_bdc/filer_category/display_name). Properties that trigger
cross-filing or facts fetches (filer_type, business_category, public_float, ...) are
excluded and belong to dedicated endpoints.
"""

from __future__ import annotations

from edgar.entity.core import Company
from edgar.entity.data import Address

from app.cik import pad_cik
from app.models.common import Address as WireAddress
from app.models.company import (
    CompanyProfile,
    EntityFormerName,
    SubmissionFiling,
    SubmissionsPage,
)
from app.serialize import to_bool, to_date, to_int, to_str, utc_naive_to_utc


def _entity_address(address: Address | None) -> WireAddress | None:
    if address is None or address.empty:
        return None
    return WireAddress(
        street1=to_str(address.street1),
        street2=to_str(address.street2),
        city=to_str(address.city),
        state_or_country=to_str(address.state_or_country),
        state_or_country_description=to_str(address.state_or_country_desc),
        zipcode=to_str(address.zipcode),
    )


def _former_names(data: object) -> list[EntityFormerName]:
    # entries are {'name', 'from', 'to'} with dates pre-truncated to YYYY-MM-DD
    names = getattr(data, "former_names", None) or []
    return [
        EntityFormerName(
            name=to_str(entry.get("name")),
            from_date=to_date(to_str(entry.get("from"))),
            to_date=to_date(to_str(entry.get("to"))),
        )
        for entry in names
    ]


def company_profile(company: Company) -> CompanyProfile:
    data = company.data
    category = company.filer_category
    state = to_str(data.state_of_incorporation)
    return CompanyProfile(
        cik=pad_cik(company.cik),
        name=to_str(data.name),
        display_name=to_str(company.display_name),
        entity_type=to_str(data.entity_type),
        tickers=list(data.tickers or []),
        exchanges=[to_str(exchange) for exchange in data.exchanges or []],
        sic=to_str(data.sic),
        sic_description=to_str(data.sic_description),
        # category and the fields below arrive via EntityData kwargs - no declared attrs
        category=to_str(getattr(data, "category", None)),
        filer_status=category.status.value if category.status else None,
        is_smaller_reporting_company=category.is_smaller_reporting_company,
        is_emerging_growth_company=category.is_emerging_growth_company,
        fiscal_year_end=to_str(data.fiscal_year_end),
        ein=to_str(data.ein),
        phone=to_str(getattr(data, "phone", None)),
        description=to_str(getattr(data, "description", None)),
        website=to_str(getattr(data, "website", None)),
        investor_website=to_str(getattr(data, "investor_website", None)),
        state_of_incorporation=state,
        state_of_incorporation_description=to_str(getattr(data, "state_of_incorporation_description", None)),
        # foreign detection delegated to the public Company.is_foreign property, but only with a
        # state code: its stateless fallback (filer_type) returns False for individuals, where the
        # honest value is unknown (null). With a state code the property is a pure in-memory lookup.
        is_foreign=company.is_foreign if state else None,
        flags=to_str(getattr(data, "flags", None)),
        business_address=_entity_address(data.business_address),
        mailing_address=_entity_address(data.mailing_address),
        former_names=_former_names(data),
        insider_transaction_for_owner_exists=bool(getattr(data, "insider_transaction_for_owner_exists", False)),
        insider_transaction_for_issuer_exists=bool(getattr(data, "insider_transaction_for_issuer_exists", False)),
        is_company=data.is_company,
        is_individual=not data.is_company,
        is_bdc=data.is_bdc,
    )


def _submission_filing(row: dict) -> SubmissionFiling:
    items = to_str(row.get("items"))
    return SubmissionFiling(
        accession_number=row["accession_number"],
        form=row["form"],
        filing_date=row["filing_date"],
        report_date=to_date(to_str(row.get("reportDate"))),
        acceptance_datetime=utc_naive_to_utc(row.get("acceptanceDateTime")),
        act=to_str(row.get("act")),
        file_number=to_str(row.get("fileNumber")),
        items=[code.strip() for code in items.split(",")] if items else [],
        size=to_int(row.get("size")),
        is_xbrl=to_bool(row.get("isXBRL")),
        is_inline_xbrl=to_bool(row.get("isInlineXBRL")),
        primary_document=to_str(row.get("primaryDocument")),
        primary_doc_description=to_str(row.get("primaryDocDescription")),
    )


def submissions_page(company: Company, *, form: str | None, start: int, page_size: int) -> SubmissionsPage:
    # full history (recent + paginated submission files); rows stay in SEC order (newest first)
    filings = company.get_filings(form=form, trigger_full_load=True)
    table = filings.data
    total = table.num_rows
    rows = table.slice(start, page_size).to_pylist()
    has_more = start + len(rows) < total
    return SubmissionsPage(
        cik=pad_cik(company.cik),
        company=to_str(company.name),
        total=total,
        start=start,
        page_size=page_size,
        has_more=has_more,
        next_start=start + len(rows) if has_more else None,
        filings=[_submission_filing(row) for row in rows],
    )
