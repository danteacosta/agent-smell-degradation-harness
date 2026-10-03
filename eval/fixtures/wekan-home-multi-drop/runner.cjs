'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"home": null, "boards": [{"id": "d1", "title": "Sprint"}, {"id": "d2", "title": "Roadmap"}, {"id": "d3", "title": "Ops"}, {"id": "d4", "title": "Personal"}]}, "multi": ["d1", "d3"], "single": "d1"}, {"state": {"home": "e2", "boards": [{"id": "e1", "title": "Marketing"}, {"id": "e2", "title": "Support"}, {"id": "e3", "title": "Hiring"}, {"id": "e4", "title": "Budget"}]}, "multi": ["e1", "e3", "e4"], "single": "e3"}];
const report={schema_version:'wekan-home-multi-drop-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;const initialHome=fixture.state.home??'';
  const homeNow=()=>page.locator('#home-row').evaluate(x=>x.dataset.home);
  const selectedNow=async()=>(await page.locator('#boards li').evaluateAll(ns=>ns.filter(x=>x.dataset.selected==='true').map(x=>x.dataset.id))).sort();
  const select=async ids=>{for(const b of fixture.state.boards)await (await one(page,`#boards li[data-id="${b.id}"] input.select`)).setChecked(ids.includes(b.id))};
  if(await homeNow()!==initialHome||(await selectedNow()).length!==0)throw new InterfaceError('home or selection changed before the drop');
  await select(fixture.multi);
  if(JSON.stringify(await selectedNow())!==JSON.stringify([...fixture.multi].sort()))throw new InterfaceError('boards could not be selected');
  await (await one(page,'#drop-home')).click();
  const home1=await homeNow();const sel1=await selectedNow();const msg=((await page.locator('#message').textContent())||'').toLowerCase();
  await reload(page);const home1r=await homeNow();
  check(`multi_drop_changes_nothing_${n}`,home1===initialHome&&home1r===initialHome);
  check(`multi_drop_reports_${n}`,msg.includes('please select only one board'));
  check(`multi_drop_keeps_selection_${n}`,JSON.stringify(sel1)===JSON.stringify([...fixture.multi].sort()));
  await select([fixture.single]);await (await one(page,'#drop-home')).click();await reload(page);
  const home2=await homeNow();
  await select([fixture.single]);await (await one(page,'#drop-home')).click();await reload(page);
  check(`single_drop_sets_home_${n}`,home2===fixture.single&&await homeNow()===fixture.single);
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
