'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"user": {"id": "u1", "name": "Ana"}, "docs": [{"id": "inventory", "name": "Inventory", "suggestions": false, "rows": [{"id": "bolts", "label": "Bolts", "value": "120"}, {"id": "nuts", "label": "Nuts", "value": "80"}]}, {"id": "survey", "name": "Survey results", "suggestions": true, "rows": [{"id": "q1", "label": "Question 1", "value": "Yes"}, {"id": "q2", "label": "Question 2", "value": "No"}]}]}, "plain": "inventory", "plain_edit": ["nuts", "95"], "suggested": "survey", "edit": ["q2", "Maybe"]}, {"state": {"user": null, "docs": [{"id": "budget", "name": "Public budget", "suggestions": true, "rows": [{"id": "parks", "label": "Parks", "value": "5000"}, {"id": "roads", "label": "Roads", "value": "9000"}, {"id": "library", "label": "Library", "value": "3000"}]}, {"id": "prices", "name": "Price list", "suggestions": false, "rows": [{"id": "tea", "label": "Tea", "value": "2.00"}]}]}, "plain": "prices", "plain_edit": null, "suggested": "budget", "edit": ["library", "3500"]}];
const report={schema_version:'grist-suggestions-open-copy-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;
  const view=()=>page.locator('#view').evaluate(v=>({shown:v.dataset.shown,copyOf:v.dataset.copyOf,cells:Object.fromEntries([...v.querySelectorAll('input[data-row]')].map(i=>[i.dataset.row,i.dataset.stored]))}));
  const originals=()=>page.locator('#docs li').evaluateAll(ns=>Object.fromEntries(ns.map(li=>[li.dataset.id,li.dataset.cells])));
  const cellsOf=id=>JSON.stringify(Object.fromEntries(fixture.state.docs.find(d=>d.id===id).rows.map(r=>[r.id,r.value])));
  const start=await originals();
  if((await view()).shown!==''||JSON.stringify(start)!==JSON.stringify(Object.fromEntries(fixture.state.docs.map(d=>[d.id,cellsOf(d.id)]))))throw new InterfaceError('documents missing or a document already open');
  async function edit([row,value]){const input=await one(page,`#view input[data-row="${row}"]`);await input.fill(value);await input.press('Tab')}
  await (await one(page,`#docs li[data-id="${fixture.plain}"] button.open`)).click();
  const plain=await view();
  check(`plain_document_opened_${n}`,plain.shown===fixture.plain&&plain.copyOf==='');
  if(fixture.plain_edit){
    if(plain.shown!=='')await edit(fixture.plain_edit);
    check(`plain_edit_live_${n}`,JSON.parse((await originals())[fixture.plain])[fixture.plain_edit[0]]===fixture.plain_edit[1]);
  }
  await (await one(page,`#docs li[data-id="${fixture.suggested}"] button.open`)).click();
  const opened=await view();
  check(`copy_opened_${n}`,opened.copyOf===fixture.suggested&&opened.shown!==fixture.suggested&&opened.shown!=='');
  if(opened.shown!=='')await edit(fixture.edit);
  const edited=await view();
  check(`edit_in_copy_${n}`,edited.copyOf===fixture.suggested&&edited.cells[fixture.edit[0]]===fixture.edit[1]);
  check(`original_unchanged_${n}`,(await originals())[fixture.suggested]===cellsOf(fixture.suggested));
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
