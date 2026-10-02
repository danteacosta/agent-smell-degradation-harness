'use strict';
// Executes one generated browser test suite against one frozen artifact.
// Mirrors the case runners: the artifact is served at http://localhost/ with
// the same CSP and no network; each test gets a fresh context.
const fs = require('node:fs');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const { chromium } = require('playwright');

const html = fs.readFileSync('/input/app.html');
const URL = 'http://localhost/';
const CSP = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const report = {
  schema_version: 'test-anchor-execution/v1',
  status: 'runner_error',
  app_sha256: crypto.createHash('sha256').update(html).digest('hex'),
  suite_sha256: crypto.createHash('sha256').update(fs.readFileSync('/input/suite.cjs')).digest('hex'),
  tests: [],
};

function withTimeout(promise, ms) {
  let timer;
  return Promise.race([
    promise,
    new Promise((_, reject) => { timer = setTimeout(() => reject(new Error(`test timeout after ${ms} ms`)), ms); }),
  ]).finally(() => clearTimeout(timer));
}

(async () => {
  let browser;
  try {
    let suite;
    try {
      suite = require('/input/suite.cjs');
    } catch (error) {
      report.status = 'suite_invalid';
      report.error = String(error).slice(0, 1500);
      return;
    }
    const tests = suite && Array.isArray(suite.tests) ? suite.tests : null;
    if (!tests || tests.length === 0 || tests.length > 12
        || tests.some(t => !t || typeof t.name !== 'string' || typeof t.run !== 'function')) {
      report.status = 'suite_invalid';
      report.error = 'module.exports.tests must be 1-12 {name, run} entries';
      return;
    }
    browser = await chromium.launch({ headless: true, chromiumSandbox: false });
    for (const test of tests) {
      const context = await browser.newContext({ viewport: { width: 1000, height: 720 }, timezoneId: 'UTC', serviceWorkers: 'block' });
      const row = { name: test.name.slice(0, 200), outcome: 'pass' };
      try {
        await context.route('**/*', route => (route.request().url() === URL && route.request().isNavigationRequest()
          ? route.fulfill({ body: html, contentType: 'text/html', headers: { 'Content-Security-Policy': CSP } })
          : route.abort()));
        const page = await context.newPage();
        page.setDefaultTimeout(2500);
        await withTimeout(test.run({ context, page, url: URL, assert }), 20000);
      } catch (error) {
        row.outcome = error instanceof assert.AssertionError ? 'assertion_failure' : 'error';
        row.message = String(error && error.message || error).slice(0, 800);
      } finally {
        await context.close();
      }
      report.tests.push(row);
    }
    report.status = 'complete';
  } catch (error) {
    report.status = 'runner_error';
    report.error = String(error).slice(0, 1500);
  } finally {
    if (browser) await browser.close();
    fs.writeFileSync('/output/report.json', JSON.stringify(report, null, 2));
    process.exitCode = report.status === 'complete' ? 0 : 2;
  }
})();
