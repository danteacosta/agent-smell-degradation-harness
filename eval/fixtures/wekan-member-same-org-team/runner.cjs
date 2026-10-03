'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"actor": {"id": "u0", "isAdmin": false}, "settings": {"boardMembersFromSameOrgOnly": true, "boardMembersFromSameTeamOnly": false}, "users": [{"id": "u0", "username": "maria", "orgs": ["acme"], "teams": ["design"]}, {"id": "u5", "username": "lee", "orgs": ["globex"], "teams": []}, {"id": "u6", "username": "kim", "orgs": ["initech"], "teams": []}, {"id": "u1", "username": "ana", "orgs": ["acme"], "teams": []}, {"id": "u2", "username": "ben", "orgs": [], "teams": ["design"]}, {"id": "u3", "username": "cai", "orgs": ["globex"], "teams": []}, {"id": "u4", "username": "dev", "orgs": ["initech"], "teams": []}, {"id": "u7", "username": "eve", "orgs": ["umbrella"], "teams": ["sales"]}], "members": [{"userId": "u0", "isActive": true}, {"userId": "u5", "isActive": true}, {"userId": "u6", "isActive": false}]}, "inviter_share": ["u1"], "member_share": ["u3"], "blocked": ["u2", "u4", "u7"]}, {"state": {"actor": {"id": "v0", "isAdmin": false}, "settings": {"boardMembersFromSameOrgOnly": false, "boardMembersFromSameTeamOnly": true}, "users": [{"id": "v0", "username": "jon", "orgs": ["north"], "teams": ["ops"]}, {"id": "v5", "username": "ivy", "orgs": [], "teams": ["qa"]}, {"id": "v6", "username": "rob", "orgs": ["south"], "teams": ["sales"]}, {"id": "v1", "username": "zoe", "orgs": [], "teams": ["ops"]}, {"id": "v2", "username": "tom", "orgs": ["east"], "teams": ["qa"]}, {"id": "v3", "username": "liz", "orgs": ["north"], "teams": []}, {"id": "v4", "username": "sam", "orgs": [], "teams": ["sales"]}], "members": [{"userId": "v0", "isActive": true}, {"userId": "v5", "isActive": true}, {"userId": "v6", "isActive": false}]}, "inviter_share": ["v1"], "member_share": ["v2"], "blocked": ["v3", "v4"]}];
const report={schema_version:'wekan-member-same-org-team-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;const initial=fixture.state.members.map(m=>m.userId);
  const read=()=>page.locator('#members li').evaluateAll(ns=>ns.map(x=>x.dataset.user));
  const attempts=[...fixture.blocked,...fixture.member_share,...fixture.inviter_share];
  if(JSON.stringify(await read())!==JSON.stringify(initial))throw new InterfaceError('members missing before adding');
  await one(page,'#user');
  for(const id of attempts){await reload(page);const select=await one(page,'#user');
    if(!(await select.locator('option').evaluateAll(ns=>ns.map(x=>x.value))).includes(id))continue;
    await select.selectOption(id);await (await one(page,'#add')).click()}
  await reload(page);const after=await read();const count=id=>after.filter(x=>x===id).length;
  check(`unshared_users_blocked_${n}`,fixture.blocked.every(id=>count(id)===0));
  check(`active_member_share_added_${n}`,fixture.member_share.every(id=>count(id)>=1));
  check(`inviter_share_added_${n}`,fixture.inviter_share.every(id=>count(id)>=1));
  check(`members_list_intact_${n}`,JSON.stringify(after.slice(0,initial.length))===JSON.stringify(initial)&&new Set(after).size===after.length);
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
