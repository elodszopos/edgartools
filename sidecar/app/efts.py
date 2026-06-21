"""EFTS request encoding and response decoding for the /search endpoint.

edgar.search.efts exposes only the single-shot search_filings() wrapper; its
param-building and hit/aggregation parsing are private. /search drives its own
paginated fetch against EFTS_BASE_URL, so the encode/decode is here, reusing
edgar's public EFTSResult / EFTSAggregations / Aggregation dataclasses.

NOTE: parse_hit/parse_aggregations mirror edgar.search.efts._parse_hit/_parse_aggregations
(private). If edgar changes its EFTS response parsing, these must be updated in lockstep.
"""

from __future__ import annotations

from edgar.search.efts import Aggregation, EFTSAggregations, EFTSResult


def _format_accession(adsh: str) -> str:
    # EFTS returns adsh without dashes; render the standard NNNNNNNNNN-NN-NNNNNN form
    adsh = adsh.replace("-", "")
    if len(adsh) == 18:
        return f"{adsh[:10]}-{adsh[10:12]}-{adsh[12:]}"
    return adsh


def build_efts_params(
    q: str,
    *,
    forms: list[str] | None = None,
    items: list[str] | None = None,
    cik: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, str]:
    """EFTS query params for an already-resolved CIK. EFTS accepts q="" when other filters are set."""
    params: dict[str, str] = {"q": q}
    if forms:
        params["forms"] = ",".join(forms)
    if items:
        params["items"] = ",".join(items)
    if start_date or end_date:
        params["dateRange"] = "custom"
        if start_date:
            params["startdt"] = start_date
        if end_date:
            params["enddt"] = end_date
    if cik:
        params["ciks"] = cik
    return params


def parse_hit(hit: dict) -> EFTSResult:
    """Decode a single EFTS `hits.hits[]` entry into the public EFTSResult dataclass."""
    source = hit.get("_source", {})
    names = source.get("display_names", [])
    ciks = source.get("ciks", [])
    sics = source.get("sics", [])
    biz_locations = source.get("biz_locations", [])
    biz_states = source.get("biz_states", [])
    inc_states = source.get("inc_states", [])

    # _id is "accession:document_filename"
    raw_id = hit.get("_id", "")
    document_id = raw_id.split(":", 1)[1] if ":" in raw_id else None

    return EFTSResult(
        accession_number=_format_accession(source.get("adsh", "")),
        form=source.get("form", ""),
        filed=source.get("file_date", ""),
        company=names[0] if names else None,
        cik=str(ciks[0]) if ciks else None,
        period=source.get("period_ending"),
        score=hit.get("_score", 0.0) or 0.0,
        file_type=source.get("file_type"),
        file_description=source.get("file_description"),
        document_id=document_id,
        items=source.get("items", []) or [],
        sic=str(sics[0]) if sics else None,
        location=biz_locations[0] if biz_locations else None,
        state=biz_states[0] if biz_states else None,
        inc_state=inc_states[0] if inc_states else None,
    )


def parse_aggregations(aggs_data: dict) -> EFTSAggregations:
    """Decode EFTS faceted aggregation buckets into the public EFTSAggregations dataclass."""

    def _buckets(filter_key: str) -> list[Aggregation]:
        filter_data = aggs_data.get(filter_key, {})
        return [Aggregation(key=b.get("key", ""), count=b.get("doc_count", 0)) for b in filter_data.get("buckets", [])]

    return EFTSAggregations(
        entities=_buckets("entity_filter"),
        sics=_buckets("sic_filter"),
        states=_buckets("biz_states_filter"),
        forms=_buckets("form_filter"),
    )
