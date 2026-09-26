'use strict';
const fs=require('node:fs');
const crypto=require('node:crypto');
const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');
const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[
  {target:'Project Plan.md',control:'Budget.csv'},
  {target:'Design Notes.txt',control:'Sprint Report.pdf'},
];
const report={schema_version:'nextcloud-permanent-delete-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
async function runFixture(browser,fixture,index){
  const context=await browser.newContext({viewport:{width:1000,height:720},timezoneId:'UTC',serviceWorkers:'block'});
  try{
    await context.addInitScript(initial=>Object.defineProperty(window,'initialState',{value:initial}),
      {files:[{id:'target-file',name:fixture.target},{id:'control-file',name:fixture.control}]});
    await context.route('**/*',route=>route.request().url()===URL&&route.request().isNavigationRequest()
      ?route.fulfill({body:html,contentType:'text/html',headers:{'Content-Security-Policy':CSP}}):route.abort());
    const page=await context.newPage();page.setDefaultTimeout(2500);
    page.on('console',m=>{if(m.type()==='error'&&report.console_errors.length<20)report.console_errors.push(m.text().slice(0,500))});
    page.on('pageerror',e=>{if(report.console_errors.length<20)report.console_errors.push(String(e).slice(0,500))});
    await page.goto(URL,{waitUntil:'load',timeout:10000});
    const target=await one(page,'[data-file-id="target-file"]');
    const control=await one(page,'[data-file-id="control-file"]');
    if(await target.locator('h2').innerText()!==fixture.target||await control.locator('h2').innerText()!==fixture.control)
      throw new InterfaceError('initial trash fixture mismatch');
    const pre=await page.evaluate(()=>({registered:typeof deleteBehavior==='function',count:app.files().length}));
    if(!pre.registered||pre.count!==2||await page.locator('[data-file-id]').count()!==2)
      throw new InterfaceError('selected deletion must be handled after click');
    await (await one(target,'button')).click();
    await page.reload({waitUntil:'load',timeout:10000});
    if(await page.locator('h1').innerText()!=='Deleted files')throw new InterfaceError('deleted-files view unavailable');
    const targetRows=page.locator('[data-file-id="target-file"]');
    const controlRows=page.locator('[data-file-id="control-file"]');
    report.assertions[`selected_absent_${index+1}`]=await targetRows.count()===0;
    report.assertions[`control_preserved_${index+1}`]=await controlRows.count()===1&&
      await controlRows.locator('h2').innerText()===fixture.control;
    report.assertions[`no_extra_rows_${index+1}`]=await page.locator('[data-file-id]').count()===await controlRows.count()+await targetRows.count();
    await page.screenshot({path:`/output/fixture-${index+1}.png`,fullPage:true});
  }finally{await context.close()}
}
(async()=>{let browser;try{
  browser=await chromium.launch({headless:true,chromiumSandbox:false});
  for(let i=0;i<fixtures.length;i++)await runFixture(browser,fixtures[i],i);
  report.status='complete';report.screenshots=['fixture-1.png','fixture-2.png'];
}catch(error){report.status=report.console_errors.length?'browser_error':error instanceof InterfaceError?'interface_error':'browser_error';
  report.assertions={};report.error=String(error).slice(0,1500);
}finally{if(browser)await browser.close();fs.writeFileSync('/output/report.json',JSON.stringify(report,null,2));
  process.exitCode=report.status==='complete'?0:2}})();
