'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"projects": [{"id": "pr1", "name": "Website relaunch"}, {"id": "pr2", "name": "Data center"}], "current": "pr1", "roles": [{"id": "r1", "name": "Member"}, {"id": "r2", "name": "Reader"}], "principals": [{"id": "u1", "name": "Alice Wong", "kind": "user"}, {"id": "u2", "name": "Ben Ortiz", "kind": "user"}, {"id": "g1", "name": "Design team", "kind": "group"}, {"id": "g2", "name": "Support staff", "kind": "group"}, {"id": "ph1", "name": "Contractor TBD", "kind": "placeholder_user"}, {"id": "ph2", "name": "Future tester", "kind": "placeholder_user"}], "members": [{"project": "pr1", "principal": "u1", "kind": "user", "name": "Alice Wong", "email": "", "role": "r1"}]}, "first": {"project": "pr2", "name": "new.person@example.org", "role": "r2"}, "second": {"kind": "group", "project": "pr1", "name": "Design team", "id": "g1", "role": "r1"}}, {"state": {"projects": [{"id": "pq1", "name": "Mobile app"}, {"id": "pq2", "name": "Office move"}], "current": "pq2", "roles": [{"id": "s1", "name": "Project admin"}, {"id": "s2", "name": "Member"}], "principals": [{"id": "u1", "name": "Alice Wong", "kind": "user"}, {"id": "u2", "name": "Ben Ortiz", "kind": "user"}, {"id": "g1", "name": "Design team", "kind": "group"}, {"id": "g2", "name": "Support staff", "kind": "group"}, {"id": "ph1", "name": "Contractor TBD", "kind": "placeholder_user"}, {"id": "ph2", "name": "Future tester", "kind": "placeholder_user"}], "members": [{"project": "pq2", "principal": "g2", "kind": "group", "name": "Support staff", "email": "", "role": "s2"}]}, "first": {"project": "pq2", "name": "Ben Ortiz", "id": "u2", "role": "s1"}, "second": {"kind": "placeholder_user", "project": "pq1", "name": "Contractor TBD", "id": "ph1", "role": "s2"}}];
const report={schema_version:'openproject-invite-permission-basis-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;const dlg=page.locator('#invite');
  const members=()=>page.locator('#members li').evaluateAll(ns=>ns.map(x=>({...x.dataset})));
  if((await members()).length!==fixture.state.members.length||await dlg.isVisible())throw new InterfaceError('members changed or dialog open before inviting');
  const KIND={user:/^\s*(an?\s+)?(existing\s+)?users?(\s+role)?\s*$/i,group:/^\s*(an?\s+)?groups?\b/i,placeholder_user:/placeholder/i};
  async function choose(re){
    const radio=dlg.getByRole('radio',{name:re});if(await radio.count()===1&&await radio.isVisible()){await radio.check();return true}
    for(const s of await dlg.locator('select').all()){const id=await s.getAttribute('id');if(id==='invite-project'||id==='invite-role'||!await s.isVisible())continue;
      const hit=(await s.locator('option').evaluateAll(os=>os.map(o=>[o.value,o.textContent.trim()]))).filter(o=>re.test(o[1]));
      if(hit.length===1){await s.selectOption(hit[0][0]);return true}}
    const tab=dlg.getByRole('tab',{name:re});if(await tab.count()===1&&await tab.isVisible()){await tab.click();return true}
    const button=dlg.getByRole('button',{name:re});if(await button.count()===1&&await button.isVisible()){await button.click();return true}
    return false}
  async function invite(step){
    await (await one(page,'#invite-project')).selectOption(step.project);
    await (await one(page,'#invite-name')).fill(step.name);
    await (await one(page,'#invite-role')).selectOption(step.role);
    await (await one(page,'#invite-submit')).click();await reload(page)}
  const f=fixture.first;await (await one(page,'#open-invite')).click();await choose(KIND.user);await invite(f);
  const after1=await members();
  if(n===1)check('new_user_invited_by_email_1',after1.some(m=>m.email===f.name&&m.kind==='user'&&m.project===f.project&&m.role===f.role));
  else check('existing_user_added_2',after1.some(m=>m.principal===f.id&&m.kind==='user'&&m.project===f.project&&m.role===f.role));
  const s=fixture.second;let added=false;
  await (await one(page,'#open-invite')).click();
  if(await choose(KIND[s.kind])){await invite(s);added=(await members()).some(m=>m.principal===s.id&&m.kind===s.kind&&m.project===s.project&&m.role===s.role)}
  check(n===1?'group_basis_selectable_1':'placeholder_basis_selectable_2',added);
  const final=await members();
  check(`existing_members_kept_${n}`,fixture.state.members.every(e=>final.some(m=>m.project===e.project&&m.principal===e.principal&&m.role===e.role)));
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
