'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"user": {"id": 7, "name": "Lena"}, "settings": {"readOnScroll": "always"}, "topics": [{"id": "t1", "name": "login page down", "resolved": false}, {"id": "t2", "name": "invoice export", "resolved": false}], "messages": [{"id": 1, "topic": "t1", "sender": "Omar", "content": "Login returns 502.", "read": true}, {"id": 2, "topic": "t2", "sender": "Ana", "content": "CSV export is empty.", "read": false}]}, "steps": [["t1", true], ["t1", false]]}, {"state": {"user": {"id": 9, "name": "Rui"}, "settings": {"readOnScroll": "conversation"}, "topics": [{"id": "t3", "name": "build flaky", "resolved": false}, {"id": "t4", "name": "printer offline", "resolved": true}, {"id": "t5", "name": "vpn access", "resolved": false}], "messages": [{"id": 11, "topic": "t3", "sender": "Kim", "content": "Test 14 fails at random.", "read": false}, {"id": 12, "topic": "t4", "sender": "Notification Bot", "content": "@Kim has marked this topic as resolved.", "read": true}, {"id": 13, "topic": "t5", "sender": "Ivo", "content": "Who can grant VPN access?", "read": true}]}, "steps": [["t3", false], ["t4", true]]}];
const report={schema_version:'zulip-resolved-notice-auto-read-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;
  const msgs=()=>page.locator('#messages li').evaluateAll(ns=>ns.map(x=>({id:x.dataset.id,topic:x.dataset.topic,sender:x.dataset.sender,read:x.dataset.read})));
  const topics=()=>page.locator('#topics li').evaluateAll(ns=>Object.fromEntries(ns.map(x=>[x.dataset.id,x.dataset.resolved])));
  const init=await msgs();
  if(JSON.stringify(init.map(m=>[m.id,m.read]))!==JSON.stringify(fixture.state.messages.map(m=>[String(m.id),String(m.read)])))throw new InterfaceError('messages missing or changed before acting');
  async function setOption(on){
    const c=page.getByLabel(/mark resolved topic notices as read/i);
    if(await c.count()!==1||!await c.isVisible()||!await c.isEnabled())return false;
    const kind=await c.evaluate(x=>x.tagName+':'+(x.type||''));
    if(kind==='INPUT:checkbox'){await c.setChecked(on);return true}
    if(kind.startsWith('SELECT')){
      const opts=await c.locator('option').evaluateAll(os=>os.map(o=>[o.value,o.textContent.trim()]));
      const re=on?/^(always|yes|on|enabled?|true)$/i:/^(never|no|off|disabled?|false)$/i;
      const o=opts.find(([v,t])=>re.test(t)||re.test(v));if(!o)return false;await c.selectOption(o[0]);return true}
    return false}
  const seen=new Set(init.map(m=>m.id));let readOk=true,unreadOk=true,posted=true,toggled=true;
  for(const [topic,on] of fixture.steps){
    const before=(await topics())[topic];
    const set=await setOption(on);
    await (await one(page,`#topics button[data-topic="${topic}"]`)).click();await page.waitForTimeout(100);await reload(page);
    const now=(await topics())[topic];
    const fresh=(await msgs()).filter(m=>!seen.has(m.id));fresh.forEach(m=>seen.add(m.id));
    const notices=fresh.filter(m=>m.topic===topic&&m.sender==='Notification Bot');
    posted=posted&&fresh.length===1&&notices.length===1;
    toggled=toggled&&now===String(before!=='true');
    if(on)readOk=readOk&&set&&notices.every(m=>m.read==='true');
    else unreadOk=unreadOk&&set&&notices.every(m=>m.read==='false');
  }
  const final=await msgs();
  check(`notice_read_when_enabled_${n}`,readOk);
  check(`notice_unread_when_disabled_${n}`,unreadOk);
  check(`notice_posted_for_each_change_${n}`,posted);
  check(`topic_state_toggled_${n}`,toggled);
  check(`other_messages_unchanged_${n}`,init.every(m=>final.some(f=>f.id===m.id&&f.read===m.read)));
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
