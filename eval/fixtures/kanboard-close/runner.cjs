'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{target:'Review proposal',control:'Prepare budget'},{target:'Write release note',control:'Update roadmap'}];
const report={schema_version:'kanboard-close-browser/v1',status:'browser_error',app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
async function name(page,selector){const node=page.locator(selector);return await node.count()===1&&await node.isVisible()?await node.innerText():''}
async function runFixture(browser,f,i){
  const context=await browser.newContext({viewport:{width:1000,height:720},timezoneId:'UTC',serviceWorkers:'block'});
  try{
    await context.addInitScript(initial=>Object.defineProperty(window,'initialState',{value:initial}),
      {tasks:[{id:'target',title:f.target,status:'open',boardVisible:true},{id:'control',title:f.control,status:'open',boardVisible:true}]});
    await context.route('**/*',route=>route.request().url()===URL&&route.request().isNavigationRequest()?route.fulfill({body:html,contentType:'text/html',headers:{'Content-Security-Policy':CSP}}):route.abort());
    const page=await context.newPage();page.setDefaultTimeout(2500);
    page.on('console',m=>{if(m.type()==='error'&&report.console_errors.length<20)report.console_errors.push(m.text().slice(0,500))});
    page.on('pageerror',e=>{if(report.console_errors.length<20)report.console_errors.push(String(e).slice(0,500))});
    await page.goto(URL,{waitUntil:'load',timeout:10000});
    const target=await one(page,'[data-task-id="target"]');await one(page,'[data-task-id="control"]');
    if(await target.locator('h2').innerText()!==f.target||await page.locator('[data-task-id]').count()!==2)throw new InterfaceError('initial board mismatch');
    const action=await one(target,'button');if(!await action.isEnabled())throw new InterfaceError('close action unavailable');
    await action.click();await page.reload({waitUntil:'load',timeout:10000});
    report.assertions[`target_hidden_${i+1}`]=await page.locator('[data-task-id="target"]').count()===0;
    report.assertions[`control_on_board_${i+1}`]=await name(page,'[data-task-id="control"] h2')===f.control;
    report.assertions[`board_count_${i+1}`]=await page.locator('[data-task-id]').count()===(await page.locator('[data-task-id="target"]').count()+1);
    await page.screenshot({path:`/output/board-${i+1}.png`,fullPage:true});
    await (await one(page,'#closed')).click();
    report.assertions[`closed_reachable_${i+1}`]=await name(page,'[data-task-id="target"] h2')===f.target;
    report.assertions[`no_unrelated_closed_${i+1}`]=await page.locator('[data-task-id="control"]').count()===0;
    await page.screenshot({path:`/output/closed-${i+1}.png`,fullPage:true});
  }finally{await context.close()}
}
(async()=>{let browser;try{
  browser=await chromium.launch({headless:true,chromiumSandbox:false});
  for(let i=0;i<fixtures.length;i++)await runFixture(browser,fixtures[i],i);
  report.status='complete';report.screenshots=['board-1.png','closed-1.png','board-2.png','closed-2.png'];
}catch(error){report.status=report.console_errors.length?'browser_error':error instanceof InterfaceError?'interface_error':'browser_error';report.assertions={};report.error=String(error).slice(0,1500);
}finally{if(browser)await browser.close();fs.writeFileSync('/output/report.json',JSON.stringify(report,null,2));process.exitCode=report.status==='complete'?0:2}})();
