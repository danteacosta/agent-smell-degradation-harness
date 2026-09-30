'use strict';
const fs=require('node:fs');
const crypto=require('node:crypto');
const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');
const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[
  {name:'Project Plan.md',active:'Budget.csv',deleted:'Old Notes.txt'},
  {name:'Design Notes.txt',active:'Sprint Report.pdf',deleted:'Archive.zip'},
];
const report={schema_version:'nextcloud-restore-conflict-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
async function visibleText(page,selector){const node=page.locator(selector);return await node.count()===1&&await node.isVisible()?await node.innerText():''}
async function runFixture(browser,fixture,index){
  const context=await browser.newContext({viewport:{width:1000,height:720},timezoneId:'UTC',serviceWorkers:'block'});
  try{
    await context.addInitScript(initial=>Object.defineProperty(window,'initialState',{value:initial}),
      {active:[{id:'collision',name:fixture.name},{id:'active-control',name:fixture.active}],
       deleted:[{id:'restored',name:fixture.name},{id:'deleted-control',name:fixture.deleted}]});
    await context.route('**/*',route=>route.request().url()===URL&&route.request().isNavigationRequest()
      ?route.fulfill({body:html,contentType:'text/html',headers:{'Content-Security-Policy':CSP}}):route.abort());
    const page=await context.newPage();page.setDefaultTimeout(2500);
    page.on('console',m=>{if(m.type()==='error'&&report.console_errors.length<20)report.console_errors.push(m.text().slice(0,500))});
    page.on('pageerror',e=>{if(report.console_errors.length<20)report.console_errors.push(String(e).slice(0,500))});
    await page.goto(URL,{waitUntil:'load',timeout:10000});
    await one(page,'#show-files');await one(page,'#show-deleted');
    if(await page.locator('#location').innerText()!=='Original location: /files (writable)')
      throw new InterfaceError('writable original location not established');
    if(await page.locator('[data-file-id]').count()!==2||await (await one(page,'[data-file-id="collision"] h2')).innerText()!==fixture.name)
      throw new InterfaceError('active file fixture mismatch');
    await page.locator('#show-deleted').click();
    const target=await one(page,'[data-file-id="restored"]');
    await one(page,'[data-file-id="deleted-control"]');
    if(await target.locator('h2').innerText()!==fixture.name||await page.locator('[data-file-id]').count()!==2)
      throw new InterfaceError('deleted file fixture mismatch');
    const action=await one(target,'button');
    if(!await action.isEnabled())throw new InterfaceError('restore action unavailable');
    await action.click();
    await page.locator('#show-files').click();
    await page.reload({waitUntil:'load',timeout:10000});
    if(await page.locator('h1').innerText()!=='Files')throw new InterfaceError('files view unavailable');
    const collision=page.locator('[data-file-id="collision"]');
    const restored=page.locator('[data-file-id="restored"]');
    const collisionName=await visibleText(page,'[data-file-id="collision"] h2');
    const restoredName=await visibleText(page,'[data-file-id="restored"] h2');
    report.assertions[`original_preserved_${index+1}`]=collisionName===fixture.name;
    report.assertions[`restored_visible_${index+1}`]=await restored.count()===1;
    report.assertions[`unique_name_${index+1}`]=Boolean(restoredName.trim())&&restoredName!==fixture.name;
    report.assertions[`active_control_${index+1}`]=await visibleText(page,'[data-file-id="active-control"] h2')===fixture.active;
    report.assertions[`active_count_${index+1}`]=await page.locator('[data-file-id]').count()===3;
    await page.screenshot({path:`/output/files-${index+1}.png`,fullPage:true});
    await page.locator('#show-deleted').click();
    report.assertions[`removed_from_trash_${index+1}`]=await page.locator('[data-file-id="restored"]').count()===0;
    report.assertions[`trash_control_${index+1}`]=await visibleText(page,'[data-file-id="deleted-control"] h2')===fixture.deleted;
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
