'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"workflow": "Apply AI Suggestions", "documents": [{"id": "d1", "title": "Invoice March", "content": "Invoice 2026-03, total 120 EUR, due 30 April."}, {"id": "d2", "title": "Blank scan", "content": "   \n\t  \n"}, {"id": "d3", "title": "Letter", "content": "Dear customer, thank you for your order."}]}, "blank": ["d2"], "text": ["d1", "d3"]}, {"state": {"workflow": "Apply AI Suggestions", "documents": [{"id": "e1", "title": "Receipt", "content": ""}, {"id": "e2", "title": "Contract", "content": "Contract between Alpha Ltd and Beta GmbH."}, {"id": "e3", "title": "Photo of whiteboard", "content": "\n\n   "}]}, "blank": ["e1", "e3"], "text": ["e2"]}];
const report={schema_version:'paperless-ai-suggestions-blank-text-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;const ids=fixture.state.documents.map(d=>d.id);
  const before=await page.locator('#documents li').evaluateAll(ns=>ns.map(x=>[x.dataset.id,x.dataset.queued]));
  if(JSON.stringify(before)!==JSON.stringify(ids.map(id=>[id,'0'])))throw new InterfaceError('documents missing or queued before the run');
  await (await one(page,'#run')).click();await reload(page);
  const after=Object.fromEntries(await page.locator('#documents li').evaluateAll(ns=>ns.map(x=>[x.dataset.id,Number(x.dataset.queued)])));
  check(`blank_documents_skipped_${n}`,fixture.blank.every(id=>after[id]===0));
  check(`text_documents_queued_once_${n}`,fixture.text.every(id=>after[id]===1));
  check(`documents_preserved_${n}`,JSON.stringify(Object.keys(after))===JSON.stringify(ids));
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
