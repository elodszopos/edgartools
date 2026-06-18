# Form Field Reference Index

Per-form field reference for every typed data object returned by `filing.obj()`. Each doc is self-contained — an agent reads ONE file to know every field available on that form type.

Structure: 4 base docs (inherited field sets) + 33 per-form docs.

## How to use

1. Identify the SEC form code (e.g., "10-K", "4", "DEF 14A")
2. Find the per-form doc below
3. Read the per-form doc for form-specific fields
4. Read the referenced base doc(s) for inherited fields

## Base Docs (Inherited Field Sets)

_base-filing                  Fields on every Filing object (all 28 form types inherit these)
_base-company-report          Fields shared by TenK, TenQ, EightK, TwentyF, FortyF
_base-ownership               Fields shared by Form3, Form4, Form5
_base-beneficial-ownership    Fields shared by Schedule13D, Schedule13G

## Tier 1 — Core Financial Intelligence

form-4                        Insider transactions (Form 4) — extends Ownership
form-10k                      Annual report (10-K) — extends CompanyReport
form-10q                      Quarterly report (10-Q) — extends CompanyReport
form-8k                       Current report / material events (8-K) — extends CompanyReport
form-def14a                   Proxy statement (DEF 14A, 30 form codes) — standalone
form-13f                      Institutional holdings (13F-HR) — standalone
form-sc13d                    Activist beneficial ownership (SC 13D) — extends beneficial-ownership base

## Tier 2 — Regular Use

form-sc13g                    Passive beneficial ownership (SC 13G) — extends beneficial-ownership base
form-3                        Initial insider ownership (Form 3) — extends Ownership
form-5                        Annual insider summary (Form 5) — extends Ownership
form-20f                      Foreign annual report (20-F) — extends CompanyReport
form-40f                      Canadian MJDS annual report (40-F) — extends CompanyReport
form-6k                       Foreign current report (6-K) — standalone (NOT CompanyReport)
form-s1                       IPO registration (S-1, F-1) — standalone
form-s3                       Shelf registration (S-3, F-3, ASR) — standalone
form-424b                     Prospectus (424B1-B8) — standalone
form-nport                    Fund portfolio holdings (NPORT-P) — standalone
form-144                      Restricted stock sale notice — standalone

## Tier 3 — Specialized

form-c                        Crowdfunding offering (Form C, Reg CF) — standalone
form-d                        Private placement (Form D) — standalone
form-effect                   Effectiveness notice (EFFECT) — standalone
form-drs                      Draft registration statement — standalone
form-npx                      Fund proxy voting record (N-PX) — standalone
form-nmfp                     Money market fund (N-MFP2/3) — standalone
form-ncen                     Fund annual census (N-CEN) — standalone
form-ncsr                     Fund shareholder report (N-CSR) — standalone
form-497k                     Fund summary prospectus (497K) — standalone
form-24f2nt                   Fund annual fee notice (24F-2NT) — standalone
form-correspondence           SEC correspondence (CORRESP, UPLOAD) — standalone
form-mai                      Municipal advisor individual (MA-I) — standalone
form-atsn                     Alternative trading system (ATS-N) — standalone
form-10d                      ABS distribution report (10-D) — standalone
form-xml                      Generic XML filing (22 form codes) — standalone
