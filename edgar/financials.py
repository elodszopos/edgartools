from collections import Counter
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from edgar.core import log
from edgar.richtools import repr_rich
from edgar.xbrl import XBRL, XBRLS
from edgar.xbrl.core import get_currency_symbol
from edgar.xbrl.presentation import ViewType
from edgar.xbrl.statements import StitchedStatement
from edgar.xbrl.xbrl import XBRLFilingWithNoXbrlData

# Canonical XBRL concept local-names per metric, in resolution priority order.
# Getters match these against the rendered statement's concept column by bare
# local-name (taxonomy/company namespace stripped), so a single list resolves
# US GAAP, IFRS (ifrs-full), and company-extension tags (e.g. infy_PurchaseOf...).
# Match is exact local-name, never substring: that avoids picking near-named rows
# like NetIncomeLossAttributableToNoncontrollingInterest when NetIncomeLoss is the
# target (GH #814).
_METRIC_CONCEPTS: Dict[str, List[str]] = {
    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractsWithCustomers",
        "Revenues",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "SalesRevenueNet",
        "Revenue",
    ],
    "operating_income": [
        "OperatingIncomeLoss",
        "ProfitLossFromOperatingActivities",
    ],
    "net_income": [
        "NetIncomeLoss",
        "ProfitLoss",
    ],
    "total_assets": [
        "Assets",
    ],
    "total_liabilities": [
        "Liabilities",
    ],
    "stockholders_equity": [
        "StockholdersEquity",
        "Equity",
        "EquityAttributableToOwnersOfParent",
    ],
    "current_assets": [
        "AssetsCurrent",
        "CurrentAssets",
    ],
    "current_liabilities": [
        "LiabilitiesCurrent",
        "CurrentLiabilities",
    ],
    "operating_cash_flow": [
        "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
        "CashFlowsFromUsedInOperatingActivities",
    ],
    "capital_expenditures": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",
        "PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",
        "PurchaseOfPropertyPlantAndEquipmentAndIntangiblesClassifiedAsInvestingActivities",
    ],
    "shares_outstanding_basic": [
        "WeightedAverageNumberOfSharesOutstandingBasic",
        "WeightedAverageShares",
        "CommonStockSharesOutstanding",
    ],
    "shares_outstanding_diluted": [
        "WeightedAverageNumberOfDilutedSharesOutstanding",
        "WeightedAverageNumberOfSharesOutstandingDiluted",
        "AdjustedWeightedAverageShares",
    ],
}

# Non-period columns in render(standard=True).to_dataframe(); every other column is a
# period value column, ordered newest first (so period_offset 0 == most recent period).
_STATEMENT_META_COLUMNS = frozenset(
    {"concept", "label", "level", "abstract", "dimension", "is_breakdown", "standard_concept"}
)


def _bare_local_name(concept: str) -> str:
    """Reduce an XBRL concept to its bare, lowercased local-name.

    Cuts at the first ``_`` or ``:`` separator, stripping the taxonomy or company
    prefix: ``us-gaap_NetIncomeLoss``, ``ifrs-full:ProfitLoss`` and
    ``infy_PurchaseOfPropertyPlantAndEquipment...`` all reduce to their local name.
    """
    text = str(concept)
    for separator in ("_", ":"):
        index = text.find(separator)
        if index != -1:
            return text[index + 1:].lower()
    return text.lower()


class Financials:
    def __init__(self, xb: Optional[XBRL]):
        self.xb: XBRL = xb

    @classmethod
    def extract(cls, filing) -> Optional["Financials"]:
        try:
            xb = XBRL.from_filing(filing)
            return Financials(xb)
        except XBRLFilingWithNoXbrlData as e:
            # Handle the case where the filing does not have XBRL data
            log.warning(f"Filing {filing} does not contain XBRL data: {e}")
            return None

    def balance_sheet(self, include_dimensions: bool = None, view: ViewType = None):
        """
        Get the balance sheet.

        Args:
            include_dimensions: Default setting for whether to include dimensional segment data
                              when rendering or converting to DataFrame (default: False)
            view: StatementView controlling dimensional data display.
                  STANDARD: Face presentation matching SEC Viewer (display default)
                  DETAILED: All dimensional data included (to_dataframe default)
                  SUMMARY: Non-dimensional totals only

        Returns:
            A Statement object for the balance sheet, or None if not available
        """
        if self.xb is None:
            return None
        return self.xb.statements.balance_sheet(include_dimensions=include_dimensions, view=view)

    def income_statement(self, include_dimensions: bool = None, view: ViewType = None):
        """
        Get the income statement.

        Args:
            include_dimensions: Default setting for whether to include dimensional segment data
                              when rendering or converting to DataFrame (default: False)
            view: StatementView controlling dimensional data display.
                  STANDARD: Face presentation matching SEC Viewer (display default)
                  DETAILED: All dimensional data included (to_dataframe default)
                  SUMMARY: Non-dimensional totals only

        Returns:
            A Statement object for the income statement, or None if not available
        """
        if self.xb is None:
            return None
        return self.xb.statements.income_statement(include_dimensions=include_dimensions, view=view)

    def cashflow_statement(self, include_dimensions: bool = None, view: ViewType = None):
        """
        Get the cash flow statement.

        Args:
            include_dimensions: Default setting for whether to include dimensional segment data
                              when rendering or converting to DataFrame (default: False)
            view: StatementView controlling dimensional data display.
                  STANDARD: Face presentation matching SEC Viewer (display default)
                  DETAILED: All dimensional data included (to_dataframe default)
                  SUMMARY: Non-dimensional totals only

        Returns:
            A Statement object for the cash flow statement, or None if not available
        """
        if self.xb is None:
            return None
        return self.xb.statements.cashflow_statement(include_dimensions=include_dimensions, view=view)

    def cash_flow_statement(self, **kwargs):
        """Alias for cashflow_statement()."""
        return self.cashflow_statement(**kwargs)

    def statement_of_equity(self, include_dimensions: bool = None, view: ViewType = None):
        """
        Get the statement of equity.

        Args:
            include_dimensions: Default setting for whether to include dimensional segment data
                              when rendering or converting to DataFrame (default: False)
            view: StatementView controlling dimensional data display.
                  STANDARD: Face presentation matching SEC Viewer (display default)
                  DETAILED: All dimensional data included (to_dataframe default)
                  SUMMARY: Non-dimensional totals only

        Returns:
            A Statement object for the statement of equity, or None if not available
        """
        if self.xb is None:
            return None
        return self.xb.statements.statement_of_equity(include_dimensions=include_dimensions, view=view)

    def comprehensive_income(self, include_dimensions: bool = None, view: ViewType = None):
        """
        Get the comprehensive income statement.

        Args:
            include_dimensions: Default setting for whether to include dimensional segment data
                              when rendering or converting to DataFrame (default: False)
            view: StatementView controlling dimensional data display.
                  STANDARD: Face presentation matching SEC Viewer (display default)
                  DETAILED: All dimensional data included (to_dataframe default)
                  SUMMARY: Non-dimensional totals only

        Returns:
            A Statement object for the comprehensive income statement, or None if not available
        """
        if self.xb is None:
            return None
        return self.xb.statements.comprehensive_income(include_dimensions=include_dimensions, view=view)

    def cover(self):
        """
        Get the cover page.

        Returns:
            A Statement object for the cover page, or None if not available
        """
        if self.xb is None:
            return None
        return self.xb.statements.cover_page()

    # Standardized Financial Data Accessor Methods
    # These resolve common metrics by XBRL concept (us-gaap, ifrs-full, and
    # company-extension tags) from the rendered statement, independent of the
    # presentation label, so they work across filers and taxonomies.

    def _resolve_metric_value(self, statement_type: str,
                              concept_local_names: List[str],
                              period_offset: int = 0) -> Optional[Union[int, float]]:
        """
        Resolve a metric by exact XBRL concept local-name from a rendered statement.

        Tries each name in ``concept_local_names`` in order and returns the first
        period value found. Matching is on the bare local-name (namespace stripped,
        case-insensitive, exact - never substring), so US GAAP, IFRS, and
        company-extension tags all resolve through one curated list.

        Args:
            statement_type: Type of statement ('income', 'balance', 'cashflow')
            concept_local_names: Candidate concept local-names, highest priority first
            period_offset: Which period to get (0=most recent, 1=previous, etc.)

        Returns:
            The concept value if found, None otherwise
        """
        if self.xb is None:
            return None

        if statement_type == 'income':
            statement = self.income_statement()
        elif statement_type == 'balance':
            statement = self.balance_sheet()
        elif statement_type == 'cashflow':
            statement = self.cashflow_statement()
        else:
            return None

        if statement is None:
            return None

        try:
            # Rendering can raise on malformed XBRL; a metric miss must never propagate.
            df = statement.render(standard=True).to_dataframe()
        except Exception as e:
            log.debug(f"Error rendering {statement_type} statement for metric lookup: {e}")
            return None

        if df.empty or 'concept' not in df.columns:
            return None

        # Abstract rows are section headers and never carry values.
        if 'abstract' in df.columns:
            df = df[~df['abstract']].copy()

        period_columns = [col for col in df.columns if col not in _STATEMENT_META_COLUMNS]
        if len(period_columns) <= period_offset:
            return None
        period_col = period_columns[period_offset]

        concept_bare = df['concept'].astype(str).map(_bare_local_name)
        for name in concept_local_names:
            target = _bare_local_name(name)
            matches = df[concept_bare == target]
            for idx in range(len(matches)):
                value = matches.iloc[idx][period_col]

                # Skip empty/NA values - the same concept may appear on dimensional
                # rows with no top-level value; keep scanning to the populated row.
                if pd.isna(value) or value == '':
                    continue

                try:
                    return float(value) if '.' in str(value) else int(value)
                except (ValueError, TypeError):
                    continue
        return None

    def get_revenue(self, period_offset: int = 0) -> Optional[Union[int, float]]:
        """
        Get revenue from the income statement by XBRL concept.

        Resolves the us-gaap revenue concepts and the IFRS
        ``ifrs-full_RevenueFromContractsWithCustomers`` used by 20-F filers,
        regardless of how the row is labeled in the presentation.

        Args:
            period_offset: Which period to get (0=most recent, 1=previous, etc.)

        Returns:
            Revenue value if found, None otherwise

        Example:
            >>> company = Company('AAPL')
            >>> financials = company.get_financials()
            >>> revenue = financials.get_revenue()  # Most recent revenue
            >>> prev_revenue = financials.get_revenue(1)  # Previous period revenue
        """
        return self._resolve_metric_value('income', _METRIC_CONCEPTS['revenue'], period_offset)

    def get_net_income(self, period_offset: int = 0) -> Optional[Union[int, float]]:
        """
        Get net income from the income statement by XBRL concept.

        Resolves ``us-gaap_NetIncomeLoss`` first (the parent-attributable line for
        filers reporting noncontrolling interest) then ``ifrs-full_ProfitLoss`` for
        20-F filers. Exact concept match avoids the
        NetIncomeLossAttributableToNoncontrollingInterest row that a substring match
        would wrongly pick (GH #814).

        Args:
            period_offset: Which period to get (0=most recent, 1=previous, etc.)

        Returns:
            Net income value if found, None otherwise

        Example:
            >>> company = Company('AAPL')
            >>> financials = company.get_financials()
            >>> net_income = financials.get_net_income()
        """
        return self._resolve_metric_value('income', _METRIC_CONCEPTS['net_income'], period_offset)

    def get_operating_income(self, period_offset: int = 0) -> Optional[Union[int, float]]:
        """
        Get operating income from the income statement by XBRL concept.

        Resolves ``us-gaap_OperatingIncomeLoss`` and the IFRS
        ``ifrs-full_ProfitLossFromOperatingActivities`` (20-F filers). Returns None
        for filers that do not report an operating-income line (e.g. banks).

        Args:
            period_offset: Which period to get (0=most recent, 1=previous, etc.)

        Returns:
            Operating income value if found, None otherwise

        Example:
            >>> company = Company('AAPL')
            >>> financials = company.get_financials()
            >>> operating_income = financials.get_operating_income()
        """
        return self._resolve_metric_value('income', _METRIC_CONCEPTS['operating_income'], period_offset)

    def get_total_assets(self, period_offset: int = 0) -> Optional[Union[int, float]]:
        """
        Get total assets from the balance sheet using standardized labels.

        Args:
            period_offset: Which period to get (0=most recent, 1=previous, etc.)

        Returns:
            Total assets value if found, None otherwise

        Example:
            >>> company = Company('AAPL')
            >>> financials = company.get_financials()
            >>> total_assets = financials.get_total_assets()
        """
        return self._resolve_metric_value('balance', _METRIC_CONCEPTS['total_assets'], period_offset)

    def get_total_liabilities(self, period_offset: int = 0) -> Optional[Union[int, float]]:
        """
        Get total liabilities from the balance sheet by XBRL concept.

        Args:
            period_offset: Which period to get (0=most recent, 1=previous, etc.)

        Returns:
            Total liabilities value if found, None otherwise
        """
        return self._resolve_metric_value('balance', _METRIC_CONCEPTS['total_liabilities'], period_offset)

    def get_stockholders_equity(self, period_offset: int = 0) -> Optional[Union[int, float]]:
        """
        Get stockholders' equity from the balance sheet by XBRL concept.

        Resolves ``us-gaap_StockholdersEquity`` and the IFRS ``ifrs-full_Equity`` /
        ``ifrs-full_EquityAttributableToOwnersOfParent`` (20-F filers).

        Args:
            period_offset: Which period to get (0=most recent, 1=previous, etc.)

        Returns:
            Stockholders' equity value if found, None otherwise
        """
        return self._resolve_metric_value('balance', _METRIC_CONCEPTS['stockholders_equity'], period_offset)

    def get_operating_cash_flow(self, period_offset: int = 0) -> Optional[Union[int, float]]:
        """
        Get operating cash flow from the cash flow statement by XBRL concept.

        Resolves ``us-gaap_NetCashProvidedByUsedInOperatingActivities`` (and its
        continuing-operations variant) plus the IFRS
        ``ifrs-full_CashFlowsFromUsedInOperatingActivities`` (20-F filers). Concept
        match means the AAPL label "Cash generated by operating activities" - which
        no label regex caught - now resolves (GH #814 sibling fix).

        Args:
            period_offset: Which period to get (0=most recent, 1=previous, etc.)

        Returns:
            Operating cash flow value if found, None otherwise
        """
        return self._resolve_metric_value('cashflow', _METRIC_CONCEPTS['operating_cash_flow'], period_offset)

    def get_free_cash_flow(self, period_offset: int = 0) -> Optional[Union[int, float]]:
        """
        Calculate free cash flow (Operating Cash Flow - Capital Expenditures).

        Args:
            period_offset: Which period to get (0=most recent, 1=previous, etc.)

        Returns:
            Free cash flow if both components found, None otherwise
        """
        operating_cf = self.get_operating_cash_flow(period_offset)
        capex = self.get_capital_expenditures(period_offset)

        if operating_cf is not None and capex is not None:
            # CapEx is usually negative, so we subtract it (making FCF = OCF - |CapEx|)
            return operating_cf - abs(capex)
        return None

    def get_capital_expenditures(self, period_offset: int = 0) -> Optional[Union[int, float]]:
        """
        Get capital expenditures from the cash flow statement by XBRL concept.

        Resolves the us-gaap purchase-of-PP&E concepts and the IFRS / company
        extensions (e.g. ``infy_PurchaseOfPropertyPlantAndEquipment...``) that 20-F
        filers use. The bare local-name match strips the company prefix, so those
        extension tags resolve through the shared list.

        Args:
            period_offset: Which period to get (0=most recent, 1=previous, etc.)

        Returns:
            Capital expenditures value if found, None otherwise
        """
        return self._resolve_metric_value('cashflow', _METRIC_CONCEPTS['capital_expenditures'], period_offset)

    def get_current_assets(self, period_offset: int = 0) -> Optional[Union[int, float]]:
        """
        Get current assets from the balance sheet using standardized labels.

        Args:
            period_offset: Which period to get (0=most recent, 1=previous, etc.)

        Returns:
            Current assets value if found, None otherwise
        """
        return self._resolve_metric_value('balance', _METRIC_CONCEPTS['current_assets'], period_offset)

    def get_current_liabilities(self, period_offset: int = 0) -> Optional[Union[int, float]]:
        """
        Get current liabilities from the balance sheet by XBRL concept.

        Args:
            period_offset: Which period to get (0=most recent, 1=previous, etc.)

        Returns:
            Current liabilities value if found, None otherwise
        """
        return self._resolve_metric_value('balance', _METRIC_CONCEPTS['current_liabilities'], period_offset)

    def get_shares_outstanding_basic(self, period_offset: int = 0) -> Optional[Union[int, float]]:
        """
        Get weighted average basic shares outstanding from the income statement.

        Returns the weighted average basic shares used in computing basic EPS.
        Resolves the us-gaap concept and the IFRS ``ifrs-full_WeightedAverageShares``
        (20-F filers); falls back to ``CommonStockSharesOutstanding``.

        Args:
            period_offset: Which period to get (0=most recent, 1=previous, etc.)

        Returns:
            Basic shares outstanding if found, None otherwise

        Example:
            >>> company = Company('AAPL')
            >>> financials = company.get_financials()
            >>> shares = financials.get_shares_outstanding_basic()
            >>> print(f"Basic shares: {shares:,.0f}")

            >>> # Get previous period
            >>> prev_shares = financials.get_shares_outstanding_basic(period_offset=1)

            >>> # Also works with quarterly financials
            >>> quarterly = company.get_quarterly_financials()
            >>> q_shares = quarterly.get_shares_outstanding_basic()
        """
        return self._resolve_metric_value('income', _METRIC_CONCEPTS['shares_outstanding_basic'], period_offset)

    def get_shares_outstanding_diluted(self, period_offset: int = 0) -> Optional[Union[int, float]]:
        """
        Get weighted average diluted shares outstanding from the income statement.

        Returns the weighted average diluted shares used in computing diluted EPS
        (includes options, convertibles, and other dilutive instruments). Resolves
        the us-gaap concepts and the IFRS ``ifrs-full_AdjustedWeightedAverageShares``
        (20-F filers).

        Args:
            period_offset: Which period to get (0=most recent, 1=previous, etc.)

        Returns:
            Diluted shares outstanding if found, None otherwise

        Example:
            >>> company = Company('AAPL')
            >>> financials = company.get_financials()
            >>> diluted_shares = financials.get_shares_outstanding_diluted()
            >>> print(f"Diluted shares: {diluted_shares:,.0f}")

            >>> # Compare basic vs diluted
            >>> basic = financials.get_shares_outstanding_basic()
            >>> diluted = financials.get_shares_outstanding_diluted()
            >>> dilution = (diluted - basic) / basic * 100 if basic else None
            >>> print(f"Dilution effect: {dilution:.2f}%")
        """
        return self._resolve_metric_value('income', _METRIC_CONCEPTS['shares_outstanding_diluted'], period_offset)

    def get_financial_metrics(self) -> Dict[str, Any]:
        """
        Get a dictionary of common financial metrics using standardized labels.

        Returns:
            Dictionary containing available financial metrics

        Example:
            >>> company = Company('AAPL')
            >>> financials = company.get_financials()
            >>> metrics = financials.get_financial_metrics()
            >>> print(f"Revenue: ${metrics.get('revenue', 'N/A'):,}")
        """
        metrics = {}

        # Income Statement Metrics
        metrics['revenue'] = self.get_revenue()
        metrics['operating_income'] = self.get_operating_income()
        metrics['net_income'] = self.get_net_income()

        # Balance Sheet Metrics
        metrics['total_assets'] = self.get_total_assets()
        metrics['total_liabilities'] = self.get_total_liabilities()
        metrics['stockholders_equity'] = self.get_stockholders_equity()
        metrics['current_assets'] = self.get_current_assets()
        metrics['current_liabilities'] = self.get_current_liabilities()

        # Cash Flow Metrics
        metrics['operating_cash_flow'] = self.get_operating_cash_flow()
        metrics['capital_expenditures'] = self.get_capital_expenditures()
        metrics['free_cash_flow'] = self.get_free_cash_flow()

        # Share Metrics
        metrics['shares_outstanding_basic'] = self.get_shares_outstanding_basic()
        metrics['shares_outstanding_diluted'] = self.get_shares_outstanding_diluted()

        # Calculate basic ratios if we have the data
        if metrics['current_assets'] and metrics['current_liabilities']:
            try:
                metrics['current_ratio'] = metrics['current_assets'] / metrics['current_liabilities']
            except (TypeError, ZeroDivisionError):
                metrics['current_ratio'] = None
        else:
            metrics['current_ratio'] = None

        if metrics['total_liabilities'] and metrics['total_assets']:
            try:
                metrics['debt_to_assets'] = metrics['total_liabilities'] / metrics['total_assets']
            except (TypeError, ZeroDivisionError):
                metrics['debt_to_assets'] = None
        else:
            metrics['debt_to_assets'] = None

        return metrics

    def __str__(self):
        """Concise string representation for LLMs and logging."""
        if self.xb is None:
            return "Financials(No data)"

        info = self.xb.entity_info
        name = info.get('entity_name', 'Unknown')
        ticker = info.get('ticker', '')
        doc_type = info.get('document_type', '')
        fiscal_year = info.get('fiscal_year', '')
        fiscal_period = info.get('fiscal_period', '')

        # Build period string (e.g., "FY2025" or "Q3 2025")
        period_str = f"{fiscal_period}{fiscal_year}" if fiscal_period and fiscal_year else ""

        # Fact count
        fact_count = len(self.xb.facts) if self.xb.facts else 0

        parts = [name]
        if ticker:
            parts.append(f"[{ticker}]")
        if doc_type:
            parts.append(doc_type)
        if period_str:
            parts.append(period_str)
        parts.append(f"• {fact_count:,} facts")

        return f"Financials({' '.join(parts)})"

    def get_currency_symbol(self) -> str:
        """
        Get the reporting currency symbol for this filing.

        Detects the most common monetary unit from the XBRL units dict.
        Returns '$' as default if currency cannot be determined.
        """
        if self.xb is None:
            return "$"
        try:
            # Count currency measures across all unit definitions
            currencies = Counter()
            for unit_info in self.xb.units.values():
                if unit_info.get('type') == 'simple':
                    measure = unit_info.get('measure', '')
                    if measure.startswith('iso4217:'):
                        currencies[measure] += 1
            if currencies:
                most_common = currencies.most_common(1)[0][0]
                return get_currency_symbol(most_common)
        except Exception as e:
            log.debug(f"Currency detection failed, defaulting to $: {e}")
        return "$"

    def to_context(self) -> str:
        """
        Return context string for LLMs with available actions.

        This guides AI agents on what they can do with this Financials object,
        focusing on the high-level Financials API rather than raw XBRL access.
        """
        if self.xb is None:
            return "Financials: No data available"

        info = self.xb.entity_info
        name = info.get('entity_name', 'Unknown')
        ticker = info.get('ticker', '')
        doc_type = info.get('document_type', '')
        fiscal_year = info.get('fiscal_year', '')
        fiscal_period = info.get('fiscal_period', '')

        ticker_part = f" [{ticker}]" if ticker else ""
        period_str = f"{fiscal_period}{fiscal_year}" if fiscal_period and fiscal_year else ""

        lines = [
            f"Financials: {name}{ticker_part} {doc_type} {period_str}".strip(),
            "",
            "AVAILABLE STATEMENTS:",
            "  financials.income_statement()",
            "  financials.balance_sheet()",
            "  financials.cashflow_statement()",
            "  financials.statement_of_equity()",
            "  financials.comprehensive_income()",
            "",
            "QUICK METRICS (returns value or None):",
            "  financials.get_revenue()",
            "  financials.get_operating_income()",
            "  financials.get_net_income()",
            "  financials.get_total_assets()",
            "  financials.get_stockholders_equity()",
            "  financials.get_operating_cash_flow()",
            "  financials.get_free_cash_flow()",
            "",
            "ALL METRICS:",
            "  financials.get_financial_metrics()  # Dict with 14 metrics + ratios",
        ]

        return "\n".join(lines)

    def __rich__(self):
        if self.xb is None:
            return "No XBRL data available"
        return self.xb.__rich__()

    def __repr__(self):
        return repr_rich(self.__rich__())


class MultiFinancials:
    """
    Merges the financial statements from multiple periods into a single financials.
    """

    def __init__(self, xbs: XBRLS):
        self.xbs = xbs

    @classmethod
    def extract(cls, filings) -> "MultiFinancials":
        return cls(XBRLS.from_filings(filings))

    def balance_sheet(self, view: ViewType = None) -> Optional[StitchedStatement]:
        return self.xbs.statements.balance_sheet(view=view)

    def income_statement(self, view: ViewType = None) -> Optional[StitchedStatement]:
        return self.xbs.statements.income_statement(view=view)

    def cashflow_statement(self, view: ViewType = None) -> Optional[StitchedStatement]:
        return self.xbs.statements.cashflow_statement(view=view)

    def cash_flow_statement(self, **kwargs):
        """Alias for cashflow_statement()."""
        return self.cashflow_statement(**kwargs)

    def __rich__(self):
        return self.xbs.__rich__()

    def __repr__(self):
        return repr_rich(self.__rich__())
