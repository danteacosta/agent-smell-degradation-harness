'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"files": [{"id": "f1", "name": "Documents", "type": "folder", "path": "/"}, {"id": "f2", "name": "Photos", "type": "folder", "path": "/"}, {"id": "f3", "name": "notes.md", "type": "file", "path": "/"}], "deleted": [{"id": "t1", "name": "old-report.pdf", "type": "file", "originalPath": "/"}, {"id": "t2", "name": "Drafts", "type": "folder", "originalPath": "/"}]}, "folder": "f2", "restore": "t1", "erase": "t2"}, {"state": {"files": [{"id": "g1", "name": "Projects", "type": "folder", "path": "/"}, {"id": "g2", "name": "Invoices", "type": "folder", "path": "/"}, {"id": "g3", "name": "budget.ods", "type": "file", "path": "/"}, {"id": "g4", "name": "Music", "type": "folder", "path": "/"}], "deleted": [{"id": "u1", "name": "Archive", "type": "folder", "originalPath": "/"}, {"id": "u2", "name": "photo.jpg", "type": "file", "originalPath": "/"}, {"id": "u3", "name": "scan.pdf", "type": "file", "originalPath": "/"}]}, "folder": "g2", "restore": "u1", "erase": "u3"}];
const report={schema_version:'nextcloud-delete-folder-trash-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;
  const read=sel=>page.locator(sel+' li').evaluateAll(ns=>ns.map(x=>x.dataset.id));
  if(JSON.stringify(await read('#files'))!==JSON.stringify(fixture.state.files.map(f=>f.id))||JSON.stringify(await read('#deleted'))!==JSON.stringify(fixture.state.deleted.map(f=>f.id)))throw new InterfaceError('files or deleted files missing or changed');
  await (await one(page,`#files li[data-id="${fixture.folder}"] button.delete`)).click();await reload(page);
  let files=await read('#files'),deleted=await read('#deleted');
  check(`folder_removed_from_files_${n}`,!files.includes(fixture.folder)&&fixture.state.files.filter(f=>f.id!==fixture.folder).every(f=>files.includes(f.id)));
  check(`folder_in_trash_bin_${n}`,deleted.filter(id=>id===fixture.folder).length===1);
  await (await one(page,`#deleted li[data-id="${fixture.restore}"] button.restore`)).click();await reload(page);
  files=await read('#files');deleted=await read('#deleted');
  check(`restore_returns_item_${n}`,files.includes(fixture.restore)&&!deleted.includes(fixture.restore));
  await (await one(page,`#deleted li[data-id="${fixture.erase}"] button.erase`)).click();await reload(page);
  files=await read('#files');deleted=await read('#deleted');
  check(`delete_permanently_removes_${n}`,!files.includes(fixture.erase)&&!deleted.includes(fixture.erase));
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
