# Form XML — Generic XML Filing

**SEC form codes**: X-17A-5, TA-1, TA-2, TA-W, MA, MA-W, CFPORTAL, SBSE, SBSE-A, SBSE-W, ATS-N-C (and /A amendment variants for each — 22 codes total)
**Python class**: `XmlFiling` (no base class)
**Access**: `filing.obj()` → `XmlFiling` (fallback for XML-native forms with no dedicated parser)
**Base fields**: See `_base-filing.md`
**Source**: `edgar/xmlfiling.py`

## Complete Field Reference

### From Filing (inherited)
See `_base-filing.md`

### XmlFiling-Specific Fields

#### Properties

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `filing` | `Filing` | no | Underlying Filing object |
| `form` | `str` | no | Full form string including `/A` if amendment |
| `base_form` | `str` | no | Form without `/A` suffix, e.g. `'X-17A-5'` |
| `company` | `str` | no | Filer company name from `_filing.company` |
| `filing_date` | any | no | Filing date from `_filing.filing_date` |
| `accession_number` | `str` | no | From `_filing.accession_no` |
| `is_amendment` | `bool` | no | True when `'/A'` in `_filing.form` |
| `form_data` | `dict` | no | `formData` XML element as nested dict; `{}` if not found |
| `header_data` | `dict` | no | `headerData` XML element as nested dict; `{}` if not found |
| `description` | `str` | no | Human-readable form type string from `_FORM_DESCRIPTIONS`; falls back to `form` |

#### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `from_filing` | `filing: Filing` | `Optional[XmlFiling]` | Classmethod. Parses XML, strips namespaces, converts to nested dict. Returns None on failure. |
| `__getitem__` | `key: str` | `Any` | Deep recursive key search in `form_data`; returns first match or None |
| `get` | `key: str, default: Any = None` | `Any` | Deep key lookup with default value |
| `to_html` | — | `Optional[str]` | Fetches SEC XSLT-rendered HTML. Network call. Returns None on error or unknown form. |
| `to_context` | `detail: str = 'standard'` | `str` | AI context. `'minimal'`: identity only. `'standard'`: + top-level form_data keys. `'full'`: + available actions. |

## Form Descriptions

| Form Code | Description |
|-----------|-------------|
| `X-17A-5` | Broker-Dealer Financial Report |
| `TA-1` | Transfer Agent Registration |
| `TA-2` | Transfer Agent Annual Report |
| `TA-W` | Transfer Agent Withdrawal |
| `MA` | Municipal Advisor Firm Registration |
| `MA-W` | Municipal Advisor Withdrawal |
| `CFPORTAL` | Crowdfunding Portal Registration |
| `SBSE` | Security-Based Swap Entity Registration |
| `SBSE-A` | Security-Based Swap Entity Registration (Annual) |
| `SBSE-W` | Security-Based Swap Entity Withdrawal |
| `ATS-N-C` | ATS Cessation of Operations |

`XML_FILING_FORMS` includes all of the above plus their `/A` amendment variants (built dynamically from `_XSLT_PREFIXES` keys).

## XSLT Rendering Pipeline

| Step | Detail |
|------|--------|
| XSLT prefix lookup | `_XSLT_PREFIXES[base_form]` → e.g. `'xslX-17A-5_X01'` |
| URL pattern | `https://www.sec.gov/Archives/edgar/data/{cik}/{acc_no_dashes}/{prefix}/primary_doc.xml` |
| Network call | `httpx.get(url, timeout=15, follow_redirects=True)` |
| Success | Returns HTML string from `resp.text` when `status_code == 200` |
| Failure | Returns None on HTTP error, network error, or missing XSLT prefix |

## XML Parsing — `_element_to_dict` behavior

| Input | Output |
|-------|--------|
| Leaf element with text | `str` value |
| Leaf element without text | `None` |
| Element with children | `dict` keyed by child tag names |
| Repeated sibling tags (first occurrence) | Scalar value |
| Repeated sibling tags (second occurrence) | Coalesced to `list` |
| Namespace prefixes | Stripped by `_strip_namespaces()` before conversion |

The type of any `form_data` field depends on how many times the tag appears in the XML. Fields that are always singletons are scalars; repeating fields are lists. This is filing-dependent.

## `_deep_get` — key lookup behavior

- Searches `form_data` dict recursively, depth-first
- Returns first match found anywhere in the tree
- Returns None if key not found (not raising `KeyError`)
- Traverses into nested dicts and lists of dicts
- `__getitem__` calls `_deep_get`; `get()` wraps it with a default

## Error Paths

| Condition | Behavior |
|-----------|----------|
| `filing.xml()` returns None | `from_filing` returns None |
| XML parse fails (lxml) | `from_filing` returns None; logs at debug level |
| `formData` element not found | `form_data` is `{}` |
| `headerData` element not found | `header_data` is `{}` |
| `base_form` not in `_XSLT_PREFIXES` | `to_html()` returns None immediately |
| HTTP error from SEC XSLT endpoint | `to_html()` returns None; logs at debug level |
| Key not in `form_data` tree | `__getitem__` returns None; `get()` returns default |

## Access Patterns

- `filing.obj()` → `XmlFiling` for any form in `XML_FILING_FORMS`
- `xf['fieldName']` — deep key lookup; field names vary by form type
- `xf.form_data.keys()` — inspect top-level XML sections
- `xf.to_html()` — SEC-rendered HTML; network call, 15s timeout, returns None on failure
- `xf.is_amendment` — quick check without parsing form string manually
- `xf.description` — human-readable label from `_FORM_DESCRIPTIONS`; useful for display
- `xf.header_data` — submission metadata (filer info, dates) separate from form content
- For TA-1/TA-2, MA, CFPORTAL etc.: form_data structure mirrors the SEC XML schema for each form type; field names are form-specific and not standardized across types
