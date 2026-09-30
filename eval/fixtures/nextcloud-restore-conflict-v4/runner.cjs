'use strict';
const fs=require('node:fs');
const crypto=require('node:crypto');
const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');
const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[
  {path:'/files/Projects',name:'Plan.md',second:'Plan.md (restored)',control:'Budget.csv',deleted:'Old Notes.txt'},
  {path:'/files/Design',name:'Sketch.png',second:'Sketch.png (restored)',control:'Guide.pdf',deleted:'Archive.zip'},
];
const report={schema_version:'nextcloud-restore-conflict-browser/v4',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
async function visibleText(page,selector){const node=page.locator(selector);return await node.count()===1&&await node.isVisible()?await node.innerText():''}
async function runFixture(browser,f,i){
  const context=await browser.newContext({viewport:{width:1000,height:720},timezoneId:'UTC',serviceWorkers:'block'});
  try{
    await context.addInitScript(initial=>Object.defineProperty(window,'initialState',{value:initial}),
      {directory:{path:f.path,writable:true},
       active:[{id:'collision',name:f.name,path:f.path},{id:'second-collision',name:f.second,path:f.path},{id:'active-control',name:f.control,path:f.path}],
       deleted:[{id:'restored',name:f.name,originalPath:f.path},{id:'deleted-control',name:f.deleted,originalPath:f.path}]});
    await context.route('**/*',route=>route.request().url()===URL&&route.request().isNavigationRequest()
      ?route.fulfill({body:html,contentType:'text/html',headers:{'Content-Security-Policy':CSP}}):route.abort());
    const page=await context.newPage();page.setDefaultTimeout(2500);
    page.on('console',m=>{if(m.type()==='error'&&report.console_errors.length<20)report.console_errors.push(m.text().slice(0,500))});
    page.on('pageerror',e=>{if(report.console_errors.length<20)report.console_errors.push(String(e).slice(0,500))});
    await page.goto(URL,{waitUntil:'load',timeout:10000});
    await one(page,'#show-files');await one(page,'#show-deleted');
    if(await visibleText(page,'#location')!==`Original location: ${f.path} (writable)`||await page.locator('[data-file-id]').count()!==3)
      throw new InterfaceError('writable original directory not established');
    if(await visibleText(page,'[data-file-id="collision"] h2')!==f.name||await visibleText(page,'[data-file-id="second-collision"] h2')!==f.second||await visibleText(page,'[data-file-id="active-control"] h2')!==f.control)
      throw new InterfaceError('active namespace mismatch');
    await page.locator('#show-deleted').click();
    const target=await one(page,'[data-file-id="restored"]');
    await one(page,'[data-file-id="deleted-control"]');
    if(await target.locator('h2').innerText()!==f.name||await visibleText(page,'[data-file-id="restored"] .path')!==f.path||await page.locator('[data-file-id]').count()!==2)
      throw new InterfaceError('deleted item original path mismatch');
    const action=await one(target,'button');if(!await action.isEnabled())throw new InterfaceError('restore unavailable');
    await action.click();await page.locator('#show-files').click();await page.reload({waitUntil:'load',timeout:10000});
    if(await visibleText(page,'h1')!=='Files'||await visibleText(page,'#location')!==`Original location: ${f.path} (writable)`)
      throw new InterfaceError('original directory unavailable after reload');
    const ids=['collision','second-collision','active-control'];
    const original=[f.name,f.second,f.control];
    const activeNames=await Promise.all(ids.map(id=>visibleText(page,`[data-file-id="${id}"] h2`)));
    const restoredName=await visibleText(page,'[data-file-id="restored"] h2');
    report.assertions[`active_preserved_${i+1}`]=activeNames.every((name,j)=>name===original[j]);
    report.assertions[`restored_visible_${i+1}`]=await page.locator('[data-file-id="restored"]').count()===1;
    report.assertions[`restored_original_path_${i+1}`]=await visibleText(page,'[data-file-id="restored"] .path')===f.path;
    report.assertions[`unique_name_${i+1}`]=Boolean(restoredName.trim())&&!activeNames.includes(restoredName);
    report.assertions[`active_count_${i+1}`]=await page.locator('[data-file-id]').count()===4;
    await page.screenshot({path:`/output/files-${i+1}.png`,fullPage:true});
    await page.locator('#show-deleted').click();
    report.assertions[`removed_from_trash_${i+1}`]=await page.locator('[data-file-id="restored"]').count()===0;
    report.assertions[`trash_control_${i+1}`]=await visibleText(page,'[data-file-id="deleted-control"] h2')===f.deleted;
  }finally{await context.close()}
}
(async()=>{let browser;try{
  browser=await chromium.launch({headless:true,chromiumSandbox:false});
  for(let i=0;i<fixtures.length;i++)await runFixture(browser,fixtures[i],i);
  report.status='complete';report.screenshots=['files-1.png','files-2.png'];
}catch(error){report.status=report.console_errors.length?'browser_error':error instanceof InterfaceError?'interface_error':'browser_error';
  report.assertions={};report.error=String(error).slice(0,1500);
}finally{if(browser)await browser.close();fs.writeFileSync('/output/report.json',JSON.stringify(report,null,2));
  process.exitCode=report.status==='complete'?0:2}})();
