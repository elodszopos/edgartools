/**
 * Every golden under fixtures/responses/<endpoint>/<case>.json must strict-parse with the
 * generated Zod schema for that endpoint. An endpoint dir with no schema mapping FAILS the
 * suite - goldens can never silently skip validation (plan: test architecture, TS leg).
 */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, test } from 'bun:test';
import type { z } from 'zod';
import {
  ErrorResponse,
  GetAttachmentContentFilingAccessionAttachmentsSequenceGetResponse,
  GetCompanyCompanyIdGetResponse,
  GetCompanyFinancialMetricsCompanyIdFinancialsMetricsGetResponse,
  GetCompanyFinancialsCompanyIdFinancialsGetResponse,
  GetCompanyFinancialsMultiCompanyIdFinancialsMultiGetResponse,
  GetCompanyFinancialsTtmCompanyIdFinancialsTtmGetResponse,
  GetCompanySubmissionsCompanyIdSubmissionsGetResponse,
  GetFilingContentFilingAccessionContentGetResponse,
  GetFilingFilingAccessionGetResponse,
  GetFilingSectionsFilingAccessionSectionsGetResponse,
  HealthHealthGetResponse,
  ListAttachmentsFilingAccessionAttachmentsGetResponse,
  ListCurrentFilingsFilingsCurrentGetResponse,
  ListFilingsFilingsGetResponse,
  ListTickersTickersGetResponse,
  SearchSearchGetResponse,
} from '../src/generated/zod';

const FIXTURES = join(import.meta.dir, '..', 'fixtures', 'responses');

// endpoint dir name -> generated response schema; extend with every new endpoint
const RESPONSE_SCHEMAS: Record<string, z.ZodType> = {
  // not an endpoint dir: canonical error bodies, one golden per error mechanism
  errors: ErrorResponse,
  health: HealthHealthGetResponse,
  company: GetCompanyCompanyIdGetResponse,
  company_financials: GetCompanyFinancialsCompanyIdFinancialsGetResponse,
  company_financials_metrics: GetCompanyFinancialMetricsCompanyIdFinancialsMetricsGetResponse,
  company_financials_multi: GetCompanyFinancialsMultiCompanyIdFinancialsMultiGetResponse,
  company_financials_ttm: GetCompanyFinancialsTtmCompanyIdFinancialsTtmGetResponse,
  company_submissions: GetCompanySubmissionsCompanyIdSubmissionsGetResponse,
  filing: GetFilingFilingAccessionGetResponse,
  filing_attachment_content: GetAttachmentContentFilingAccessionAttachmentsSequenceGetResponse,
  filing_attachments: ListAttachmentsFilingAccessionAttachmentsGetResponse,
  filing_content: GetFilingContentFilingAccessionContentGetResponse,
  filing_sections: GetFilingSectionsFilingAccessionSectionsGetResponse,
  filings: ListFilingsFilingsGetResponse,
  filings_current: ListCurrentFilingsFilingsCurrentGetResponse,
  search: SearchSearchGetResponse,
  tickers: ListTickersTickersGetResponse,
};

const endpoints = readdirSync(FIXTURES).filter((entry) => statSync(join(FIXTURES, entry)).isDirectory());

test('at least one golden endpoint exists', () => {
  expect(endpoints.length).toBeGreaterThan(0);
});

for (const endpoint of endpoints) {
  describe(endpoint, () => {
    test('has a response schema mapping', () => {
      expect(RESPONSE_SCHEMAS[endpoint], `add ${endpoint} to RESPONSE_SCHEMAS in goldens.test.ts`).toBeDefined();
    });

    const schema = RESPONSE_SCHEMAS[endpoint];
    if (schema) {
      const cases = readdirSync(join(FIXTURES, endpoint)).filter((f) => f.endsWith('.json'));
      test('has at least one golden case', () => {
        expect(cases.length).toBeGreaterThan(0);
      });

      for (const file of cases) {
        test(`${file} strict-parses`, () => {
          const payload: unknown = JSON.parse(readFileSync(join(FIXTURES, endpoint, file), 'utf-8'));
          const result = schema.safeParse(payload);
          if (!result.success) {
            throw new Error(`golden ${endpoint}/${file} rejected by generated Zod:\n${result.error.message}`);
          }
        });
      }
    }
  });
}
