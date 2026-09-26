'use strict';

const fs = require('node:fs');
const crypto = require('node:crypto');
const {chromium} = require('playwright');

const html = fs.readFileSync('/input/app.html');
const URL = 'http://fixture.invalid/';
const CSP = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures = [
  {title: 'Release candidate', projectId: 'project-one', controlTitle: 'Unrelated task'},
  {title: 'Hotfix review', projectId: 'project-two', controlTitle: 'Budget review'},
];
const report = {
  schema_version: 'kanboard-duplicate-title-browser/v1', status: 'browser_error',
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
    }, {tasks: [
      {id: 'source-task', projectId: fixture.projectId, title: fixture.title},
      {id: 'control-task', projectId: fixture.projectId, title: fixture.controlTitle},
    ]});
    await context.route('**/*', route => route.request().url() === URL && route.request().isNavigationRequest()
      ? route.fulfill({body: html, contentType: 'text/html', headers: {'Content-Security-Policy': CSP}})
      : route.abort());
    const page = await context.newPage();
    page.setDefaultTimeout(2500);
    page.on('console', message => {if (message.type() === 'error' && report.console_errors.length < 20) report.console_errors.push(message.text().slice(0, 500));});
    page.on('pageerror', error => {if (report.console_errors.length < 20) report.console_errors.push(String(error).slice(0, 500));});
    await page.goto(URL, {waitUntil: 'load', timeout: 10000});
    const source = await one(page, '[data-task-id="source-task"]');
    const control = await one(page, '[data-task-id="control-task"]');
    if (await source.locator('h2').innerText() !== fixture.title || await control.locator('h2').innerText() !== fixture.controlTitle) {
      throw new InterfaceError('initial task fixture mismatch');
    }
    const preClick = await page.evaluate(() => ({taskCount: app.tasks().length, handlerRegistered: typeof duplicateBehavior === 'function'}));
    if (preClick.taskCount !== 2 || !preClick.handlerRegistered || await page.locator('[data-task-id]').count() !== 2) {
      throw new InterfaceError('duplicate must be created by the click handler');
    }
    await (await one(source, 'button')).click();
    const rows = page.locator('[data-task-id]');
    if (await rows.count() !== 3) throw new InterfaceError('one distinct duplicate required');
    const ids = await rows.evaluateAll(nodes => nodes.map(node => node.getAttribute('data-task-id')));
    if (ids.some(id => !id) || new Set(ids).size !== 3 || !ids.includes('source-task') || !ids.includes('control-task')) {
      throw new InterfaceError('distinct task identity required');
    }
    const duplicateId = ids.find(id => id !== 'source-task' && id !== 'control-task');
    const duplicate = rows.nth(ids.indexOf(duplicateId));
    if (!await duplicate.isVisible()) throw new InterfaceError('visible duplicate required');
    const duplicateTitle = duplicate.locator('h2');
    if (await duplicateTitle.count() !== 1) throw new InterfaceError('one duplicate title node required');
    report.assertions[`duplicate_title_${index + 1}`] = await duplicateTitle.isVisible()
      && await duplicateTitle.innerText() === fixture.title;
    report.assertions[`same_project_${index + 1}`] = await (await one(duplicate, '.project')).innerText() === 'Project: ' + fixture.projectId;
    report.assertions[`source_preserved_${index + 1}`] = await source.locator('h2').innerText() === fixture.title
      && await (await one(source, '.project')).innerText() === 'Project: ' + fixture.projectId;
    report.assertions[`unrelated_preserved_${index + 1}`] = await control.locator('h2').innerText() === fixture.controlTitle
      && await (await one(control, '.project')).innerText() === 'Project: ' + fixture.projectId;
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
    report.status = report.console_errors.length ? 'browser_error'
      : error instanceof InterfaceError ? 'interface_error' : 'browser_error';
    report.assertions = {};
    report.error = String(error).slice(0, 1500);
  } finally {
    if (browser) await browser.close();
    fs.writeFileSync('/output/report.json', JSON.stringify(report, null, 2));
    process.exitCode = report.status === 'complete' ? 0 : 2;
  }
})();
