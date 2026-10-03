'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"groupNames": {"role:administrators": "Administrators", "role:moderators": "Moderators", "role:members": "Members", "design-team": "design-team", "eng-leads": "eng-leads"}, "actor": {"id": "u1", "name": "Lena", "groups": ["role:members", "design-team"]}, "users": [{"id": "u1", "name": "Lena"}, {"id": "u2", "name": "Omar"}, {"id": "u3", "name": "Ana"}], "channel": {"id": "c1", "name": "design reviews", "privacy": "private", "permissions": {"administer": ["role:administrators"], "subscribeSelf": ["role:administrators"], "subscribeAnyone": ["role:administrators"], "unsubscribeAnyone": ["role:administrators"]}}, "subscribers": ["u1", "u2", "u3"]}, "other": "u2", "other_allowed": false, "bystanders": ["u3"]}, {"state": {"groupNames": {"role:administrators": "Administrators", "role:moderators": "Moderators", "role:members": "Members", "design-team": "design-team", "eng-leads": "eng-leads"}, "actor": {"id": "v1", "name": "Omar", "groups": ["role:members", "eng-leads"]}, "users": [{"id": "v1", "name": "Omar"}, {"id": "v2", "name": "Kim"}, {"id": "v3", "name": "Rui"}, {"id": "v4", "name": "Ivo"}], "channel": {"id": "c2", "name": "engineering", "privacy": "public", "permissions": {"administer": ["role:administrators"], "subscribeSelf": ["role:members"], "subscribeAnyone": ["role:moderators"], "unsubscribeAnyone": ["role:moderators", "eng-leads"]}}, "subscribers": ["v2", "v1", "v3", "v4"]}, "other": "v3", "other_allowed": true, "bystanders": ["v2", "v4"]}];
const report={schema_version:'zulip-unsubscribe-self-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;const me=fixture.state.actor.id;
  const subs=()=>page.locator('#subscribers li').evaluateAll(ns=>ns.map(x=>x.dataset.id));
  if(JSON.stringify(await subs())!==JSON.stringify(fixture.state.subscribers))throw new InterfaceError('subscribers missing or changed');
  const selector=`#subscribers button[data-user="${fixture.other}"]`;
  if(fixture.other_allowed)await (await one(page,selector)).click();
  else{const other=page.locator(selector);if(await other.count()===1&&await other.isVisible()&&await other.isEnabled())await other.click()}
  await reload(page);const mid=await subs();
  await (await one(page,`#subscribers button[data-user="${me}"]`)).click();await reload(page);
  const after=await subs();
  check(`self_unsubscribed_${n}`,!after.includes(me));
  if(n===1)check('other_kept_without_permission_1',mid.includes(fixture.other)&&after.includes(fixture.other));
  else check('other_unsubscribed_with_permission_2',!mid.includes(fixture.other)&&!after.includes(fixture.other));
  check(`bystanders_kept_${n}`,fixture.bystanders.every(id=>after.includes(id)));
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
