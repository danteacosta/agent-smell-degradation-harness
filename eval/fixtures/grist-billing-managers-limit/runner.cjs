'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"managers": ["finance1@acme.test", "finance2@acme.test", "finance3@acme.test", "finance4@acme.test", "finance5@acme.test", "finance6@acme.test", "finance7@acme.test", "finance8@acme.test"]}, "allowed": ["cfo@acme.test", "audit@acme.test"], "refused": ["intern@acme.test"]}, {"state": {"managers": ["ana@team.test", "ben@team.test", "chen@team.test"]}, "allowed": ["dara@team.test", "eli@team.test", "fay@team.test", "gus@team.test", "hana@team.test", "ivo@team.test", "jun@team.test"], "refused": ["kai@team.test", "lea@team.test"]}];
const report={schema_version:'grist-billing-managers-limit-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;const list=()=>page.locator('#managers li').evaluateAll(ns=>ns.map(x=>x.dataset.email));
  if(JSON.stringify(await list())!==JSON.stringify(fixture.state.managers))throw new InterfaceError('billing managers missing before adding');
  async function add(email){await (await one(page,'#email')).fill(email);await (await one(page,'#add')).click();await reload(page)}
  for(const email of fixture.allowed)await add(email);
  const expected=[...fixture.state.managers,...fixture.allowed];
  check(`managers_added_${n}`,JSON.stringify(await list())===JSON.stringify(expected));
  for(const email of fixture.refused)await add(email);
  const after=await list();
  check(`no_more_than_ten_${n}`,after.length<=10&&!fixture.refused.some(e=>after.includes(e)));
  check(`existing_managers_kept_${n}`,expected.every(e=>after.includes(e)));
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
