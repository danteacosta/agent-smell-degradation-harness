'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"tracker": "Jira project WEB", "cards": [{"id": "c1", "externalId": "WEB-1", "title": "Login page", "description": "Build the login form", "sourceTitle": "Login page", "sourceDescription": "Build the login form", "archived": false}, {"id": "c2", "externalId": "WEB-2", "title": "Fix crash (urgent, seen twice)", "description": "Null pointer", "sourceTitle": "Fix crash", "sourceDescription": "Null pointer", "archived": false}, {"id": "c3", "externalId": "WEB-3", "title": "Old task", "description": "", "sourceTitle": "Old task", "sourceDescription": "", "archived": false}], "upstream": [{"externalId": "WEB-1", "title": "Login page with SSO", "description": "Build the login form"}, {"externalId": "WEB-2", "title": "Fix crash", "description": "Null pointer in the parser"}, {"externalId": "WEB-4", "title": "Write docs", "description": "API reference"}]}, "updated": [["WEB-1", "title", "Login page with SSO"], ["WEB-2", "description", "Null pointer in the parser"]], "kept": [["WEB-2", "title", "Fix crash (urgent, seen twice)"]], "created": ["WEB-4", "Write docs", "API reference"], "missing": "WEB-3"}, {"state": {"tracker": "GitHub repository acme/app", "cards": [{"id": "c1", "externalId": "G-10", "title": "Dark mode", "description": "Add a theme toggle; check contrast first", "sourceTitle": "Dark mode", "sourceDescription": "Add a theme toggle", "archived": false}, {"id": "c2", "externalId": "G-11", "title": "Export CSV", "description": "", "sourceTitle": "Export CSV", "sourceDescription": "", "archived": false}, {"id": "c3", "externalId": "G-12", "title": "Typo in footer", "description": "", "sourceTitle": "Typo in footer", "sourceDescription": "", "archived": false}, {"id": "c4", "externalId": "G-14", "title": "Release 2.0 (our checklist)", "description": "Tag and publish", "sourceTitle": "Release 2.0", "sourceDescription": "Tag and publish", "archived": false}], "upstream": [{"externalId": "G-10", "title": "Dark mode", "description": "Add a theme toggle"}, {"externalId": "G-11", "title": "Export CSV", "description": "Include a header row"}, {"externalId": "G-14", "title": "Release 2.0", "description": "Tag, sign and publish"}, {"externalId": "G-13", "title": "Import JSON", "description": "From Trello exports"}]}, "updated": [["G-11", "description", "Include a header row"], ["G-14", "description", "Tag, sign and publish"]], "kept": [["G-10", "description", "Add a theme toggle; check contrast first"], ["G-14", "title", "Release 2.0 (our checklist)"]], "created": ["G-13", "Import JSON", "From Trello exports"], "missing": "G-12"}];
const report={schema_version:'wekan-sync-local-edits-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;
  const read=()=>page.locator('#cards li').evaluateAll(ns=>ns.map(x=>({ext:x.dataset.externalId,title:x.dataset.title,description:x.dataset.description,archived:x.dataset.archived})));
  const initial=fixture.state.cards.map(c=>({ext:c.externalId,title:c.title,description:c.description,archived:'false'}));
  if(JSON.stringify(await read())!==JSON.stringify(initial))throw new InterfaceError('cards missing or changed before sync');
  await (await one(page,'#sync')).click();await reload(page);
  const after=await read();const by=ext=>after.filter(c=>c.ext===ext);
  const has=([ext,field,value])=>by(ext).length===1&&by(ext)[0][field]===value;
  check(`unchanged_local_text_updated_${n}`,fixture.updated.every(has));
  check(`local_edit_kept_${n}`,fixture.kept.every(has));
  const [ext,title,description]=fixture.created;
  check(`new_item_created_${n}`,by(ext).length===1&&by(ext)[0].title===title&&by(ext)[0].description===description&&by(ext)[0].archived==='false');
  check(`missing_item_archived_${n}`,by(fixture.missing).length===1&&by(fixture.missing)[0].archived==='true'
    &&after.filter(c=>c.ext!==fixture.missing).every(c=>c.archived==='false'));
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
