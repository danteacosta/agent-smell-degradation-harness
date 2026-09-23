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
async function recognizeRow(page,title,{visibleOnly=true}={}) {
  const rows=page.locator('ul.todo-list > li');
  const count=await rows.count();
  let match;
  for(let i=0;i<count;i++){
    const candidate=rows.nth(i);
    // Even visibleOnly:false cannot turn hidden DOM text into a semantic match.
    if(!await candidate.isVisible())continue;
    const elements=candidate.locator(':visible');
    const titles=await elements.evaluateAll((nodes,title)=>{
      const formControls='input,textarea,select,option,button,output';
      const textNodes=nodes.map((element,index)=>({element,index,
        text:typeof element.innerText==='string'?element.innerText.trim():''}))
        .filter(({element})=>!element.closest(formControls) && !element.querySelector(formControls));
      const exact=textNodes.filter(({text})=>text===title);
      // This boolean only gates the edit fallback; it never constructs a title match.
      const hasText=nodes.some(element=>!element.closest(formControls)
        && Array.from(element.childNodes).some(child=>
          child.nodeType===Node.TEXT_NODE && child.textContent.trim().length>0));
      return {hasText,
        indices:exact.filter(({element})=>!exact.some(other=>
          other.element!==element && element.contains(other.element))).map(({index})=>index)};
    },title);
    if(titles.indices.length>1)return {status:'ambiguous'};
    let titleElement=titles.indices.length===1?elements.nth(titles.indices[0]):null;
    if(!titleElement && !titles.hasText){
      const input=await editInput(candidate);
      if(input && (await input.inputValue()).trim()===title)titleElement=input;
    }
    if(titleElement){
      if(match)return {status:'ambiguous'};
      match={status:'matched',row:candidate,titleElement};
    }
  }
  return match || {status:'absent'};
}
async function hasExactDomTitle(page,title) {
  const rows=page.locator('ul.todo-list > li');
  for(let i=0;i<await rows.count();i++){
    const candidate=rows.nth(i);
    if(await candidate.isVisible())continue;
    if(await candidate.locator('*').evaluateAll((elements,title)=>elements.some(element=>
        !element.closest('input,textarea,select,option,button,output')
        && (element.textContent || '').trim()===title),title))return true;
  }
  return false;
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
      return (await recognizeRow(second,title)).status==='matched';
    });
    await scenario('completed_survives_reload',async context=>{
      const errors=[];const first=await pageIn(context,errors);
      const title='persist-row-two';await add(first,title);
      const todo=await recognizeRow(first,title);
      if(todo.status!=='matched')return false;
      const check=todo.row.locator('input[type="checkbox"]');
      if(await check.count()!==1)return false;
      await check.check();await first.waitForTimeout(300);
      const second=await pageIn(context,errors);
      const restored=await recognizeRow(second,title);
      if(restored.status!=='matched')return false;
      const restoredCheck=restored.row.locator('input[type="checkbox"]');
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
      const todo=await recognizeRow(first,title);
      let target;
      if(todo.status!=='matched')throw new InterfaceError('one exact visible todo title required before edit');
      await todo.titleElement.dblclick();await first.waitForTimeout(300);
      const editing=await editInput(todo.row);
      if(!editing)throw new InterfaceError('visible edit input required after double-click');
      await first.screenshot({path:'/output/editing.png'});
      const second=await pageIn(context,errors);
      const restored=await recognizeRow(second,title);
      if(restored.status==='absent'){
        const hidden=await hasExactDomTitle(second,title);
        target={status:'not_evaluable',reason:hidden
          ? 'todo_not_visible_after_reload':'todo_missing_after_reload'};
      }
      else if(restored.status==='ambiguous')
        target={status:'not_evaluable',reason:'todo_ambiguous_after_reload'};
      else target={status:await editInput(restored.row)?'failed':'passed'};
      await second.screenshot({path:'/output/after-reload.png'});
      const storage=await second.evaluate(()=>({
        storage_keys:Object.keys(localStorage).filter(key=>key==='todos-vanilla'),
        storage_key_count:localStorage.length}));
      report.target_observation={...storage,console_errors:errors,
        before_edit_todo_present:true,editing_visible_before_reload:
          Boolean(await editInput(todo.row)),todo_present_after_reload:restored.status==='matched',
        editing_visible_after_reload:Boolean(restored.status==='matched' && await editInput(restored.row))};
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
