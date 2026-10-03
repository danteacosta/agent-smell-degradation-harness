'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"actor": {"id": "u1", "name": "Lena", "role": "member"}, "channels": [{"id": "c1", "name": "leadership", "privacy": "private", "subscribers": ["u1", "u2"], "topics": ["Q3 hiring plan", "offsite agenda"]}, {"id": "c2", "name": "general", "privacy": "public", "subscribers": ["u2", "u3"], "topics": ["welcome", "lunch on Friday"]}]}, "private": "c1", "public": "c2"}, {"state": {"actor": {"id": "g1", "name": "Kim", "role": "guest"}, "channels": [{"id": "d1", "name": "announcements", "privacy": "public", "subscribers": ["u5", "u6"], "topics": ["new office", "holiday schedule"]}, {"id": "d2", "name": "client acme", "privacy": "private", "subscribers": ["g1", "u5"], "topics": ["contract renewal", "launch checklist", "weekly sync"]}]}, "private": "d2", "public": "d1"}];
const report={schema_version:'zulip-private-channel-access-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;
  const shown=()=>page.locator('#conversation').evaluate(x=>({channel:x.dataset.channel,topics:[...x.querySelectorAll('#topics li')].map(t=>t.dataset.topic)}));
  if((await shown()).channel!=='')throw new InterfaceError('conversations shown before opening a channel');
  async function open(id){await (await one(page,`#channels button[data-channel="${id}"]`)).click();await page.waitForTimeout(100);return shown()}
  const sees=(r,id)=>r.channel===id&&JSON.stringify(r.topics)===JSON.stringify(fixture.state.channels.find(c=>c.id===id).topics);
  if(n===1){
    check('granted_user_sees_private_1',sees(await open(fixture.private),fixture.private));
    check('member_sees_unsubscribed_public_1',sees(await open(fixture.public),fixture.public));
  }else{
    check('guest_kept_out_of_unsubscribed_public_2',(await open(fixture.public)).channel!==fixture.public);
    check('granted_guest_sees_private_2',sees(await open(fixture.private),fixture.private));
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
