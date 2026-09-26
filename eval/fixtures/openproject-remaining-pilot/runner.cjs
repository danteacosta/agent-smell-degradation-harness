'use strict';

const fs = require('node:fs');
const crypto = require('node:crypto');
const {chromium} = require('playwright');

const html = fs.readFileSync('/input/app.html');
const URL = 'http://fixture.invalid/';
const CSP = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures = [
  {work: '10', percent: '40', remaining: '6'},
  {work: '20', percent: '25', remaining: '15'},
];
const report = {
  schema_version: 'openproject-remaining-browser/v1', status: 'browser_error',
  app_sha256: crypto.createHash('sha256').update(html).digest('hex'),
  assertions: {}, console_errors: [],
};

class InterfaceError extends Error {}
async function one(page, selector) {
  const locator = page.locator(selector);
  if (await locator.count() !== 1 || !await locator.isVisible()) {
    throw new InterfaceError(`one visible ${selector} required`);
  }
  return locator;
}

async function runFixture(browser, fixture, index) {
  const context = await browser.newContext({viewport: {width: 1000, height: 720}, timezoneId: 'UTC', serviceWorkers: 'block'});
  try {
    await context.addInitScript(initial => {
      Object.defineProperty(window, 'initialState', {value: initial});
    }, {work: fixture.work, remaining: '', percent: ''});
    await context.route('**/*', route => route.request().url() === URL && route.request().isNavigationRequest()
      ? route.fulfill({body: html, contentType: 'text/html', headers: {'Content-Security-Policy': CSP}})
      : route.abort());
    const page = await context.newPage();
    page.setDefaultTimeout(2500);
    page.on('console', message => {if (message.type() === 'error' && report.console_errors.length < 20) report.console_errors.push(message.text().slice(0, 500));});
    page.on('pageerror', error => {if (report.console_errors.length < 20) report.console_errors.push(String(error).slice(0, 500));});
    await page.goto(URL, {waitUntil: 'load', timeout: 10000});
    const work = await one(page, '[aria-label="Work"]');
    const remaining = await one(page, '[aria-label="Remaining work"]');
    const percent = await one(page, '[aria-label="% Complete"]');
    if (await work.inputValue() !== fixture.work || await remaining.inputValue() !== '' || await percent.inputValue() !== '') {
      throw new InterfaceError('fixture initial state mismatch');
    }
    await percent.fill(fixture.percent);
    await (await one(page, 'button')).click();
    await page.reload({waitUntil: 'load', timeout: 10000});
    report.assertions[`remaining_${fixture.remaining}h`] = await (await one(page, '[aria-label="Remaining work"]')).inputValue() === fixture.remaining;
    report.assertions[`work_${fixture.work}h`] = await (await one(page, '[aria-label="Work"]')).inputValue() === fixture.work;
    report.assertions[`percent_${fixture.percent}`] = /^(?:\d+)(?:%)?$/.test(await (await one(page, '[aria-label="% Complete"]')).inputValue())
      && parseFloat(await percent.inputValue()) === Number(fixture.percent);
    await page.screenshot({path: `/output/fixture-${index + 1}.png`, fullPage: true});
  } finally {
    await context.close();
  }
}

(async () => {
  let browser;
  try {
    browser = await chromium.launch({headless: true, chromiumSandbox: false});
    for (let index = 0; index < fixtures.length; index++) await runFixture(browser, fixtures[index], index);
    report.status = 'complete';
    report.screenshots = ['fixture-1.png', 'fixture-2.png'];
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
