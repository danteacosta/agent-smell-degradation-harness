'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"channel": "deploys", "currentUser": "alice", "members": ["alice", "bob"], "users": [{"username": "alice"}, {"username": "bob"}, {"username": "carol"}, {"username": "dan"}]}, "text": "@carol can you review the deploy plan? cc @bob", "nonmembers": ["carol"], "mentioned_members": ["bob"], "add": "carol"}, {"state": {"channel": "launch-room", "currentUser": "erin", "members": ["erin", "frank", "gina"], "users": [{"username": "erin"}, {"username": "frank"}, {"username": "gina"}, {"username": "hal"}, {"username": "ivy"}]}, "text": "@hal and @ivy please join the call, @frank FYI", "nonmembers": ["hal", "ivy"], "mentioned_members": ["frank"], "add": "ivy"}];
const report={schema_version:'mattermost-mention-add-prompt-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;
  const members=()=>page.locator('#members li').evaluateAll(ns=>ns.map(x=>x.dataset.username));
  const posts=()=>page.locator('#posts li').evaluateAll(ns=>ns.map(x=>x.dataset.text));
  const names=u=>new RegExp('(^|[^a-z0-9._-])@?'+u+'(?![a-z0-9._-])','i');
  if(JSON.stringify(await members())!==JSON.stringify(fixture.state.members)||(await posts()).length||await page.locator('#notices li').count())throw new InterfaceError('channel changed before sending');
  await (await one(page,'#message')).fill(fixture.text);await (await one(page,'#send')).click();await page.waitForTimeout(100);
  const notices=await page.locator('#notices li').evaluateAll(ns=>ns.map(x=>x.textContent));
  const afterSend=await members();
  check(`nonmember_prompted_not_added_${n}`,fixture.nonmembers.every(u=>notices.some(t=>names(u).test(t))&&!afterSend.includes(u)));
  check(`member_not_prompted_${n}`,fixture.mentioned_members.every(u=>!notices.some(t=>names(u).test(t))));
  const notice=page.locator('#notices li').filter({hasText:names(fixture.add)});
  if(await notice.count()>=1&&await notice.first().locator('button').count()>=1){await notice.first().locator('button').first().click();await page.waitForTimeout(100)}
  await reload(page);
  const after=await members();
  check(`prompt_adds_nonmember_${n}`,after.includes(fixture.add));
  check(`message_posted_once_${n}`,JSON.stringify(await posts())===JSON.stringify([fixture.text]));
  check(`existing_members_kept_${n}`,fixture.state.members.every(u=>after.includes(u)));
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
