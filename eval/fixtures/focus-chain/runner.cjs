'use strict';
// Trusted Node controller. Untrusted HTML is only a Chromium document.
const fs = require('node:fs');
const crypto = require('node:crypto');
const {chromium} = require('playwright');
const html = fs.readFileSync('/input/app.html');
const report = {schema_version: 'focus-chain-browser/v1', status: 'browser_error',
  app_sha256: crypto.createHash('sha256').update(html).digest('hex'),
  focus_horizon_ms: 500, action_settle_ms: 500, cases: [], browser_sandbox: false,
  isolation: 'non-root offline resource-bounded Docker; browser sandbox disabled'};
let browser;
class InterfaceError extends Error {}
async function fresh() {
  const context = await browser.newContext({viewport:{width:1000,height:720}, serviceWorkers:'block', acceptDownloads:false});
  await context.route('**/*', route => route.request().url() === 'http://fixture.invalid/' && route.request().isNavigationRequest()
    ? route.fulfill({body:html, contentType:'text/html', headers:{'Content-Security-Policy':"default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"}})
    : route.abort());
  const page = await context.newPage();
  page.setDefaultTimeout(2500);
  page.on('dialog', dialog => dialog.dismiss());
  await page.goto('http://fixture.invalid/', {waitUntil:'load',timeout:10000});
  await page.waitForTimeout(500);
  const input=page.locator('input.new-todo'); const list=page.locator('.todo-list');
  if (await input.count() !== 1 || await list.count() !== 1 || !await input.isVisible()) {
    await context.close(); throw new InterfaceError('one visible input.new-todo and one .todo-list required');
  }
  return {context,page,input,list};
}
async function scenario(id, check) {
  const s=await fresh();
  try { report.cases.push({id, status:await check(s) ? 'passed':'failed'}); }
  finally {await s.context.close();}
}
async function visibleTitlesMatch(list, expected) {
  const items=list.locator(':scope > li');
  if (await items.count() !== expected.length) return false;
  for (let index=0; index<expected.length; index++) {
    const item=items.nth(index); const label=item.locator(':scope > label');
    if (await label.count() !== 1) throw new InterfaceError('each todo li requires one direct-child label');
    if (!await item.isVisible() || !await label.isVisible()
        || await label.textContent() !== expected[index]) return false;
  }
  return true;
}
async function enter(input, page) {
  await input.press('Enter');
  // Uniform observation horizon, not a source-defined performance requirement.
  await page.waitForTimeout(500);
}
async function isolatedFocus(page) {
  const session=await page.context().newCDPSession(page);
  try {
    const tree=await session.send('Page.getFrameTree');
    const world=await session.send('Page.createIsolatedWorld',{frameId:tree.frameTree.frame.id, worldName:'trusted-observer'});
    const value=await session.send('Runtime.evaluate',{contextId:world.executionContextId, returnByValue:true,
      expression:'({focused: document.activeElement === document.querySelector("input.new-todo"), tag: document.activeElement?.tagName, classes: document.activeElement?.className})'});
    return value.result.value;
  } finally {await session.detach();}
}
(async()=>{
  try {
    browser=await chromium.launch({headless:true, chromiumSandbox:false});
    await scenario('initial_focus', async({page})=>{
      report.focus_observation=await isolatedFocus(page);
      await page.screenshot({path:'/output/initial-focus.png'});
      return report.focus_observation.focused === true;
    });
    await scenario('input_above_list', async({input,list})=>{
      const a=await input.boundingBox(); const b=await list.boundingBox();
      return a !== null && b !== null && a.y+a.height <= b.y;
    });
    await scenario('enter_append', async({page,input,list})=>{
      await input.fill('first task'); await enter(input,page);
      await input.fill('second task'); await enter(input,page);
      return visibleTitlesMatch(list, ['first task','second task']);
    });
    await scenario('input_cleared', async({page,input})=>{
      await input.fill('a task'); await enter(input,page); return await input.inputValue() === '';
    });
    await scenario('trimmed_title', async({page,input,list})=>{
      await input.fill('  padded task  '); await enter(input,page);
      return visibleTitlesMatch(list, ['padded task']);
    });
    await scenario('empty_rejected', async({page,input,list})=>{
      await input.fill(''); await enter(input,page); return await list.locator('li').count() === 0;
    });
    await scenario('whitespace_rejected', async({page,input,list})=>{
      await input.fill('   '); await enter(input,page); return await list.locator('li').count() === 0;
    });
    report.status='complete';
  } catch(error) {
    report.status=error instanceof InterfaceError ? 'interface_error':'browser_error';
    report.error=String(error).slice(0,1500);
  } finally {
    if(browser) await browser.close();
    fs.writeFileSync('/output/report.json',JSON.stringify(report,null,2));
    process.exitCode=report.status !== 'complete' ? 2 : report.cases.some(c=>c.status==='failed') ? 1 : 0;
  }
})();
