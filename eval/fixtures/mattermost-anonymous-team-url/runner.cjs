'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"config": {"anonymousUrls": true, "enableOpenServer": true, "restrictCreationToDomains": ""}, "teams": [{"name": "Engineering", "url": "engineering"}]}, "name": "Release Crew", "url": "release-crew"}, {"state": {"config": {"anonymousUrls": false, "enableOpenServer": true, "restrictCreationToDomains": ""}, "teams": [{"name": "Sales", "url": "sales"}, {"name": "Marketing", "url": "marketing"}]}, "name": "Support Desk", "url": "help-desk-emea"}];
const report={schema_version:'mattermost-anonymous-team-url-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;const before=fixture.state.teams;
  const teams=()=>page.locator('#teams li').evaluateAll(ns=>ns.map(x=>({name:x.dataset.name,url:x.dataset.url})));
  if(JSON.stringify(await teams())!==JSON.stringify(before)||await page.locator('#url-step').isVisible())throw new InterfaceError('teams changed or URL step open before creating');
  await (await one(page,'#team-name')).fill(fixture.name);await (await one(page,'#next')).click();await page.waitForTimeout(100);
  const prompted=await page.locator('#url-step').isVisible();
  const early=(await teams()).filter(t=>t.name===fixture.name);
  if(prompted){await (await one(page,'#team-url')).fill(fixture.url);await (await one(page,'#finish')).click();await page.waitForTimeout(100)}
  await reload(page);
  const after=await teams();const created=after.filter(t=>t.name===fixture.name);
  const kept=before.every(b=>after.some(t=>t.name===b.name&&t.url===b.url));
  if(fixture.state.config.anonymousUrls){
    check('url_assigned_without_prompt_1',!prompted&&early.length===1&&/^[a-z][a-z0-9-]{0,62}[a-z0-9]$/.test(early[0].url)&&!before.some(b=>b.url===early[0].url));
    check('team_created_once_1',created.length===1);
    check('existing_teams_kept_1',kept);
  }else{
    check('url_step_shown_2',prompted&&early.length===0);
    check('chosen_url_saved_2',created.length===1&&created[0].url===fixture.url);
    check('existing_teams_kept_2',kept);
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
