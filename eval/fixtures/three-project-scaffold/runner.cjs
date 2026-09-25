'use strict';

const fs = require('node:fs');
const crypto = require('node:crypto');
const {chromium} = require('playwright');

const html = fs.readFileSync('/input/app.html');
const config = JSON.parse(fs.readFileSync('/input/case.json', 'utf8'));
const URL = 'http://fixture.invalid/';
const CSP = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const report = {
  schema_version: 'three-project-fixed-scaffold-browser/v1',
  project_id: config.project_id,
  status: 'browser_error',
  app_sha256: crypto.createHash('sha256').update(html).digest('hex'),
  assertions: {},
  console_errors: [],
};

class InterfaceError extends Error {}
async function one(page, selector) {
  const locator = page.locator(selector);
  if (await locator.count() !== 1 || !await locator.isVisible()) {
    throw new InterfaceError(`one visible ${selector} required`);
  }
  return locator;
}

async function runPaperless(page) {
  await one(page, '[data-document-id="document-control"]');
  report.assertions.existing_document_visible = true;
  const upload = await one(page, 'button[aria-label="Upload document"]');
  await upload.click();
  report.assertions.upload_creates_document = await page.locator('[data-document-id]', {hasText: 'Selected.pdf'}).count() === 1;
  await page.evaluate(() => {
    const transfer = new DataTransfer();
    transfer.items.add(new File(['bounded'], 'Invoice.pdf', {type: 'application/pdf'}));
    document.body.dispatchEvent(new DragEvent('dragover', {bubbles: true, cancelable: true, dataTransfer: transfer}));
    document.body.dispatchEvent(new DragEvent('drop', {bubbles: true, cancelable: true, dataTransfer: transfer}));
  });
  await page.waitForTimeout(50);
  report.assertions.drop_creates_document = await page.locator('[data-document-id]', {hasText: 'Invoice.pdf'}).count() === 1;
}

async function runNextcloud(page) {
  const target = await one(page, '[data-file-id="file-target"]');
  await target.getByRole('button', {name: 'Delete', exact: true}).click();
  report.assertions.deleted_absent_from_all = await page.locator('[data-file-id="file-target"]').count() === 0;
  report.assertions.unrelated_file_unchanged = await page.locator('[data-file-id="file-control"]').count() === 1;
  await page.getByRole('button', {name: 'Deleted files', exact: true}).click();
  const deleted = page.locator('[data-file-id="file-target"]');
  report.assertions.deleted_visible_in_trash = await deleted.count() === 1 && await deleted.isVisible();
  if (report.assertions.deleted_visible_in_trash) {
    await deleted.getByRole('button', {name: 'Restore', exact: true}).click();
  }
  await page.getByRole('button', {name: 'All files', exact: true}).click();
  report.assertions.restore_returns_to_all = report.assertions.deleted_visible_in_trash && await page.locator('[data-file-id="file-target"]').count() === 1;
}

async function runOpenProject(page) {
  const work = await one(page, '[aria-label="Work"]');
  await work.fill('8');
  await page.getByRole('button', {name: 'Save', exact: true}).click();
  report.assertions.work_preserved = await work.inputValue() === '8';
  report.assertions.remaining_matches_work = await (await one(page, '[aria-label="Remaining Work"]')).inputValue() === '8';
  report.assertions.percent_zero = /^(?:0|0%)$/.test(await (await one(page, '[aria-label="% Complete"]')).inputValue());
}

(async () => {
  let browser;
  try {
    if (!['paperless-ngx', 'nextcloud', 'openproject'].includes(config.project_id)) throw new InterfaceError('unsupported project_id');
    browser = await chromium.launch({headless: true, chromiumSandbox: false});
    const context = await browser.newContext({viewport: {width: 1000, height: 720}, timezoneId: 'UTC', serviceWorkers: 'block'});
    await context.addInitScript(project => {
      if (project === 'paperless-ngx') Object.defineProperty(window, 'initialState', {value: {documents: [{id: 'document-control', title: 'Existing.pdf'}]}});
      if (project === 'nextcloud') Object.defineProperty(window, 'initialState', {value: {files: [{id: 'file-target', name: 'Project Plan.md'}, {id: 'file-control', name: 'Budget.csv'}]}});
    }, config.project_id);
    await context.route('**/*', route => route.request().url() === URL && route.request().isNavigationRequest()
      ? route.fulfill({body: html, contentType: 'text/html', headers: {'Content-Security-Policy': CSP}})
      : route.abort());
    const page = await context.newPage();
    page.setDefaultTimeout(2500);
    page.on('console', message => {if (message.type() === 'error' && report.console_errors.length < 20) report.console_errors.push(message.text().slice(0, 500));});
    page.on('pageerror', error => {if (report.console_errors.length < 20) report.console_errors.push(String(error).slice(0, 500));});
    await page.goto(URL, {waitUntil: 'load', timeout: 10000});
    await page.waitForTimeout(100);
    if (config.project_id === 'paperless-ngx') await runPaperless(page);
    if (config.project_id === 'nextcloud') await runNextcloud(page);
    if (config.project_id === 'openproject') await runOpenProject(page);
    await page.screenshot({path: '/output/final.png', fullPage: true});
    report.status = 'complete';
    report.screenshot = 'final.png';
    await context.close();
  } catch (error) {
    report.status = error instanceof InterfaceError ? 'interface_error' : 'browser_error';
    report.assertions = {};
    report.error = String(error).slice(0, 1500);
  } finally {
    if (browser) await browser.close();
    fs.writeFileSync('/output/report.json', JSON.stringify(report, null, 2));
    process.exitCode = report.status === 'complete' ? 0 : 2;
  }
})();
