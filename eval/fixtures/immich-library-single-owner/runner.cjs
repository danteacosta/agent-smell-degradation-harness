'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"users": [{"id": "u1", "name": "Alice"}, {"id": "u2", "name": "Bob"}, {"id": "u3", "name": "Carol"}]}, "multi": ["u1", "u2"], "multi_name": "Photos NAS", "single": "u3", "single_name": "Archive"}, {"state": {"users": [{"id": "v1", "name": "Dan"}, {"id": "v2", "name": "Erin"}, {"id": "v3", "name": "Femi"}]}, "multi": ["v1", "v2", "v3"], "multi_name": "Family drive", "single": "v2", "single_name": "Camera roll"}];
const report={schema_version:'immich-library-single-owner-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;const libs=()=>page.locator('#libraries li').evaluateAll(ns=>ns.map(x=>({name:x.dataset.name,owners:x.dataset.owners.split(',')})));
  if((await libs()).length!==0||await page.locator('input[name=owner]').count()!==fixture.state.users.length)throw new InterfaceError('owner choices missing or libraries present');
  for(const id of fixture.multi){const b=page.locator(`input[name=owner][value="${id}"]`);if(await b.isEnabled())await b.click()}
  await (await one(page,'#library-name')).fill(fixture.multi_name);await (await one(page,'#create')).click();await reload(page);
  check(`no_multi_owner_library_${n}`,(await libs()).every(l=>l.owners.length===1));
  const b=page.locator(`input[name=owner][value="${fixture.single}"]`);await b.click();
  await (await one(page,'#library-name')).fill(fixture.single_name);await (await one(page,'#create')).click();await reload(page);
  const created=(await libs()).filter(l=>l.name===fixture.single_name);
  check(`single_owner_library_created_${n}`,created.length===1&&created[0].owners.length===1&&created[0].owners[0]===fixture.single);
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
