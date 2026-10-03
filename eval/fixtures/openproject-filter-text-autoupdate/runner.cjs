'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"workPackages": [{"id": 101, "subject": "Invoice template redesign", "description": "Update the layout", "comments": ["Looks good"]}, {"id": 102, "subject": "Server migration", "description": "Move the archive to the new host", "comments": []}, {"id": 103, "subject": "Team offsite", "description": "Plan the agenda", "comments": ["Book the venue near the river"]}, {"id": 104, "subject": "Release notes", "description": "Write notes for 17.8", "comments": ["Mention the venue change"]}]}, "typed": ["Server", [102]], "entered": ["venue", [103, 104]]}, {"state": {"workPackages": [{"id": 201, "subject": "Login page broken", "description": "Users see a blank screen after the upgrade", "comments": []}, {"id": 202, "subject": "Database maintenance", "description": "Plan downtime", "comments": ["Backup first"]}, {"id": 203, "subject": "Onboarding checklist", "description": "Steps for new hires", "comments": ["Add the upgrade guide link"]}, {"id": 204, "subject": "Budget review", "description": "Quarterly numbers", "comments": []}]}, "typed": ["Budget", [204]], "entered": ["upgrade", [201, 203]]}];
const report={schema_version:'openproject-filter-text-autoupdate-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;const rows=()=>page.locator('#rows tr').evaluateAll(ns=>ns.map(x=>Number(x.dataset.id)));
  const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);const all=fixture.state.workPackages.map(w=>w.id);
  if(!same(await rows(),all))throw new InterfaceError('table does not show all work packages');
  const field=await one(page,'#filter-text');
  await field.click();await field.pressSequentially(fixture.typed[0]);await page.waitForTimeout(500);
  check(`results_update_while_typing_${n}`,same(await rows(),fixture.typed[1]));
  await field.fill('');await field.pressSequentially(fixture.entered[0]);await field.press('Enter');await page.waitForTimeout(300);
  check(`text_matches_subject_description_comments_${n}`,same(await rows(),fixture.entered[1]));
  await field.fill('');await field.press('Enter');await page.waitForTimeout(300);
  check(`empty_text_shows_all_${n}`,same(await rows(),all));
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
