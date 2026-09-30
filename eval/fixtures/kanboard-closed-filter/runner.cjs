'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[
  {open:{id:'open-11',title:'Prepare release',status:'open'},closed:{id:'closed-13',title:'Archive invoice',status:'closed'}},
  {open:{id:'open-41',title:'Review patch',status:'open'},closed:{id:'closed-47',title:'Finish migration',status:'closed'}},
];
const report={schema_version:'kanboard-closed-filter-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
async function taskSeen(page,task){const row=page.locator(`[data-task-id="${task.id}"]`);return await row.count()===1&&await row.isVisible()&&await row.innerText()===task.title}
async function runFixture(browser,f,i){const context=await browser.newContext({viewport:{width:1000,height:720},timezoneId:'UTC',serviceWorkers:'block'});
  try{
    await context.addInitScript(initial=>Object.defineProperty(window,'initialState',{value:initial}),{tasks:[f.open,f.closed]});
    await context.route('**/*',route=>route.request().url()===URL&&route.request().isNavigationRequest()
      ?route.fulfill({body:html,contentType:'text/html',headers:{'Content-Security-Policy':CSP}}):route.abort());
    const page=await context.newPage();page.setDefaultTimeout(2500);
    page.on('console',m=>{if(m.type()==='error'&&report.console_errors.length<20)report.console_errors.push(m.text().slice(0,500))});
    page.on('pageerror',e=>{if(report.console_errors.length<20)report.console_errors.push(String(e).slice(0,500))});
    await page.goto(URL,{waitUntil:'load',timeout:10000});
    if(!await page.evaluate(()=>typeof viewHandler==='function'))throw new InterfaceError('view handler unavailable');
    const selector=await one(page,'#view');if(await selector.inputValue()!=='board'||await selector.locator('option[value="closed"]').count()!==1)throw new InterfaceError('filter unavailable');
    report.assertions[`open_on_board_${i+1}`]=await taskSeen(page,f.open);
    report.assertions[`closed_absent_on_board_${i+1}`]=await page.locator(`[data-task-id="${f.closed.id}"]`).count()===0;
    await selector.selectOption('closed');
    report.assertions[`closed_visible_${i+1}`]=await taskSeen(page,f.closed);
    report.assertions[`view_changed_${i+1}`]=await selector.inputValue()==='closed';
    report.assertions[`rows_unique_${i+1}`]=await page.locator('[data-task-id]').evaluateAll(nodes=>{
      const ids=nodes.map(node=>node.dataset.taskId);return ids.every(Boolean)&&new Set(ids).size===ids.length});
    await page.screenshot({path:`/output/fixture-${i+1}.png`,fullPage:true});
  }finally{await context.close()}
}
(async()=>{let browser;try{browser=await chromium.launch({headless:true,chromiumSandbox:false});
  for(let i=0;i<fixtures.length;i++)await runFixture(browser,fixtures[i],i);
  report.status='complete';report.screenshots=['fixture-1.png','fixture-2.png'];
}catch(error){report.status=report.console_errors.length?'browser_error':error instanceof InterfaceError?'interface_error':'browser_error';report.assertions={};report.error=String(error).slice(0,1500);
}finally{if(browser)await browser.close();fs.writeFileSync('/output/report.json',JSON.stringify(report,null,2));process.exitCode=report.status==='complete'?0:2}})();
