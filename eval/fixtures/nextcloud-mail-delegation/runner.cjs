'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"actor": "alice", "users": [{"id": "alice", "name": "Alice"}, {"id": "bob", "name": "Bob"}, {"id": "carol", "name": "Carol"}], "accounts": [{"id": "a1", "email": "alice@example.org", "owner": "alice", "provisioned": false}, {"id": "b1", "email": "bob@example.org", "owner": "bob", "provisioned": false}, {"id": "c1", "email": "carol@example.org", "owner": "carol", "provisioned": false}], "lists": {"alice": [{"accountId": "a1", "tag": "Default"}], "bob": [{"accountId": "b1", "tag": "Default"}], "carol": [{"accountId": "c1", "tag": "Default"}]}}, "delegate": ["a1", "bob"], "provisioned": null}, {"state": {"actor": "dana", "users": [{"id": "dana", "name": "Dana"}, {"id": "erin", "name": "Erin"}, {"id": "femi", "name": "Femi"}], "accounts": [{"id": "d1", "email": "dana@example.net", "owner": "dana", "provisioned": false}, {"id": "d2", "email": "team@example.net", "owner": "dana", "provisioned": false}, {"id": "d3", "email": "dana@corp.example.net", "owner": "dana", "provisioned": true}, {"id": "e1", "email": "erin@example.net", "owner": "erin", "provisioned": false}, {"id": "f1", "email": "femi@example.net", "owner": "femi", "provisioned": false}], "lists": {"dana": [{"accountId": "d1", "tag": "Default"}, {"accountId": "d2", "tag": ""}, {"accountId": "d3", "tag": ""}], "erin": [{"accountId": "e1", "tag": "Default"}], "femi": [{"accountId": "f1", "tag": "Default"}]}}, "delegate": ["d2", "femi"], "provisioned": ["d3", "erin"]}];
const report={schema_version:'nextcloud-mail-delegation-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;const [acc,user]=fixture.delegate;
  const state=()=>page.evaluate(()=>({acc:Object.fromEntries([...document.querySelectorAll('#accounts li')].map(x=>[x.dataset.id,x.dataset.delegates])),
    lists:Object.fromEntries([...document.querySelectorAll('#account-lists section')].map(s=>[s.dataset.user,[...s.querySelectorAll('li')].map(l=>[l.dataset.account,l.dataset.tag])]))}));
  const expected=Object.fromEntries(fixture.state.users.map(u=>[u.id,(fixture.state.lists[u.id]??[]).map(e=>[e.accountId,e.tag])]));
  const s0=await state();
  if(JSON.stringify(s0.lists)!==JSON.stringify(expected)||Object.values(s0.acc).some(v=>v!==''))throw new InterfaceError('accounts or account lists missing or changed');
  const usable=async sel=>{const x=page.locator(sel);return await x.count()===1&&await x.isVisible()&&await x.isEnabled()};
  const delegate=async(a,u,strict)=>{
    for(const sel of [`#accounts li[data-id="${a}"] button.delegate`,'#add-delegate','#user','#delegate-access']){
      if(!strict&&!await usable(sel))return;const node=await one(page,sel);
      if(sel==='#user')await node.selectOption(u);else await node.click()}
    await reload(page)};
  const delegatesOf=(s,a)=>(s.acc[a]||'').split(',').filter(Boolean);
  await delegate(acc,user,true);
  const s1=await state();const mine=(s1.lists[user]||[]).filter(e=>e[0]===acc);
  check(`delegate_sees_delegated_account_${n}`,mine.length===1&&/delegat/i.test(mine[0][1]||''));
  const recorded=delegatesOf(s1,acc).includes(user);
  check(`delegation_recorded_${n}`,recorded);
  check(`other_account_lists_unchanged_${n}`,Object.entries(expected).every(([u,l])=>JSON.stringify((s1.lists[u]||[]).filter(e=>!(u===user&&e[0]===acc)))===JSON.stringify(l)));
  if(fixture.provisioned){const [pa,pu]=fixture.provisioned;await delegate(pa,pu,false);await reload(page);const s=await state();
    check(`provisioned_not_delegated_${n}`,delegatesOf(s,pa).length===0&&!(s.lists[pu]||[]).some(e=>e[0]===pa))}
  await (await one(page,`#accounts li[data-id="${acc}"] button.delegate`)).click();
  const revoke=`#delegates li[data-user="${user}"] button.revoke`;
  if(await usable(revoke)){await page.locator(revoke).click();if(await usable('#revoke-access'))await page.locator('#revoke-access').click()}
  await reload(page);
  check(`revoke_removes_delegate_${n}`,recorded&&!delegatesOf(await state(),acc).includes(user));
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
