'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"slide": 2, "slides": ["Welcome", "Add a dish", "Change an order", "Done"], "rows": [{"id": "mon", "label": "Monday", "value": "Pasta"}, {"id": "tue", "label": "Tuesday", "value": "Soup"}, {"id": "wed", "label": "Wednesday", "value": "Salad"}]}, "saved": null, "unsaved": ["tue", "Curry"]}, {"state": {"slide": 1, "slides": ["Start", "Edit prices", "Finish"], "rows": [{"id": "tea", "label": "Tea", "value": "2.00"}, {"id": "cake", "label": "Cake", "value": "3.50"}, {"id": "pie", "label": "Pie", "value": "4.00"}]}, "saved": ["cake", "3.80"], "unsaved": ["pie", "4.75"]}];
const report={schema_version:'grist-tutorial-restart-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;
  const read=()=>page.evaluate(()=>({slide:document.querySelector('#slide').dataset.index,cells:Object.fromEntries([...document.querySelectorAll('#grid input')].map(i=>[i.dataset.row,i.dataset.stored]))}));
  const initial=Object.fromEntries(fixture.state.rows.map(r=>[r.id,r.value]));
  const before=await read();
  if(before.slide!==String(fixture.state.slide)||JSON.stringify(before.cells)!==JSON.stringify(initial))throw new InterfaceError('tutorial state changed before editing');
  async function edit([id,value]){const input=await one(page,`#grid input[data-row="${id}"]`);await input.fill(value);await input.press('Tab')}
  if(fixture.saved){await edit(fixture.saved);await (await one(page,'#replace')).click()}
  await edit(fixture.unsaved);
  if((await read()).cells[fixture.unsaved[0]]!==fixture.unsaved[1])throw new InterfaceError('edit not applied to the fork');
  await page.evaluate(()=>{window.__beforeRestart=true});
  await (await one(page,'#restart')).click();
  await page.waitForTimeout(500);await page.waitForLoadState('load');
  const refreshed=await page.evaluate(()=>window.__beforeRestart!==true);
  const after=await read();
  check(`unsaved_edit_lost_${n}`,after.cells[fixture.unsaved[0]]===initial[fixture.unsaved[0]]);
  check(`page_refreshed_${n}`,refreshed);
  check(`tutorial_restarted_${n}`,after.slide==='0');
  if(fixture.saved)check(`saved_edit_kept_${n}`,after.cells[fixture.saved[0]]===fixture.saved[1]);
  else check(`other_rows_unchanged_${n}`,Object.entries(initial).every(([k,v])=>k===fixture.unsaved[0]||after.cells[k]===v));
}
async function runFixture(browser,fixture,index){const context=await browser.newContext({viewport:{width:1000,height:760},timezoneId:'UTC',serviceWorkers:'block'});
  try{
    await context.addInitScript(initial=>Object.defineProperty(window,'initialState',{value:initial}),fixture.state);
    await context.route('**/*',route=>route.request().url()===URL&&route.request().isNavigationRequest()
      ?route.fulfill({body:html,contentType:'text/html',headers:{'Content-Security-Policy':CSP}}):route.abort());
    const page=await context.newPage();page.setDefaultTimeout(2500);
    page.on('console',m=>{if(m.type()==='error'&&report.console_errors.length<20)report.console_errors.push(m.text().slice(0,500))});
    page.on('pageerror',e=>{if(report.console_errors.length<20)report.console_errors.push(String(e).slice(0,500))});
    await page.goto(URL,{waitUntil:'load',timeout:10000});
    if(!await page.evaluate(()=>typeof behavior==='function'))throw new InterfaceError('behavior handler not registered');
    await journey(page,fixture,index);
    await page.screenshot({path:`/output/fixture-${index+1}.png`,fullPage:true});
  }finally{await context.close()}
}
(async()=>{let browser;try{browser=await chromium.launch({headless:true,chromiumSandbox:false});
  for(let i=0;i<fixtures.length;i++)await runFixture(browser,fixtures[i],i);
  report.status='complete';report.screenshots=['fixture-1.png','fixture-2.png'];
}catch(error){report.status=report.console_errors.length?'browser_error':error instanceof InterfaceError?'interface_error':'browser_error';report.assertions={};report.error=String(error).slice(0,1500);
}finally{if(browser)await browser.close();fs.writeFileSync('/output/report.json',JSON.stringify(report,null,2));process.exitCode=report.status==='complete'?0:2}})();
