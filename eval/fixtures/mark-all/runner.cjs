'use strict';
// Trusted controller: generated HTML runs only as an offline Chromium document.
const fs = require('node:fs');
const crypto = require('node:crypto');
const {chromium} = require('playwright');
const html = fs.readFileSync('/input/app.html');
const report = {schema_version:'mark-all-browser/v1', status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),
  action_settle_ms:300, cases:[], browser_sandbox:false,
  isolation:'non-root offline resource-bounded Docker; browser sandbox disabled'};
let browser;
class InterfaceError extends Error {}
async function fresh() {
  const context=await browser.newContext({viewport:{width:1000,height:720}, serviceWorkers:'block', acceptDownloads:false});
  await context.addInitScript({content:'window.initialTodos = [{id:"fixture-a",title:"alpha",completed:false},{id:"fixture-b",title:"beta",completed:false}];'});
  await context.route('**/*',route=>route.request().url()==='http://fixture.invalid/' && route.request().isNavigationRequest()
    ? route.fulfill({body:html,contentType:'text/html',headers:{'Content-Security-Policy':"default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"}})
    : route.abort());
  const page=await context.newPage(); page.setDefaultTimeout(2500);
  const consoleErrors=[];
  page.on('console',message=>{if(message.type()==='error' && consoleErrors.length<20)consoleErrors.push(message.text().slice(0,500));});
  page.on('pageerror',error=>{if(consoleErrors.length<20)consoleErrors.push(String(error).slice(0,500));});
  page.on('dialog',dialog=>dialog.dismiss());
  await page.goto('http://fixture.invalid/',{waitUntil:'load',timeout:10000});
  await page.waitForTimeout(300);
  const master=page.locator('input[type="checkbox"]#toggle-all');
  const clear=page.locator('button#clear-completed');
  const list=page.locator('ul#todo-list');
  if (await master.count()!==1 || await clear.count()!==1 || await list.count()!==1
      || !await master.isVisible()) {
    await context.close(); throw new InterfaceError('one visible master, clear button and todo list required initially');
  }
  async function rows() {
    const items=list.locator(':scope > li');
    if (await items.count()!==2) throw new InterfaceError('exactly two initial todo rows required');
    const checks=new Map();
    for (let i=0;i<2;i++) {
      const input=items.nth(i).locator('input[type="checkbox"]');
      const label=items.nth(i).locator('label');
      if(await input.count()!==1 || await label.count()!==1 || !await label.isVisible()) {
        throw new InterfaceError('todo rows require one descendant checkbox and visible label');
      }
      const title=(await label.textContent()).trim();
      if(!['alpha','beta'].includes(title) || checks.has(title))throw new InterfaceError('fixture titles missing or duplicated');
      checks.set(title,input);
    }
    return ['alpha','beta'].map(title=>checks.get(title));
  }
  const checks=await rows();
  if(await master.isChecked() || await checks[0].isChecked() || await checks[1].isChecked()) {
    await context.close(); throw new InterfaceError('fixture todos must start active');
  }
  return {context,page,master,clear,list,checks,consoleErrors};
}
async function settled(page) {await page.waitForTimeout(300);}
async function scenario(id, check) {
  const s=await fresh();
  try {
    const result=await check(s);
    report.cases.push({id,...(typeof result==='boolean'
      ? {status:result?'passed':'failed'} : result)});
  }
  finally {await s.context.close();}
}
(async()=>{
  try {
    browser=await chromium.launch({headless:true,chromiumSandbox:false});
    await scenario('master_sets_items',async({page,master,checks})=>{
      await master.check();await settled(page);
      if (!await checks[0].isChecked() || !await checks[1].isChecked()) return false;
      await master.uncheck();await settled(page);
      return !await checks[0].isChecked() && !await checks[1].isChecked();
    });
    await scenario('master_tracks_individuals',async({page,master,checks})=>{
      await checks[0].check();await settled(page);
      if(await master.isChecked())return false;
      await checks[1].check();await settled(page);
      if(!await master.isChecked())return false;
      await checks[0].uncheck();await settled(page);
      return !await master.isChecked();
    });
    await scenario('clear_completed_removes_items',async({page,master,clear,list,checks})=>{
      await master.check();await settled(page);
      if(!await checks[0].isChecked() || !await checks[1].isChecked()) {
        await page.screenshot({path:'/output/after-clear.png'});
        return {status:'not_evaluable',reason:'bulk_selection_failed'};
      }
      if(!await clear.isVisible()){
        await page.screenshot({path:'/output/after-clear.png'});return false;
      }
      await clear.click();await settled(page);
      await page.screenshot({path:'/output/after-clear.png'});
      return await list.locator(':scope > li').count()===0;
    });
    const target=await fresh();
    try {
      const {page,master,clear,list,checks,consoleErrors}=target;
      const observe=async()=>({todo_count:await list.locator(':scope > li').count(),
        checked_items:await list.locator(':scope > li input[type="checkbox"]:checked').count(),
        master_count:await master.count(), master_checked:await master.count()?await master.isChecked():null,
        checked_outside_list:await page.locator('input[type="checkbox"]').evaluateAll(
          elements=>elements.filter(element=>!element.closest('#todo-list') && element.checked)
            .map(element=>element.id||'(unnamed)'))});
      await page.screenshot({path:'/output/before-target.png'});
      const before=await observe();
      await master.check();await settled(page);
      let targetCase;
      if(!await checks[0].isChecked() || !await checks[1].isChecked()){
        targetCase={id:'clear_master_after_clear_completed',status:'not_evaluable',reason:'bulk_selection_failed'};
      }else if(!await clear.isVisible()){
        targetCase={id:'clear_master_after_clear_completed',status:'not_evaluable',reason:'clear_unavailable'};
      }else{
        await clear.click();await settled(page);
        if(await list.locator(':scope > li').count()!==0){
          targetCase={id:'clear_master_after_clear_completed',status:'not_evaluable',reason:'clear_failed'};
        }else{
          const masterCount=await master.count();
          if(masterCount===1){
            targetCase={id:'clear_master_after_clear_completed',
              status:await master.isChecked()?'failed':'passed'};
          }else if(masterCount>1){
            targetCase={id:'clear_master_after_clear_completed',status:'not_evaluable',
              reason:'master_identity_ambiguous'};
          }else{
            const otherChecked=await page.locator('input[type="checkbox"]').evaluateAll(
              elements=>elements.some(element=>!element.closest('#todo-list') && element.checked));
            targetCase={id:'clear_master_after_clear_completed',
              status:otherChecked?'not_evaluable':'passed',
              ...(otherChecked?{reason:'master_identity_ambiguous'}:{})};
          }
        }
      }
      const after=await observe();
      await page.screenshot({path:'/output/after-target.png'});
      report.target_observation={before,after,console_errors:consoleErrors};
      report.cases.push(targetCase);
    }finally{await target.context.close();}
    report.status='complete';
  } catch(error) {
    report.status=error instanceof InterfaceError?'interface_error':'browser_error';
    report.error=String(error).slice(0,1500);
  } finally {
    if(browser)await browser.close();
    fs.writeFileSync('/output/report.json',JSON.stringify(report,null,2));
    process.exitCode=report.status!=='complete'?2:report.cases.some(c=>c.status!=='passed')?1:0;
  }
})();
