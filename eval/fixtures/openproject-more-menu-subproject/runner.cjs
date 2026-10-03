'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"current": "a1", "projects": [{"id": "a1", "name": "Website relaunch", "parent": null, "public": false, "template": false, "archived": false}, {"id": "a2", "name": "Intranet", "parent": null, "public": false, "template": false, "archived": false}]}, "other": {"key": "make_public_works", "re": "make\\s+(a\\s+|the\\s+)?(project\\s+)?public", "attr": "public"}, "child": "Landing pages"}, {"state": {"current": "b2", "projects": [{"id": "b1", "name": "Product line", "parent": null, "public": false, "template": false, "archived": false}, {"id": "b2", "name": "Release 3.0", "parent": "b1", "public": false, "template": false, "archived": false}, {"id": "b3", "name": "Support", "parent": null, "public": false, "template": false, "archived": false}]}, "other": {"key": "set_template_works", "re": "template", "attr": "template"}, "child": "Beta program"}];
const report={schema_version:'openproject-more-menu-subproject-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;const cur=fixture.state.current;
  const projects=()=>page.locator('#projects li').evaluateAll(ns=>ns.map(x=>({...x.dataset})));
  const initial=await projects();
  if(initial.length!==fixture.state.projects.length||!initial.some(p=>p.id===cur)||await page.locator('#new-project').isVisible())throw new InterfaceError('projects changed before the menu was used');
  async function useItem(re){await (await one(page,'#more')).click();await page.waitForTimeout(100);
    const item=page.locator('#more-menu').getByRole('menuitem',{name:re});
    if(await item.count()<1||!await item.first().isVisible())return false;await item.first().click();return true}
  const used=await useItem(new RegExp(fixture.other.re,'i'));await reload(page);
  const me=(await projects()).find(p=>p.id===cur);
  check(`${fixture.other.key}_${n}`,used&&me?.[fixture.other.attr]==='true');
  let created=false;
  if(await useItem(/add\s+(a\s+)?sub-?project/i)){const form=page.locator('#new-project');
    if(await form.isVisible()){await (await one(page,'#np-name')).fill(fixture.child);await (await one(page,'#np-create')).click();await reload(page);
      const made=(await projects()).filter(p=>p.name===fixture.child);created=made.length===1&&made[0].parent===cur}}
  check(`subproject_created_under_current_${n}`,created);
  const final=await projects();
  check(`existing_projects_kept_${n}`,fixture.state.projects.every(p=>final.some(f=>f.id===p.id&&f.parent===(p.parent??''))));
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
