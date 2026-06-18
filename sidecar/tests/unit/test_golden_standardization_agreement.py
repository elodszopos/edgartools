"""Cross-golden standardization agreement.

The single-filing and stitched financials paths share standardize_statement,
so a raw XBRL concept must resolve to the same standard_concept in every
golden that carries it. A disagreement means the mapping data or one of the
two paths regressed (review finding #20: PaymentsOfDividends was labeled
DistributionsToMinorityInterests on AAPL cash flow statements).
"""

import json
from pathlib import Path

RESPONSES = Path(__file__).parents[2] / "ts" / "fixtures" / "responses"
GOLDEN_DIRS = ("company_financials", "company_financials_multi")


def _statement_records(golden: dict):
    for key, value in golden.items():
        if isinstance(value, dict) and isinstance(value.get("records"), list):
            yield key, value["records"]


def _collect_mappings():
    """Map (cik, concept) -> {standard_concept: [golden file references]}."""
    seen: dict = {}
    for dirname in GOLDEN_DIRS:
        for path in sorted((RESPONSES / dirname).glob("*.json")):
            golden = json.loads(path.read_text())
            cik = golden.get("cik")
            if cik is None:
                continue
            for statement, records in _statement_records(golden):
                for record in records:
                    concept = record.get("concept")
                    standard = record.get("standard_concept")
                    if not concept or standard is None:
                        continue
                    ref = f"{dirname}/{path.name}:{statement}"
                    seen.setdefault((cik, concept), {}).setdefault(standard, []).append(ref)
    return seen


def test_goldens_exist():
    assert any((RESPONSES / d).glob("*.json") for d in GOLDEN_DIRS)


def test_same_concept_same_standard_concept_across_goldens():
    conflicts = {key: targets for key, targets in _collect_mappings().items() if len(targets) > 1}
    assert not conflicts, f"raw concepts standardized differently across goldens (single vs stitched divergence): {json.dumps(conflicts, indent=2)}"


def test_dividend_cluster_ground_truth():
    """Pin the corrected mappings to real filing lines (finding #20)."""
    mappings = _collect_mappings()

    def standard_for(cik: str, concept: str) -> str:
        targets = mappings[(cik, concept)]
        assert len(targets) == 1
        return next(iter(targets))

    # AAPL 10-K "Payments of dividends": common dividends, not NCI distributions
    assert standard_for("0000320193", "us-gaap_PaymentsOfDividends") == "CommonDividendsPaid"
    # Realty Income files separate common, preferred, and NCI dividend lines
    assert standard_for("0000726728", "us-gaap_PaymentsOfDividendsCommonStock") == "CommonDividendsPaid"
    assert standard_for("0000726728", "us-gaap_PaymentsOfDividendsPreferredStockAndPreferenceStock") == "PreferredDividendExpense"
    assert standard_for("0000726728", "us-gaap_PaymentsOfDividendsMinorityInterest") == "DistributionsToMinorityInterests"
    # INFY 20-F labels this line "Payment of dividends to non-controlling interests"
    assert (
        standard_for("0001067491", "ifrs-full_DividendsPaidToNoncontrollingInterestsClassifiedAsFinancingActivities")
        == "DistributionsToMinorityInterests"
    )
    assert standard_for("0001067491", "ifrs-full_DividendsPaidClassifiedAsFinancingActivities") == "CommonDividendsPaid"
