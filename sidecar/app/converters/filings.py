"""edgartools Filings index rows -> wire models, explicit field-by-field."""

from __future__ import annotations

from typing import Any

from edgar._filings import Filings

from app.cik import pad_cik
from app.models.common import FilingRef, FilingsPage
from app.models.filings import CurrentFilingRef, CurrentFilingsPage
from app.pagination import paginate
from app.serialize import to_utc_datetime


def filing_ref_from_row(row: dict[str, Any]) -> FilingRef:
    return FilingRef(
        accession_number=row["accession_number"],
        form=row["form"],
        cik=pad_cik(row["cik"]),
        company=row["company"],
        filing_date=row["filing_date"],
    )


def current_filing_ref_from_row(row: dict[str, Any]) -> CurrentFilingRef:
    accepted = to_utc_datetime(row["accepted"])
    if accepted is None:
        # every getcurrent atom entry carries <updated>; absence means the feed parser broke
        raise ValueError(f"feed entry {row['accession_number']} has no acceptance time")
    return CurrentFilingRef(
        accession_number=row["accession_number"],
        form=row["form"],
        cik=pad_cik(row["cik"]),
        company=row["company"],
        filing_date=row["filing_date"],
        accepted=accepted,
    )


def filings_page(filings: Filings, start: int, page_size: int) -> FilingsPage:
    total = len(filings.data)
    rows = filings.data.slice(start, page_size).to_pylist()
    page = paginate(total, start, page_size)
    return FilingsPage(
        filings=[filing_ref_from_row(row) for row in rows],
        total=total,
        start=start,
        page_size=page_size,
        has_more=page.has_more,
        next_start=page.next_start,
    )


def current_filings_page(filings: Filings, raw_count: int, start: int, page_size: int) -> CurrentFilingsPage:
    # has_more from the raw pre-filter count: a full SEC page means more may follow
    has_more = raw_count == page_size
    return CurrentFilingsPage(
        filings=[current_filing_ref_from_row(row) for row in filings.data.to_pylist()],
        start=start,
        page_size=page_size,
        has_more=has_more,
        next_start=start + page_size if has_more else None,
    )
