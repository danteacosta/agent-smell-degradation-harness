'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"action": {"field": "Invoice number", "value": null}, "documents": [{"id": "d1", "title": "Invoice A", "fields": {"Invoice number": "INV-1", "Due date": "2026-10-01"}}, {"id": "d2", "title": "Invoice B", "fields": {"Due date": "2026-11-01"}}]}}, {"state": {"action": {"field": "Invoice number", "value": "INV-9"}, "documents": [{"id": "e1", "title": "Invoice C", "fields": {"Invoice number": "INV-2", "Due date": "2026-12-01"}}, {"id": "e2", "title": "Invoice D", "fields": {"Due date": "2027-01-01"}}]}}];
const report={schema_version:'paperless-custom-field-no-value-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;
  const read=()=>page.locator('#documents li').evaluateAll(ns=>ns.map(li=>({id:li.dataset.id,fields:Object.fromEntries([...li.querySelectorAll('.field')].map(f=>[f.dataset.name,f.dataset.value]))})));
  const expect0=fixture.state.documents.map(d=>({id:d.id,fields:d.fields}));
  if(JSON.stringify(await read())!==JSON.stringify(expect0))throw new InterfaceError('documents changed before the action');
  await (await one(page,'#apply')).click();await reload(page);
  const [first,second]=await read();const field=fixture.state.action.field;
  const dueKept=[first,second].every((d,i)=>d&&d.fields['Due date']===fixture.state.documents[i].fields['Due date']);
  if(n===1){
    check('existing_value_kept_1',first?.fields[field]==='INV-1');
    check('field_added_empty_1',second?.fields[field]==='');
    check('other_fields_kept_1',dueKept);
  }else{
    check('value_overwrites_2',first?.fields[field]==='INV-9');
    check('value_added_2',second?.fields[field]==='INV-9');
    check('other_fields_kept_2',dueKept);
  }
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
