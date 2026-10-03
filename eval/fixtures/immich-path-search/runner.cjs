'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"assets": [{"id": "a1", "originalPath": "/John/Projects/3D_Printing/2026-07-01/IMG_0001.jpg"}, {"id": "a2", "originalPath": "/John/Holidays/Lisbon/IMG_2001.jpg"}, {"id": "a3", "originalPath": "/Maria/Recipes/Bread/IMG_3001.jpg"}]}, "queries": [["Printing", ["a1"], true], ["3D", ["a1"], true], ["Holidays", ["a2"], false], ["Kitchen", [], false]]}, {"state": {"assets": [{"id": "b1", "originalPath": "/Ana/Work/Client_Reports/2025-11/scan_004.png"}, {"id": "b2", "originalPath": "/Ana/Family/Birthday/IMG_0005.jpg"}, {"id": "b3", "originalPath": "/Rui/Work/Invoices/inv_17.png"}]}, "queries": [["Reports", ["b1"], true], ["2025", ["b1"], true], ["Family", ["b2"], false], ["Work", ["b1", "b3"], false]]}];
const report={schema_version:'immich-path-search-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;let target=true,other=true;
  if(await page.locator('#results li').count()!==0)throw new InterfaceError('results present before searching');
  for(const [query,expected,isTarget] of fixture.queries){
    await (await one(page,'#query')).fill(query);await (await one(page,'#search')).click();
    const got=(await page.locator('#results li').evaluateAll(ns=>ns.map(x=>x.dataset.id))).sort();
    // target queries: the matching asset must be included; other queries: the exact result set
    if(isTarget)target=target&&expected.every(id=>got.includes(id));
    else other=other&&JSON.stringify(got)===JSON.stringify([...expected].sort());
  }
  check(`part_of_folder_name_matches_${n}`,target);
  check(`whole_folder_and_no_match_${n}`,other);
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
