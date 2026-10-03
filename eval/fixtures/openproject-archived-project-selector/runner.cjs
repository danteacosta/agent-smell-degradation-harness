'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"current": "p3", "projects": [{"id": "p1", "name": "Marketing campaign", "archived": false}, {"id": "p2", "name": "Mobile app", "archived": false}, {"id": "p3", "name": "Market research", "archived": false}, {"id": "p4", "name": "Office move", "archived": false}]}, "query": "Mar", "query_active": ["p1"], "open_next": "p2"}, {"state": {"current": "q4", "projects": [{"id": "q1", "name": "Website relaunch", "archived": false}, {"id": "q2", "name": "Web shop", "archived": true}, {"id": "q3", "name": "Customer portal", "archived": false}, {"id": "q4", "name": "Wiki cleanup", "archived": false}]}, "query": "Web", "query_active": ["q1"], "open_next": "q3"}];
const report={schema_version:'openproject-archived-project-selector-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;const cur=fixture.state.current;const projects=fixture.state.projects;
  const current=()=>page.locator('#current').evaluate(x=>({...x.dataset}));
  const options=()=>page.locator('#project-options [data-id]').evaluateAll(ns=>ns.map(x=>x.dataset.id));
  const openSelector=async()=>{await (await one(page,'#all-projects')).click();await page.waitForTimeout(150);return options()};
  const c0=await current();if(c0.id!==cur||c0.archived!=='false')throw new InterfaceError('current project missing or archived');
  const before=await openSelector();const archivedBefore=projects.filter(p=>p.archived).map(p=>p.id);
  const activeBefore=projects.filter(p=>!p.archived).map(p=>p.id);
  await reload(page);await (await one(page,'#more')).click();await (await one(page,'#archive')).click();await reload(page);
  if((await current()).archived!=='true')throw new InterfaceError('archiving through the page failed');
  const after=await openSelector();const archived=[...archivedBefore,cur];
  check(`archived_project_not_selectable_${n}`,!after.includes(cur)&&archivedBefore.every(id=>!before.includes(id)));
  check(`active_projects_selectable_${n}`,activeBefore.every(id=>before.includes(id))&&activeBefore.filter(id=>id!==cur).every(id=>after.includes(id)));
  await (await one(page,'#project-search')).fill(fixture.query);await page.waitForTimeout(150);const found=await options();
  const title=id=>projects.find(p=>p.id===id).name.toLowerCase();
  check(`archived_not_in_search_${n}`,archived.every(id=>!found.includes(id)));
  check(`search_filters_by_title_${n}`,fixture.query_active.every(id=>found.includes(id))&&found.every(id=>title(id).includes(fixture.query.toLowerCase())));
  await (await one(page,'#project-search')).fill('');await page.waitForTimeout(150);
  const next=page.locator(`#project-options [data-id="${fixture.open_next}"]`);let opened=false;
  if(await next.count()===1&&await next.isVisible()){await next.click();await reload(page);opened=(await current()).id===fixture.open_next}
  check(`option_opens_project_${n}`,opened);
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
