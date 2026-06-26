# edgar-sidecar

Single SEC egress. Wraps edgartools as a stateless HTTP/JSON API with generated Zod types for TypeScript consumers.

## Run it

```bash
# Docker (from the fork root, one level up)
docker build -f sidecar/Dockerfile -t edgar-sidecar .
docker run -p 8000:8000 -e SEC_EDGAR_USER_AGENT="YourName contact@example.com" edgar-sidecar

# Compose (from fork root)
SEC_EDGAR_USER_AGENT="YourName contact@example.com" docker compose -f sidecar/compose.yaml up

# Bare (from sidecar/)
uv sync && SEC_EDGAR_USER_AGENT="YourName contact@example.com" uv run uvicorn app.main:app --reload
```

## Endpoints

| Path | What you get |
|------|-------------|
| `GET /health` | Status, edgartools version, identity check |
| `GET /company/{id}` | Company profile by ticker, CIK, or name |
| `GET /company/{id}/submissions` | Full filing history with pagination |
| `GET /company/{id}/facts` | All XBRL facts for the entity |
| `GET /company/{id}/facts/concept/{concept}` | Single concept timeseries (e.g. `us-gaap:Revenue`) |
| `GET /company/{id}/facts/search` | Full-text search across entity facts |
| `GET /company/{id}/financials` | Income/balance/cashflow from latest 10-K |
| `GET /company/{id}/financials/multi` | Multi-period financial comparison |
| `GET /company/{id}/financials/ttm` | Trailing twelve months |
| `GET /company/{id}/financials/metrics` | Derived ratios and metrics |
| `GET /filing/{accession}` | Filing envelope + typed `data` (see form coverage below) |
| `GET /filing/{accession}/content` | Rendered markdown/HTML/text of the filing |
| `GET /filing/{accession}/sections` | Detected document sections (TOC) |
| `GET /filing/{accession}/attachments` | Attachment listing with metadata |
| `GET /filing/{accession}/attachments/{seq}` | Single attachment content |
| `GET /filing/{accession}/xbrl` | XBRL financial statements (if present) |
| `GET /filings` | Filing search by form, date range, CIK |
| `GET /filings/current` | Latest filings feed |
| `GET /search` | Full-text EDGAR EFTS search |
| `GET /tickers` | SEC ticker-to-CIK mapping |

`{id}` accepts ticker (`AAPL`), CIK (`0000320193`), or company name.

## Filing `data`: what each form gives you

`GET /filing/{accession}` returns a `FilingEnvelope` with a `data` field. `data` is a discriminated union on `data.kind` -- narrow it to get the typed form. Unsupported forms return `data: null` with the envelope still populated.

### Corporate filings

| kind | Forms | What's in the data |
|------|-------|-------------------|
| `form10k` | 10-K +/A | Items (business, risk factors, MD&A, financial statements), auditor info, exhibits, XBRL-linked financials |
| `form10q` | 10-Q +/A | Quarterly items, MD&A, financial statements, amendment metadata |
| `form20f` | 20-F +/A | Foreign issuer annual: business overview, risk factors, financial disclosures, exhibits |
| `form40f` | 40-F +/A | Canadian MJDS annual: AIF sections (business, risk, MD&A), exhibits |
| `form8k` | 8-K +/A | Current report items (by SEC item number), exhibits, press release detection |
| `form6k` | 6-K +/A | Foreign issuer current report: items, exhibits |

### Ownership and governance

| kind | Forms | What's in the data |
|------|-------|-------------------|
| `ownership` | 3, 4, 5 +/A | Insider transactions: issuer, owner(s), non-derivative holdings, derivative holdings, footnotes, each with per-row detail |
| `proxy` | DEF 14A and 11 variants | Executive compensation (PVP XBRL), summary comp table, director comp, voting proposals, pay ratio, audit fees, beneficial ownership |
| `sc13d` | SC 13D +/A | Beneficial ownership >5%: filers, CUSIP, class of securities, aggregate amount, percent of class, purpose |
| `sc13g` | SC 13G +/A | Passive beneficial ownership: same structure as 13D, passive/institutional/exempt classification |

### Offerings and registrations

| kind | Forms | What's in the data |
|------|-------|-------------------|
| `registration_s1` | S-1, F-1 +/A | IPO registration: cover page, fee table, selling stockholders, underwriting, dilution, capitalization |
| `registration_s3` | S-3, S-3ASR, S-3D, S-3DPOS, F-3, F-3ASR +/A | Shelf registration: cover page, fee table, auto-shelf flag |
| `drs` | DRS +/A | Draft registration wrapper: underlying_form detection, nested S-1 or S-3 data (discriminated union within the union) |
| `prospectus_424b` | 424B1-B8 +/A | Priced prospectus: cover, pricing, offering terms, structured note terms, filing fees (XBRL), selling stockholders, underwriting |
| `prospectus_497k` | 497K +/A | Fund summary prospectus: fund identity, share classes with fees and expense examples, performance returns |
| `form144` | 144 +/A | Rule 144 proposed sale: security rows, analytical flags (cooling-off compliance, 10b5-1 plan, large liquidation) |
| `formd` | D +/A | Reg D exempt offering: issuer(s), related persons with roles, full offering block (industry, amounts, investors, sales compensation), signatures |
| `formc` | C, C-U, C-AR, C-TR +/A | Regulation Crowdfunding: offering terms, issuer financials, annual report figures, use of proceeds |
| `effect` | EFFECT | Effectiveness notice: effective date, source form type, source accession, filer identity |

### Institutional holdings

| kind | Forms | What's in the data |
|------|-------|-------------------|
| `form13f` | 13F-HR, 13F-NT +/A | Institutional holdings: info table with CUSIP, issuer, class, market value, shares, investment discretion, voting authority |

### Fund reports

| kind | Forms | What's in the data |
|------|-------|-------------------|
| `nport` | NPORT-P, NPORT-EX +/A | Fund portfolio: header, general info, fund info, full investment list with derivative sub-records (forwards, swaps, futures, options, swaptions) |
| `nmfp` | N-MFP2, N-MFP3 +/A | Money market fund: general info, series info, share classes, securities with ratings and repo agreements (collateral nesting) |
| `ncen` | N-CEN +/A | Fund census: registrant governance, deep per-series tree (providers, brokers, principal transactions, securities lending, line of credit, ETF info with authorized participants) |
| `ncsr` | N-CSR, N-CSRS +/A | Shareholder report (Inline XBRL): per-fund net assets, portfolio turnover, advisory fees, per-class expense ratios, average annual returns by horizon and load treatment |
| `npx` | N-PX +/A | Proxy voting record: per-matter votes (issuer, CUSIP, meeting date, description, how voted, management recommendation, vote categories). Large fund families produce thousands of records. |

Every form kind has golden fixtures, all Zod-strict validated.

## TypeScript consumer wiring

Generated Zod schemas: `sidecar/ts/src/generated/zod.ts`

Copy into your project or import directly:

```typescript
import { GetFilingFilingAccessionGetResponse } from './generated/edgar-sidecar.zod';

const envelope = GetFilingFilingAccessionGetResponse.parse(response.data);

// Narrow the discriminated union
if (envelope.data?.kind === 'form10k') {
  // envelope.data is now TenKData -- full type safety
  const auditor = envelope.data.auditor;
  const items = envelope.data.items;
}
```

Regenerate after model changes:

```bash
cd sidecar && uv run python -m scripts.export_openapi
cd ts && bun run generate
```

## Compose integration (downstream consumers)

```yaml
services:
  edgar:
    build:
      context: /path/to/edgartools   # fork root, not sidecar/
      dockerfile: sidecar/Dockerfile
    ports:
      - "8000:8000"
    environment:
      SEC_EDGAR_USER_AGENT: "YourName contact@example.com"
      EDGAR_RATE_LIMIT_PER_SEC: 8
```

The sidecar is stateless -- no DB, no Redis, no auth. It sits on the compose network and serves parsed SEC data.

## Development

```bash
cd sidecar
uv sync                                    # install
uv run uvicorn app.main:app --reload       # dev server :8000
uv run pytest tests/ -x                    # Python integration + parity + unit
cd ts && bun test                          # Zod strict-parse every golden
uv run pyright app/                        # type check
bash scripts/check_drift.sh               # openapi + zod sync gate
```

## Environment

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `SEC_EDGAR_USER_AGENT` | Yes | -- | SEC-mandated identity (e.g. `"Name contact@example.com"`) |
| `EDGAR_IDENTITY` | No | `SEC_EDGAR_USER_AGENT` | Alternate identity key |
| `EDGAR_RATE_LIMIT_PER_SEC` | No | `8` | SEC request throttle |
| `EDGAR_PORT` | No | `8000` | Container listen port |
