'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"team": "Acme", "channels": [{"id": "c1", "name": "Project Falcon"}, {"id": "c2", "name": "Vendor Support"}, {"id": "c3", "name": "Design Review"}]}, "steps": [{"email": "ana@partner.example", "channels": [], "message": ""}, {"email": "ben@partner.example", "channels": ["c2", "c3"], "message": ""}]}, {"state": {"team": "Northwind", "channels": [{"id": "d1", "name": "Onboarding"}, {"id": "d2", "name": "Q4 Launch"}]}, "steps": [{"email": "carla@agency.example", "channels": ["d1"], "message": "Welcome aboard!"}, {"email": "dev@agency.example", "channels": [], "message": "See you there."}]}];
const report={schema_version:'mattermost-guest-invite-channel-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;
  const invites=()=>page.locator('#invitations li').evaluateAll(ns=>ns.map(x=>({email:x.dataset.email,channels:x.dataset.channels?x.dataset.channels.split(',').sort():[]})));
  if((await invites()).length!==0||await page.locator('input[name=channel]').count()!==fixture.state.channels.length)throw new InterfaceError('channel choices missing or invitations present');
  for(const step of fixture.steps){
    await (await one(page,'#guest-email')).fill(step.email);
    if(step.message)await (await one(page,'#guest-message')).fill(step.message);
    for(const id of step.channels)await page.locator(`input[name=channel][value="${id}"]`).check();
    if(step.channels.length)await (await one(page,'#invite')).click();
    else{const b=page.locator('#invite');if(await b.count()===1&&await b.isVisible()&&await b.isEnabled())await b.click()}
    await page.waitForTimeout(100);await reload(page);
  }
  const all=await invites();
  const invalid=fixture.steps.find(s=>!s.channels.length),valid=fixture.steps.find(s=>s.channels.length);
  check(`no_invite_without_channel_${n}`,!all.some(i=>i.email===invalid.email));
  const sent=all.filter(i=>i.email===valid.email);
  check(`invite_limited_to_selected_channels_${n}`,sent.length===1&&JSON.stringify(sent[0].channels)===JSON.stringify([...valid.channels].sort()));
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
