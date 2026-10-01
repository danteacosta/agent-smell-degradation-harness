'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[
  {done:{id:'done-a',title:'Submit draft'},active:{id:'active-a',title:'Review figures'}},
  {done:{id:'done-b',title:'Merge notes'},active:{id:'active-b',title:'Read source'}},
];
const report={schema_version:'todomvc-clear-button-browser/v5',status:'browser_error',app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
async function runFixture(browser,fixture,index){const context=await browser.newContext({viewport:{width:1000,height:720},timezoneId:'UTC',serviceWorkers:'block'});
  try{
    await context.addInitScript(initial=>Object.defineProperty(window,'initialState',{value:initial}),{todos:[{...fixture.done,completed:true},{...fixture.active,completed:false}]});
    await context.route('**/*',route=>route.request().url()===URL&&route.request().isNavigationRequest()
      ?route.fulfill({body:html,contentType:'text/html',headers:{'Content-Security-Policy':CSP}}):route.abort());
    const page=await context.newPage();page.setDefaultTimeout(2500);
    page.on('console',m=>{if(m.type()==='error'&&report.console_errors.length<20)report.console_errors.push(m.text().slice(0,500))});
    page.on('pageerror',e=>{if(report.console_errors.length<20)report.console_errors.push(String(e).slice(0,500))});
    await page.goto(URL,{waitUntil:'load',timeout:10000});
    const done=await one(page,`[data-todo-id="${fixture.done.id}"]`);const active=await one(page,`[data-todo-id="${fixture.active.id}"]`);
    if(await done.locator('span').innerText()!==fixture.done.title||await active.locator('span').innerText()!==fixture.active.title
      ||!await done.locator('input').isChecked()||await active.locator('input').isChecked()||await page.locator('[data-todo-id]').count()!==2)
      throw new InterfaceError('initial todo fixture mismatch');
    const action=await one(page,'#clear-completed');
    report.assertions[`initial_button_visible_${index+1}`]=await action.isVisible();
    if(!await action.isEnabled())throw new InterfaceError('clear action unavailable');
    await action.click();
    const button=page.locator('#clear-completed');
    report.assertions[`clear_button_hidden_${index+1}`]=await button.count()===0||!await button.isVisible();
    report.assertions[`completed_removed_${index+1}`]=await page.locator(`[data-todo-id="${fixture.done.id}"]`).count()===0;
    const remaining=page.locator(`[data-todo-id="${fixture.active.id}"]`);
    report.assertions[`active_preserved_${index+1}`]=await remaining.count()===1&&await remaining.locator('span').innerText()===fixture.active.title&&
      !await remaining.locator('input').isChecked();
    const ids=await page.locator('[data-todo-id]').evaluateAll(nodes=>nodes.map(node=>node.getAttribute('data-todo-id')));
    report.assertions[`only_active_id_${index+1}`]=ids.length===1&&ids[0]===fixture.active.id;
    await page.screenshot({path:`/output/fixture-${index+1}.png`,fullPage:true});
  }finally{await context.close()}
}
async function runInitiallyEmpty(browser){const context=await browser.newContext({viewport:{width:1000,height:720},timezoneId:'UTC',serviceWorkers:'block'});
  try{await context.addInitScript(()=>Object.defineProperty(window,'initialState',{value:{todos:[{id:'only-active',title:'Read source',completed:false}]}}));
    await context.route('**/*',route=>route.request().url()===URL&&route.request().isNavigationRequest()
      ?route.fulfill({body:html,contentType:'text/html',headers:{'Content-Security-Policy':CSP}}):route.abort());
    const page=await context.newPage();page.setDefaultTimeout(2500);
    page.on('console',m=>{if(m.type()==='error'&&report.console_errors.length<20)report.console_errors.push(m.text().slice(0,500))});
    page.on('pageerror',e=>{if(report.console_errors.length<20)report.console_errors.push(String(e).slice(0,500))});
    await page.goto(URL,{waitUntil:'load',timeout:10000});
    const row=await one(page,'[data-todo-id="only-active"]');
    if(await row.locator('span').innerText()!=='Read source'||await row.locator('input').isChecked()||await page.locator('[data-todo-id]').count()!==1)
      throw new InterfaceError('initial no-completed fixture mismatch');
    const button=page.locator('#clear-completed');
    report.assertions.empty_button_hidden_3=await button.count()===0||!await button.isVisible();
    report.assertions.active_preserved_3=await row.count()===1&&await row.locator('span').innerText()==='Read source'&&
      !await row.locator('input').isChecked();
    await page.screenshot({path:'/output/fixture-3.png',fullPage:true});
  }finally{await context.close()}
}
async function runEmptyList(browser){const context=await browser.newContext({viewport:{width:1000,height:720},timezoneId:'UTC',serviceWorkers:'block'});
  try{await context.addInitScript(()=>Object.defineProperty(window,'initialState',{value:{todos:[]}}));
    await context.route('**/*',route=>route.request().url()===URL&&route.request().isNavigationRequest()
      ?route.fulfill({body:html,contentType:'text/html',headers:{'Content-Security-Policy':CSP}}):route.abort());
    const page=await context.newPage();page.setDefaultTimeout(2500);
    page.on('console',m=>{if(m.type()==='error'&&report.console_errors.length<20)report.console_errors.push(m.text().slice(0,500))});
    page.on('pageerror',e=>{if(report.console_errors.length<20)report.console_errors.push(String(e).slice(0,500))});
    await page.goto(URL,{waitUntil:'load',timeout:10000});
    const button=page.locator('#clear-completed');
    report.assertions.empty_list_button_hidden_4=await button.count()===0||!await button.isVisible();
    report.assertions.empty_list_preserved_4=await page.locator('[data-todo-id]').count()===0;
    await page.screenshot({path:'/output/fixture-4.png',fullPage:true});
  }finally{await context.close()}
}
(async()=>{let browser;try{browser=await chromium.launch({headless:true,chromiumSandbox:false});
  for(let i=0;i<fixtures.length;i++)await runFixture(browser,fixtures[i],i);
  await runInitiallyEmpty(browser);
  await runEmptyList(browser);
  report.status='complete';report.screenshots=['fixture-1.png','fixture-2.png','fixture-3.png','fixture-4.png'];
}catch(error){report.status=report.console_errors.length?'browser_error':error instanceof InterfaceError?'interface_error':'browser_error';report.assertions={};report.error=String(error).slice(0,1500);
}finally{if(browser)await browser.close();fs.writeFileSync('/output/report.json',JSON.stringify(report,null,2));process.exitCode=report.status==='complete'?0:2}})();
