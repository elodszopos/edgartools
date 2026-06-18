# Ownership — Base Class for Form 3 / 4 / 5

**SEC form codes**: `3`, `3/A`, `4`, `4/A`, `5`, `5/A`
**Python class**: `Ownership` (base); `Form3`, `Form4`, `Form5` are thin subclasses
**Access**: `filing.obj()` → `Form3 | Form4 | Form5` (all are `Ownership` instances)
**Source**: `edgar/ownership/ownershipforms.py:1732`

---

## Complete Field Reference

### Instance Attributes (set in `__init__`)

| Field | Type | Description |
|-------|------|-------------|
| `form` | `str` | `"3"`, `"4"`, or `"5"` — read from `<documentType>` |
| `footnotes` | `Footnotes` | Dict-like; keyed by footnote ID (e.g., `"F1"`) |
| `issuer` | `Issuer` | Issuer identity — CIK, name, ticker |
| `reporting_owners` | `ReportingOwners` | List wrapper of `Owner` objects |
| `non_derivative_table` | `NonDerivativeTable` | Common stock holdings + transactions |
| `derivative_table` | `DerivativeTable` | Derivative holdings + transactions |
| `signatures` | `OwnerSignatures` | List of `OwnerSignature` objects |
| `reporting_period` | `str` | Period of report (`YYYY-MM-DD`) from `<periodOfReport>` |
| `remarks` | `str` | Free-text remarks from `<remarks>`; empty string if absent |
| `no_securities` | `bool` | `True` when `<noSecuritiesOwned>1` — Form 3 filed with no holdings |

### Properties

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `insider_name` | `str` | no | Owner names joined with `" / "` |
| `position` | `str` | no | Owner positions joined with `"/ "` |
| `market_trades` | `pd.DataFrame \| None` | cached | Non-derivative transactions with codes `P` or `S` |
| `derivative_trades` | `DataHolder \| None` | cached | Derivative table's transactions wrapped in `DataHolder` |
| `common_stock_purchases` | `pd.DataFrame` | no | `market_trades` rows where `AcquiredDisposed == 'A'` |
| `common_stock_sales` | `pd.DataFrame` | no | `market_trades` rows where `AcquiredDisposed == 'D'` |
| `option_exercises` | `pd.DataFrame` | no | Non-derivative transactions with `TransactionType == 'Exercise'` |
| `shares_traded` | `int \| None` | cached | Sum of `market_trades.Shares` when all-numeric; else `None` |

### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `from_xml` | `content: str` | `Ownership` | classmethod; parses XML → instance |
| `parse_xml` | `content: str` | `dict` | classmethod; parses `<ownershipDocument>` XML → kwargs dict |
| `extract_form3_holdings` | — | `List[SecurityHolding]` | Combines non-derivative + derivative holdings; Form 3 focus |
| `get_transaction_activities` | — | `List[TransactionActivity]` | All market + non-market + derivative transactions; resolves footnotes |
| `get_ownership_summary` | — | `InitialOwnershipSummary \| TransactionSummary` | Form 3 → `InitialOwnershipSummary`; Form 4/5 → `TransactionSummary` |
| `to_dataframe` | `detailed: bool = True`, `include_metadata: bool = True` | `pd.DataFrame` | Delegates to `get_ownership_summary().to_dataframe()`. Note: `include_metadata` only takes effect when `detailed=True`; summary mode (`detailed=False`) always includes metadata |
| `to_context` | `detail: str = 'standard'` | `str` | AI context; `'minimal'` ~100 tokens, `'standard'` ~300, `'full'` ~500+ |
| `to_html` | — | `str` | Jinja2 SEC-style HTML via `ownership_to_html(self)` |

---

## Nested Objects

### Issuer

| Field | Type | Description |
|-------|------|-------------|
| `cik` | `IntString` | Issuer CIK from `<issuerCik>` |
| `name` | `str` | Issuer company name from `<issuerName>` |
| `ticker` | `str` | Trading symbol from `<issuerTradingSymbol>`; empty string if absent |

### Owner (frozen dataclass)

Source: `edgar/ownership/ownershipforms.py:931`

| Field | Type | Description |
|-------|------|-------------|
| `cik` | `str` | Owner CIK from `<rptOwnerCik>` |
| `is_company` | `Optional[bool]` | `True` if entity lookup determines company (vs individual); `None` if CIK lookup fails |
| `name` | `str` | Display name — reversed (First Last) if individual, unchanged if company |
| `name_unreversed` | `str` | Raw name from XML before reversal |
| `address` | `Address` | Street, city, state, zip from `<reportingOwnerAddress>` |
| `is_director` | `bool` | From `<isDirector>` |
| `is_officer` | `bool` | From `<isOfficer>` |
| `is_other` | `bool` | From `<isOther>` |
| `is_ten_pct_owner` | `bool` | From `<isTenPercentOwner>` |
| `officer_title` | `str \| None` | From `<officerTitle>`; replaced with `remarks` if value contains `"see remarks"` |

**`Owner` properties:**

| Property | Returns | Description |
|----------|---------|-------------|
| `position` | `str` | Human-readable role: officer_title if set, else derived from flags |

### Address (Pydantic model)

Source: `edgar/_party.py:25`

| Field | Type | Description |
|-------|------|-------------|
| `street1` | `Optional[str]` | Street line 1 |
| `street2` | `Optional[str]` | Street line 2 |
| `city` | `Optional[str]` | City |
| `state_or_country` | `Optional[str]` | State or country code |
| `state_or_country_description` | `Optional[str]` | Human-readable state/country |
| `zipcode` | `Optional[str]` | ZIP code |

### ReportingOwners

Source: `edgar/ownership/ownershipforms.py:977`

| Member | Type | Description |
|--------|------|-------------|
| `owners` | `List[Owner]` | Ordered list of `Owner` instances |
| `__getitem__` | `Owner` | Index access by integer |
| `__len__` | `int` | Count of owners |

### Footnotes

Source: `edgar/ownership/ownershipforms.py:285`

| Member | Type | Description |
|--------|------|-------------|
| `_footnotes` | `Dict[str, str]` | Internal dict; keys are footnote IDs (e.g. `"F1"`), values are text |
| `__getitem__(id)` | `str` | Direct access; raises `KeyError` if ID not found |
| `get(id, default)` | `Optional[str]` | Safe access with default |
| `summary()` | `pd.DataFrame` | DataFrame indexed by `id`, with column `footnote` |
| `__len__` | `int` | Number of footnotes |

### OwnerSignature

| Field | Type | Description |
|-------|------|-------------|
| `signature` | `str` | Signatory name from `<signatureName>` |
| `date` | `str` | Signature date from `<signatureDate>` |

### NonDerivativeTable

Source: `edgar/ownership/ownershipforms.py:604`

| Member | Type | Description |
|--------|------|-------------|
| `holdings` | `NonDerivativeHoldings` | DataHolder wrapping common stock static holdings DataFrame |
| `transactions` | `NonDerivativeTransactions` | DataHolder wrapping common stock transactions DataFrame |
| `form` | `str` | `"3"`, `"4"`, or `"5"` — controls rendering |
| `market_trades` | `pd.DataFrame \| None` | Rows with `Code in ('P', 'S')`; `None` if no transactions |
| `non_market_trades` | `pd.DataFrame \| None` | Rows with `Code not in ('P', 'S')` |
| `exercised_trades` | `pd.DataFrame \| None` | Rows where `TransactionType == 'Exercise'` |
| `has_holdings` | `bool` | `not self.holdings.empty` |
| `has_transactions` | `bool` | `not self.transactions.empty` |
| `empty` | `bool` | Both holdings and transactions empty |

### NonDerivativeHoldings (DataHolder subclass)

Source: `edgar/ownership/ownershipforms.py:447`

| Member | Description |
|--------|-------------|
| `data` | `pd.DataFrame` — see DataFrame schema below |
| `empty` | `bool` |
| `__len__` | row count |
| `__getitem__(int)` | Returns `NonDerivativeHolding` frozen dataclass |
| `summary()` | Filtered DataFrame with Shares, Direct, NatureOfOwnership, Security |

### NonDerivativeHolding (frozen dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `security` | `str` | Security title |
| `shares` | `str` | Shares owned; may be numeric string or `None` |
| `direct` | `bool` | `True` if direct ownership |
| `nature_of_ownership` | `str` | Ownership nature description |

### NonDerivativeTransactions (DataHolder subclass)

Source: `edgar/ownership/ownershipforms.py:544`

| Member | Description |
|--------|-------------|
| `data` | `pd.DataFrame` — see DataFrame schema below |
| `empty` | `bool` |
| `__len__` | row count |
| `__getitem__(int)` | Returns `NonDerivativeTransaction` frozen dataclass |
| `summary()` | Subset DataFrame: Date, Security, Shares (+/-), Remaining, Price |

### NonDerivativeTransaction (frozen dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `security` | `str` | Security title |
| `date` | `str` | Transaction date |
| `shares` | `int` | Number of shares |
| `remaining` | `int` | Shares owned after transaction |
| `price` | `float` | Price per share |
| `acquired_disposed` | `str` | `"A"` or `"D"` |
| `direct_indirect` | `str` | `"D"` or `"I"` |
| `form` | `str` | Form type |
| `transaction_code` | `str` | Raw code letter |
| `transaction_type` | `str` | Human-readable type from `TransactionCode.TRANSACTION_TYPES` |
| `equity_swap` | `str` | Equity swap flag |
| `footnotes` | `str` | Newline-separated footnote IDs |

### DerivativeTable

Source: `edgar/ownership/ownershipforms.py:766`

| Member | Type | Description |
|--------|------|-------------|
| `holdings` | `DerivativeHoldings` | DataHolder wrapping derivative static holdings DataFrame |
| `transactions` | `DerivativeTransactions` | DataHolder wrapping derivative transactions DataFrame |
| `form` | `str` | Form type — controls rendering |
| `derivative_trades` | `DataHolder \| None` | `DataHolder(transactions.data)` if has transactions |
| `has_holdings` | `bool` | `not self.holdings.empty` |
| `has_transactions` | `bool` | `not self.transactions.empty` |
| `empty` | `bool` | Both holdings and transactions empty |

### DerivativeHoldings (DataHolder subclass)

Source: `edgar/ownership/ownershipforms.py:407`

| Member | Description |
|--------|-------------|
| `data` | `pd.DataFrame` — see DataFrame schema below |
| `__getitem__(int)` | Returns `DerivativeHolding` frozen dataclass |
| `summary()` | Subset: Security, Underlying, Shares, Ex price, Ex date (renamed from UnderlyingShares, ExercisePrice, ExerciseDate) |

### DerivativeHolding (frozen dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `security` | `str` | Derivative security title |
| `underlying` | `str` | Underlying security title |
| `exercise_price` | `str` | Conversion/exercise price |
| `exercise_date` | `str` | Exercisable date |
| `expiration_date` | `str` | Expiration date |
| `underlying_shares` | `int` | Number of underlying shares |
| `direct_indirect` | `str` | `"D"` or `"I"` |
| `nature_of_ownership` | `str` | Ownership nature |

### DerivativeTransactions (DataHolder subclass)

Source: `edgar/ownership/ownershipforms.py:479`

| Member | Description |
|--------|-------------|
| `data` | `pd.DataFrame` — see DataFrame schema below |
| `__getitem__(int)` | Returns `DerivativeTransaction` frozen dataclass |
| `disposals` | Property — rows where `AcquiredDisposed == 'D'` |
| `acquisitions` | Property — rows where `AcquiredDisposed == 'A'` |
| `shares_disposed()` | Sum of disposed shares |
| `summary()` | Subset: Date, Security, Shares (+/-), Remaining, Price, Underlying. Date becomes the index |

### DerivativeTransaction (frozen dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `security` | `str` | Derivative security title |
| `underlying` | `str` | Underlying security title |
| `underlying_shares` | `str` | Number of underlying shares |
| `exercise_price` | `object` | Conversion/exercise price |
| `exercise_date` | `str` | Exercisable date |
| `expiration_date` | `str` | Expiration date |
| `shares` | `object` | Shares in transaction |
| `direct_indirect` | `str` | `"D"` or `"I"` |
| `price` | `str` | Transaction price per share |
| `acquired_disposed` | `str` | `"A"` or `"D"` |
| `date` | `str` | Transaction date |
| `remaining` | `str` | Derivative securities owned after transaction |
| `form` | `str` | Form type |
| `transaction_code` | `str` | Raw code letter |
| `equity_swap` | `str` | Equity swap flag |
| `footnotes` | `str` | Newline-separated footnote IDs |

### TransactionCode

Source: `edgar/ownership/ownershipforms.py:144`

| Member | Type | Description |
|--------|------|-------------|
| `form` | `str` | Form type |
| `code` | `str` | Single letter code |
| `equity_swap` | `bool` | Equity swap involved |
| `footnote` | `str` | Associated footnote |
| `description` | `str` (property) | Human-readable description from `DESCRIPTIONS` dict |

**Code → Description map:**

| Code | Description |
|------|-------------|
| `A` | Grant or award |
| `C` | Conversion of derivative |
| `D` | Disposition to the issuer |
| `E` | Expiration of short position |
| `F` | Payment of exercise price or tax |
| `G` | Gift |
| `H` | Expiration of long position |
| `I` | Disposition otherwise than to the issuer |
| `M` | Exercise or conversion of exempt derivative |
| `O` | Exercise of out-of-the-money derivative |
| `P` | Open market or private purchase |
| `S` | Open market or private sale |
| `U` | Disposition pursuant to a tender of shares |
| `X` | Exercise of in-the-money or at-the-money derivative |
| `Z` | Deposit or withdrawal from voting trust |

**`TRANSACTION_TYPES` map** (code → normalized type string used in `TransactionActivity.transaction_type`):

| Code | Type |
|------|------|
| `A` | `Award` |
| `C` | `Conversion` |
| `D` | `Disposition` |
| `E` | `Expiration` |
| `F` | `Tax Withholding` |
| `G` | `Gift` |
| `H` | `Expiration` |
| `I` | `Discretionary` |
| `J` | `Other` |
| `M` | `Exercise` |
| `O` | `Exercise` |
| `P` | `Purchase` |
| `S` | `Sale` |
| `U` | `Disposition` |
| `W` | `Willed` |
| `X` | `Exercise` |
| `Z` | `Trust` |

`TransactionCode.TRADES = ['P', 'S']` — codes used to filter `market_trades`.

### TransactionActivity (dataclass)

Source: `edgar/ownership/ownershipforms.py:1094`

| Field | Type | Description |
|-------|------|-------------|
| `transaction_type` | `str` | One of: `"purchase"`, `"sale"`, `"exercise"`, `"award"`, `"tax"`, `"gift"`, `"conversion"`, `"derivative_purchase"`, `"derivative_sale"`, `"other_acquisition"`, `"other_disposition"` |
| `code` | `str` | Raw transaction code letter |
| `shares` | `Any` | Share count; may be int, float, or footnote-embedded string |
| `value` | `Any` | Computed value (shares × price); `0` if price unavailable |
| `price_per_share` | `Any` | Price per share; `None` if unavailable |
| `description` | `str` | Optional description override |
| `security_type` | `str` | `"non-derivative"` or `"derivative"` |
| `security_title` | `str` | Security name |
| `underlying_security` | `str` | Underlying security for derivatives; empty string for non-derivative |
| `exercise_date` | `Optional[str]` | Exercise date for derivatives |
| `expiration_date` | `Optional[str]` | Expiration date for derivatives |
| `footnote_ids` | `str` | Newline-separated footnote IDs (e.g., `"F1\nF2"`) |
| `footnotes_text` | `str` | Resolved full text of all footnotes for this transaction |

**`TransactionActivity` properties:**

| Property | Returns | Description |
|----------|---------|-------------|
| `shares_numeric` | `Optional[int \| float]` | Safe numeric conversion of `shares`; strips footnote refs |
| `value_numeric` | `Optional[float]` | Safe numeric conversion of `value` |
| `price_numeric` | `Optional[float]` | Safe numeric conversion of `price_per_share` |
| `is_derivative` | `bool` | `security_type == "derivative"` |
| `is_10b5_1_plan` | `Optional[bool]` | Delegates to `detect_10b5_1_plan(footnotes_text)`; `None` if no footnotes |
| `code_description` | `str` | Verbose code description (e.g., `"Open Market Purchase"`) |
| `display_name` | `str` | Best human label: description > code_description with underlying |
| `style` | `str` | Rich terminal color string for display |

### SecurityHolding (dataclass)

Source: `edgar/ownership/ownershipforms.py:1064` — returned by `extract_form3_holdings()`

| Field | Type | Description |
|-------|------|-------------|
| `security_type` | `str` | `"non-derivative"` or `"derivative"` |
| `security_title` | `str` | Security name |
| `shares` | `int` | Non-derivative shares; `0` for derivative |
| `direct_ownership` | `bool` | `True` if `DirectIndirect == 'D'` |
| `ownership_nature` | `str` | Nature of ownership description |
| `underlying_security` | `str` | For derivatives — underlying title |
| `underlying_shares` | `int` | For derivatives — underlying share count |
| `exercise_price` | `Optional[float]` | For derivatives |
| `exercise_date` | `str` | For derivatives |
| `expiration_date` | `str` | For derivatives |

**Properties:**

| Property | Returns | Description |
|----------|---------|-------------|
| `ownership_description` | `str` | `"Direct"` or `"Indirect (nature)"` or `"Indirect"` |
| `is_derivative` | `bool` | `security_type == "derivative"` |

### OwnershipSummary (dataclass — base)

Source: `edgar/ownership/ownershipforms.py:1203`

| Field | Type | Description |
|-------|------|-------------|
| `reporting_date` | `Union[str, date]` | Reporting period |
| `issuer_name` | `str` | Issuer company name |
| `issuer_ticker` | `str` | Issuer ticker |
| `insider_name` | `str` | Owner name(s) |
| `position` | `str` | Owner role |
| `form_type` | `str` | `"3"`, `"4"`, or `"5"` |
| `remarks` | `str` | Filing remarks |

**Properties:**

| Property | Returns | Description |
|----------|---------|-------------|
| `issuer` | `str` | `"{issuer_name} ({issuer_ticker})"` |

### InitialOwnershipSummary (dataclass — Form 3)

Source: `edgar/ownership/ownershipforms.py:1238` — extends `OwnershipSummary`

| Field | Type | Description |
|-------|------|-------------|
| `holdings` | `List[SecurityHolding]` | All holdings — non-derivative + derivative |
| `no_securities` | `bool` | `True` if filed with no holdings |

**Properties:**

| Property | Returns | Description |
|----------|---------|-------------|
| `total_shares` | `int` | Sum of non-derivative `shares` |
| `has_derivatives` | `bool` | Any holding where `is_derivative == True` |

**Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `to_dataframe` | `include_metadata: bool = True` | `pd.DataFrame` | One row per holding; derivative rows include extra columns |
| `to_summary_dataframe` | — | `pd.DataFrame` | Single summary row with counts |

### TransactionSummary (dataclass — Form 4/5)

Source: `edgar/ownership/ownershipforms.py:1400` — extends `OwnershipSummary`

| Field | Type | Description |
|-------|------|-------------|
| `transactions` | `List[TransactionActivity]` | All activities from `get_transaction_activities()` |
| `remaining_shares` | `Optional[int]` | Shares owned after last transaction in filing |
| `has_derivative_transactions` | `bool` | Whether derivative table has transactions |

**Properties:**

| Property | Returns | Description |
|----------|---------|-------------|
| `transaction_types` | `List[str]` | Unique `transaction_type` values |
| `has_only_derivatives` | `bool` | All transactions are derivative |
| `has_non_derivatives` | `bool` | Any non-derivative transaction present |
| `has_10b5_1_plan` | `Optional[bool]` | `True` if any transaction is 10b5-1; `False` if footnotes exist but no plan; `None` if no footnotes |
| `net_change` | `int` | `purchases_shares - sales_shares` |
| `net_value` | `float` | `purchase_value - sale_value` |
| `primary_activity` | `str` | Dominant label: `"Purchase"`, `"Sale"`, `"Tax Withholding"`, `"Grant/Award"`, `"Option Exercise"`, `"Conversion"`, `"Mixed Transactions"`, `"DERIVATIVE TRANSACTIONS"`, `"DERIVATIVE ACQUISITION"`, `"DERIVATIVE DISPOSITION"`, `"DERIVATIVE TRANSACTION"`, `"No Transactions"`, or dynamic `.title()` of first transaction type as fallback |

**Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `to_dataframe` | `include_metadata: bool = True`, `detailed: bool = True` | `pd.DataFrame` | `detailed=True`: one row per transaction; `detailed=False`: single summary row |
| `to_summary_dataframe` | — | `pd.DataFrame` | Alias for `to_dataframe(detailed=False)` |

---

## DataFrame Schemas

### `non_derivative_table.holdings.data` columns

| Column | Type | Description |
|--------|------|-------------|
| `Security` | `str` | Security title |
| `Shares` | `numeric \| str` | Shares owned; converted to numeric if all-numeric |
| `Direct` | `str` | `"Yes"` or `"No"` |
| `NatureOfOwnership` | `str` | Nature of ownership description; empty string if direct |

### `non_derivative_table.transactions.data` columns

| Column | Type | Description |
|--------|------|-------------|
| `Security` | `str` | Security title |
| `Date` | `str` | Transaction date (`YYYY-MM-DD`) |
| `Shares` | `numeric` | Share count in transaction |
| `Remaining` | `numeric` | Shares owned after transaction |
| `Price` | `numeric` | Price per share |
| `AcquiredDisposed` | `str` | `"A"` (acquire) or `"D"` (dispose) |
| `DirectIndirect` | `str` | `"D"` or `"I"` |
| `NatureOfOwnership` | `str` | Nature description |
| `form` | `str` | Form type from `<transactionFormType>` |
| `Code` | `str` | Transaction code letter |
| `EquitySwap` | `bool` | Equity swap involved |
| `footnotes` | `str` | Newline-separated footnote IDs |
| `TransactionType` | `str` | Derived from `Code` via `TRANSACTION_TYPES` |

### `derivative_table.holdings.data` columns

| Column | Type | Description |
|--------|------|-------------|
| `Security` | `str` | Derivative security title |
| `Underlying` | `str` | Underlying security title |
| `UnderlyingShares` | `numeric` | Number of underlying shares |
| `ExercisePrice` | `str` | Conversion/exercise price |
| `ExerciseDate` | `str` | Date exercisable |
| `ExpirationDate` | `str` | Expiration date |
| `DirectIndirect` | `str` | `"D"` or `"I"` |
| `Nature Of Ownership` | `str` | Nature of ownership (note: column name has space) |

### `derivative_table.transactions.data` columns

| Column | Type | Description |
|--------|------|-------------|
| `Security` | `str` | Derivative security title |
| `Underlying` | `str` | Underlying security title |
| `UnderlyingShares` | `numeric` | Underlying shares |
| `ExercisePrice` | `numeric` | Conversion/exercise price |
| `ExerciseDate` | `str` | Date exercisable |
| `ExpirationDate` | `str` | Expiration date |
| `Shares` | `numeric` | Shares in transaction |
| `DirectIndirect` | `str` | `"D"` or `"I"` |
| `Price` | `numeric` | Transaction price |
| `AcquiredDisposed` | `str` | `"A"` or `"D"` |
| `Date` | `str` | Transaction date |
| `Remaining` | `numeric` | Derivative securities owned after transaction |
| `form` | `str` | Form type |
| `Code` | `str` | Transaction code letter |
| `EquitySwap` | `bool` | Equity swap involved |
| `footnotes` | `str` | Newline-separated footnote IDs |
| `TransactionType` | `str` | Derived from `Code` via `TRANSACTION_TYPES` |

### `Ownership.to_dataframe()` — detailed mode (Form 3)

Delegates to `InitialOwnershipSummary.to_dataframe(include_metadata)`.

| Column | Type | Notes |
|--------|------|-------|
| `Security Type` | `str` | `"Common Stock"` or `"Derivative"` |
| `Security Title` | `str` | |
| `Shares` | `numeric` | |
| `Ownership Type` | `str` | `"Direct"` or `"Indirect"` |
| `Ownership Nature` | `str` | |
| `Underlying Security` | `str` | Derivative rows only |
| `Underlying Shares` | `numeric` | Derivative rows only |
| `Exercise Price` | `numeric` | Derivative rows only |
| `Exercise Date` | `str` | Derivative rows only |
| `Expiration Date` | `str` | Derivative rows only |
| `Date` | `datetime` | When `include_metadata=True` |
| `Form` | `str` | e.g. `"Form 3"` — when `include_metadata=True` |
| `Issuer` | `str` | When `include_metadata=True` |
| `Ticker` | `str` | When `include_metadata=True` |
| `Insider` | `str` | When `include_metadata=True` |
| `Position` | `str` | When `include_metadata=True` |

### `Ownership.to_dataframe()` — detailed mode (Form 4/5)

Delegates to `TransactionSummary.to_dataframe(include_metadata, detailed=True)`.

| Column | Type | Notes |
|--------|------|-------|
| `Transaction Type` | `str` | Title-cased transaction type |
| `Code` | `str` | Raw code letter |
| `Description` | `str` | `display_name` from `TransactionActivity` |
| `Shares` | `Any` | May be numeric or original string |
| `Price` | `numeric` | `price_numeric` — `None` if unavailable |
| `Value` | `numeric \| None` | `None` if `value <= 0` |
| `Date` | `datetime` | When `include_metadata=True` |
| `Form` | `str` | When `include_metadata=True` |
| `Issuer` | `str` | When `include_metadata=True` |
| `Ticker` | `str` | When `include_metadata=True` |
| `Insider` | `str` | When `include_metadata=True` |
| `Position` | `str` | When `include_metadata=True` |
| `Remaining Shares` | `numeric \| None` | When `include_metadata=True` |

### `Ownership.to_dataframe()` — summary mode (Form 4/5)

Delegates to `TransactionSummary.to_dataframe(detailed=False)`.

| Column | Type | Notes |
|--------|------|-------|
| `Date` | `datetime` | |
| `Form` | `str` | |
| `Issuer` | `str` | |
| `Ticker` | `str` | |
| `Insider` | `str` | |
| `Position` | `str` | |
| `Remarks` | `str` | |
| `Transaction Count` | `int` | |
| `Net Change` | `int` | |
| `Net Value` | `float` | |
| `Remaining Shares` | `numeric \| None` | |
| `Primary Activity` | `str` | |
| `{Type} Count` | `int` | Dynamic; one per unique transaction type |
| `{Type} Shares` | `numeric` | Dynamic; one per unique transaction type |
| `{Type} Value` | `numeric` | Dynamic; only for `purchase` and `sale` types |
| `Avg {Type} Price` | `float` | Dynamic; only for `purchase` and `sale` types |

---

## Error Paths

| Condition | Behavior |
|-----------|----------|
| `parse_xml` called with no `<ownershipDocument>` root | Raises `ValueError("Could not find ownershipDocument in XML")` |
| `parse_xml` called with no `<issuer>` element | Raises `ValueError("Could not find issuer in XML")` |
| `market_trades` accessed when `non_derivative_table.transactions` is empty | Returns `None` |
| `shares_traded` when `market_trades.Shares` is non-numeric | Returns `None` |
| `to_context` when `get_ownership_summary()` raises | Silently sets `summary = None`; context still renders without transaction detail |
| `common_stock_purchases/sales` when `market_trades` is `None` | Returns empty `pd.DataFrame()` |
| `option_exercises` when `non_derivative_table` has no transactions | Returns empty `pd.DataFrame()` |
| Owner CIK lookup (`Entity(int(cik))`) fails | `is_company = None`; name is NOT reversed |

---

## Access Patterns

- `filing.obj()` → `Form3 | Form4 | Form5`
- `form3.non_derivative_table.holdings.data` — raw holdings DataFrame
- `form4.non_derivative_table.transactions.data` — raw transactions DataFrame
- `form4.market_trades` — open market buys/sells only
- `form4.get_transaction_activities()` — normalized `TransactionActivity` list with footnotes resolved
- `form4.get_ownership_summary()` → `TransactionSummary` → `.primary_activity`, `.net_change`, `.has_10b5_1_plan`
- `form3.get_ownership_summary()` → `InitialOwnershipSummary` → `.total_shares`, `.holdings`
- `form3.extract_form3_holdings()` → `List[SecurityHolding]` — merged non-derivative + derivative
- `form4.to_dataframe()` — one row per transaction with metadata
- `form4.to_dataframe(detailed=False)` — single summary row
- `form4.to_context(detail='full')` — AI-optimized context with 10b5-1 flag

---

## Gotchas

| Issue | Detail |
|-------|--------|
| `ReportingOwners` triggers live network call | `Entity(int(cik))` per owner to detect company vs individual for name reversal; can fail or slow for unusual CIKs |
| `officer_title` with `"see remarks"` | Replaced with the filing's `remarks` field |
| `footnote_id` as `AttributeValueList` | BeautifulSoup quirk — all extraction code takes `[0]` defensively |
| `has_10b5_1_plan` three-value return | `None` = no footnotes at all; `False` = footnotes exist but no plan; `True` = plan detected |
| Form 3 `no_securities = True` | Valid filing state — Form 3 can be filed with zero holdings |
| `Nature Of Ownership` column name | Derivative holdings DataFrame uses a space in the column name; non-derivative uses `NatureOfOwnership` |
| `shares_traded` returns `None` not `0` | When shares are non-numeric (footnote references embedded in values) |
