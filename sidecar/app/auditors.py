"""Multi-auditor extraction from a `CompanyReport`'s XBRL DEI facts.

edgar core exposes only `obj.auditor` -- the single signing auditor (first DEI fact). A filing that
reports an auditor CHANGE tags the current and prior firms on separate period contexts, so this
recovers the full ordered list (current period first) straight from the PUBLIC XBRL facts query API
(`xbrl.facts.query().by_concept(...)`). Each auditor's four DEI facts (name/location/firm id/ICFR
flag) share one period context; the facts are grouped by that context and the period end orders the
list. Shared across the CompanyReport family (10-K / 10-Q / 20-F / 40-F).
"""

from __future__ import annotations

from typing import Any

from app.models.forms.company_report import Auditor
from app.serialize import to_str

# exact concept names (namespace underscore -> colon inside by_concept); AuditorName drives the list
_NAME = "dei_AuditorName"
_LOCATION = "dei_AuditorLocation"
_FIRM_ID = "dei_AuditorFirmId"
_ICFR = "dei_IcfrAuditorAttestationFlag"


def _context_values(facts: Any, concept: str) -> dict[str, Any]:
    # context_ref -> raw DEI value; first wins so a duplicated tag can't fork the lookup
    values: dict[str, Any] = {}
    for fact in facts.query().by_concept(concept, exact=True).execute():
        context_ref = fact.get("context_ref")
        if context_ref is not None and context_ref not in values:
            values[context_ref] = fact.get("value")
    return values


def _firm_id(raw: Any) -> int | None:
    text = to_str(raw)
    if text is None:
        return None
    try:
        return int(text)  # PCAOB firm ID; unparseable DEI text -> null
    except ValueError:
        return None


def _icfr(raw: Any) -> bool:
    text = to_str(raw)
    return text is not None and text.lower() == "true"


def _period_end(fact: dict[str, Any]) -> str | None:
    # DEI auditor facts are duration-scoped; instant fallback keeps a malformed context from dropping it
    return to_str(fact.get("period_end")) or to_str(fact.get("period_instant"))


def extract_auditors(obj: Any) -> list[Auditor]:
    """Ordered wire auditors (current period first; empty when no DEI auditor facts)."""
    financials = obj.financials
    xbrl = financials.xb if financials is not None else None
    if xbrl is None:
        return []

    facts = xbrl.facts
    locations = _context_values(facts, _LOCATION)
    firm_ids = _context_values(facts, _FIRM_ID)
    icfr_flags = _context_values(facts, _ICFR)

    auditors: list[Auditor] = []
    seen: set[Any] = set()
    for fact in facts.query().by_concept(_NAME, exact=True).execute():
        context_ref = fact.get("context_ref")
        if context_ref in seen:
            continue
        seen.add(context_ref)
        name = to_str(fact.get("value"))
        if name is None:  # no auditor name on this context -> not an auditor
            continue
        auditors.append(
            Auditor(
                name=name,
                location=to_str(locations.get(context_ref)),
                firm_id=_firm_id(firm_ids.get(context_ref)),
                icfr_attestation=_icfr(icfr_flags.get(context_ref)),
                period_end=_period_end(fact),
            )
        )

    # current period first: ISO date strings sort chronologically; contexts without a period end sort last
    auditors.sort(key=lambda auditor: auditor.period_end or "", reverse=True)
    return auditors
