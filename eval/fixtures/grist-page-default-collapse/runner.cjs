'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"pages": [{"id": "sales", "name": "Sales", "parent": null}, {"id": "q1", "name": "Q1", "parent": "sales"}, {"id": "q2", "name": "Q2", "parent": "sales"}, {"id": "contacts", "name": "Contacts", "parent": null}, {"id": "people", "name": "People", "parent": "contacts"}, {"id": "summary", "name": "Summary", "parent": null}]}, "target": "sales", "manual": null}, {"state": {"pages": [{"id": "projects", "name": "Projects", "parent": null}, {"id": "alpha", "name": "Alpha", "parent": "projects"}, {"id": "beta", "name": "Beta", "parent": "projects"}, {"id": "gamma", "name": "Gamma", "parent": "projects"}, {"id": "team", "name": "Team", "parent": null}, {"id": "members", "name": "Members", "parent": "team"}, {"id": "roles", "name": "Roles", "parent": "team"}, {"id": "archive", "name": "Archive", "parent": null}, {"id": "y2024", "name": "2024", "parent": "archive"}]}, "target": "team", "manual": "projects"}];
const report={schema_version:'grist-page-default-collapse-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;const pages=fixture.state.pages;const parents=pages.filter(p=>p.parent===null).map(p=>p.id);
  const kids=id=>pages.filter(p=>p.parent===id).length;
  const shown=()=>page.locator('#pages > li').evaluateAll(ns=>Object.fromEntries(ns.map(li=>[li.dataset.id,li.querySelectorAll('li[data-parent]').length])));
  const first=await shown();
  if(JSON.stringify(Object.keys(first))!==JSON.stringify(parents)||!await page.locator('#page-menu').isHidden())throw new InterfaceError('page list missing or menu open');
  check(`nested_expanded_on_open_${n}`,parents.every(id=>first[id]===kids(id)));
  if(fixture.manual)await (await one(page,`#pages > li[data-id="${fixture.manual}"] > .toggle`)).click();
  await (await one(page,`#pages > li[data-id="${fixture.target}"] > .more`)).click();
  const items=page.locator('#page-menu button');let picked=false;const count=await items.count();
  for(let i=0;i<count;i++){const item=items.nth(i);if(/^set default:\s*collapse$/i.test((await item.innerText()).trim())&&await item.isVisible()){await item.click();picked=true;break}}
  await reload(page);
  const after=await shown();
  check(`collapsed_on_reopen_${n}`,picked&&fixture.target in after&&after[fixture.target]===0);
  check(`other_pages_expanded_on_reopen_${n}`,parents.filter(id=>id!==fixture.target).every(id=>after[id]===kids(id)));
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
