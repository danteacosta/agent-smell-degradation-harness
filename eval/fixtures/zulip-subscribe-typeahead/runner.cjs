'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"channel": "design", "subscribers": ["u1", "u4"], "users": [{"id": "u1", "name": "Anna Lee", "email": "anna@example.com"}, {"id": "u2", "name": "Andrés Silva", "email": "andres@example.com"}, {"id": "u3", "name": "Bo Andersen", "email": "bo@example.com"}, {"id": "u4", "name": "Carl Smith", "email": "carl@example.com"}, {"id": "u5", "name": "Mei Wong", "email": "mei@example.com"}]}, "before": [["an", ["u2", "u3"], ["u1"]], ["mei@", ["u5"], []], ["carl", [], ["u4"]]], "add": ["an", "u2"], "after": [["an", ["u3"], ["u1", "u2"]]]}, {"state": {"channel": "support", "subscribers": ["v1", "v4"], "users": [{"id": "v1", "name": "Priya Shah", "email": "priya@corp.test"}, {"id": "v2", "name": "Priya Nair", "email": "pnair@corp.test"}, {"id": "v3", "name": "Sam Price", "email": "sprice@corp.test"}, {"id": "v4", "name": "Lee Wong", "email": "lwong@corp.test"}, {"id": "v5", "name": "Leela Rao", "email": "leela@corp.test"}]}, "before": [["pri", ["v2", "v3"], ["v1"]], ["pnair", ["v2"], []], ["le", ["v5"], ["v4"]]], "add": ["le", "v5"], "after": [["le", [], ["v4", "v5"]], ["pri", ["v2", "v3"], ["v1"]]]}];
const report={schema_version:'zulip-subscribe-typeahead-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;
  const subs=()=>page.locator('#subscribers li').evaluateAll(ns=>ns.map(x=>x.dataset.id));
  const sugg=()=>page.locator('#typeahead li').evaluateAll(ns=>ns.map(x=>x.dataset.id));
  if(JSON.stringify(await subs())!==JSON.stringify(fixture.state.subscribers)||(await sugg()).length!==0)throw new InterfaceError('subscribers changed or suggestions shown before typing');
  let excluded=true,included=true,precise=true;
  async function query([q,expected,subscribedMatches]){
    await (await one(page,'#add-subscriber')).fill(q);await page.waitForTimeout(250);
    const got=await sugg();const current=await subs();
    excluded=excluded&&got.every(id=>!current.includes(id));
    included=included&&expected.every(id=>got.includes(id));
    precise=precise&&new Set(got).size===got.length&&got.every(id=>expected.includes(id)||subscribedMatches.includes(id));
  }
  for(const q of fixture.before)await query(q);
  const [addQuery,addUser]=fixture.add;
  await (await one(page,'#add-subscriber')).fill(addQuery);await page.waitForTimeout(250);
  const option=page.locator(`#typeahead li[data-id="${addUser}"]`);
  if(await option.count()===1&&await option.isVisible())await option.click();
  await (await one(page,'#add')).click();
  const added=(await subs()).includes(addUser);
  for(const q of fixture.after)await query(q);
  await reload(page);const persisted=(await subs()).includes(addUser);
  check(`subscribed_users_excluded_${n}`,excluded);
  check(`unsubscribed_matches_suggested_${n}`,included&&added&&persisted);
  check(`non_matching_users_excluded_${n}`,precise);
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
