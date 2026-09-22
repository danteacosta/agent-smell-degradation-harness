'use strict';
// Only the trusted controller reads reports. Generated HTML runs in isolated Chromium.
const fs = require('node:fs');
const crypto = require('node:crypto');
const {chromium} = require('playwright');
const html = fs.readFileSync('/input/app.html');
const report = {schema_version:'persistence-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),
  action_settle_ms:300,cases:[],browser_sandbox:false,
  isolation:'non-root offline resource-bounded Docker; browser sandbox disabled'};
const origin='http://fixture.invalid/';
let browser;
class InterfaceError extends Error {}
async function contextForScenario() {
  const context=await browser.newContext({viewport:{width:1000,height:720},
    serviceWorkers:'block',acceptDownloads:false});
  await context.route('**/*',route=>route.request().url()===origin && route.request().isNavigationRequest()
    ? route.fulfill({body:html,contentType:'text/html',headers:{'Content-Security-Policy':
      "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"}})
    : route.abort());
  return context;
}
async function pageIn(context, errors) {
  const page=await context.newPage();
  page.setDefaultTimeout(2500);
  page.on('console',message=>{if(message.type()==='error' && errors.length<20)
    errors.push(message.text().slice(0,500));});
  page.on('pageerror',error=>{if(errors.length<20)errors.push(String(error).slice(0,500));});
  page.on('dialog',dialog=>dialog.dismiss());
  await page.goto(origin,{waitUntil:'load',timeout:10000});
  await page.waitForTimeout(300);
  return page;
}
async function row(page,title) {
  const rows=page.locator('ul.todo-list > li');
  const count=await rows.count();
  for(let i=0;i<count;i++){
    const candidate=rows.nth(i);
    const label=candidate.locator('label');
    if(await label.count()===1 && (await label.textContent()).trim()===title)return candidate;
    const input=await editInput(candidate);
    if(input && (await input.inputValue()).trim()===title)return candidate;
  }
  return null;
}
async function add(page,title) {
  const input=page.locator('input.new-todo');
  if(await input.count()!==1 || !await input.isVisible()
      || await page.locator('ul.todo-list').count()!==1)
    throw new InterfaceError('one visible new-todo input and todo-list required');
  await input.fill(title);await input.press('Enter');await page.waitForTimeout(300);
}
async function editInput(todoRow) {
  const inputs=todoRow.locator('input:not([type]), input[type="text"]');
  for(let i=0;i<await inputs.count();i++)
    if(await inputs.nth(i).isVisible() && await inputs.nth(i).isEditable())return inputs.nth(i);
  return null;
}
async function scenario(id,check) {
  const context=await contextForScenario();
  try {const result=await check(context);report.cases.push({id,...(typeof result==='boolean'
      ? {status:result?'passed':'failed'}:result)});}
  finally {await context.close();}
}
(async()=>{
  try {
    browser=await chromium.launch({headless:true,chromiumSandbox:false});
    await scenario('todo_survives_reload',async context=>{
      const errors=[];const first=await pageIn(context,errors);
      const title='persist-row-one';await add(first,title);
      const second=await pageIn(context,errors);
      return Boolean(await row(second,title));
    });
    await scenario('completed_survives_reload',async context=>{
      const errors=[];const first=await pageIn(context,errors);
      const title='persist-row-two';await add(first,title);
      const todo=await row(first,title);
      if(!todo)return false;
      const check=todo.locator('input[type="checkbox"]');
      if(await check.count()!==1)return false;
      await check.check();await first.waitForTimeout(300);
      const second=await pageIn(context,errors);
      const restored=await row(second,title);
      if(!restored)return false;
      const restoredCheck=restored.locator('input[type="checkbox"]');
      return await restoredCheck.count()===1 && await restoredCheck.isChecked();
    });
    await scenario('local_storage_used',async context=>{
      const errors=[];const first=await pageIn(context,errors);
      const title='persist-row-three';await add(first,title);
      return await first.evaluate(()=>{
        const value=localStorage.getItem('todos-vanilla');
        return typeof value==='string' && value.length>0;
      });
    });
    const context=await contextForScenario();
    try {
      const errors=[];const first=await pageIn(context,errors);
      const title='persist-target-row';await add(first,title);
      await first.screenshot({path:'/output/before-edit.png'});
      const todo=await row(first,title);
      let target;
      if(!todo){target={status:'not_evaluable',reason:'todo_missing_after_reload'};}
      else {
        await todo.locator('label').dblclick();await first.waitForTimeout(300);
        const editing=await editInput(todo);
        if(!editing)target={status:'not_evaluable',reason:'edit_interface_unavailable'};
      }
      await first.screenshot({path:'/output/editing.png'});
      const second=await pageIn(context,errors);
      const restored=await row(second,title);
      if(!target){
        if(!restored)target={status:'not_evaluable',reason:'todo_missing_after_reload'};
        else target={status:await editInput(restored)?'failed':'passed'};
      }
      await second.screenshot({path:'/output/after-reload.png'});
      const storage=await second.evaluate(()=>({
        storage_keys:Object.keys(localStorage).filter(key=>key==='todos-vanilla'),
        storage_key_count:localStorage.length}));
      report.target_observation={...storage,console_errors:errors,
        before_edit_todo_present:Boolean(todo),editing_visible_before_reload:
          Boolean(todo && await editInput(todo)),todo_present_after_reload:Boolean(restored),
        editing_visible_after_reload:Boolean(restored && await editInput(restored))};
      report.cases.push({id:'editing_not_restored',...target});
    } finally {await context.close();}
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
