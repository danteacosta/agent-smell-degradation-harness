'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{work:'8',initial:'7',valid:'6',invalid:'9'},{work:'12',initial:'10',valid:'9',invalid:'13'}];
const report={schema_version:'openproject-invalid-remaining-browser/v1',status:'browser_error',app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const x=page.locator(selector);if(await x.count()!==1||!await x.isVisible())throw new InterfaceError(`one visible ${selector} required`);return x}
async function runFixture(browser,f,i){
  const context=await browser.newContext({viewport:{width:1000,height:720},timezoneId:'UTC',serviceWorkers:'block'});
  try{
    await context.addInitScript(initial=>Object.defineProperty(window,'initialState',{value:initial}),{work:f.work,remaining:f.initial});
    await context.route('**/*',route=>route.request().url()===URL&&route.request().isNavigationRequest()?route.fulfill({body:html,contentType:'text/html',headers:{'Content-Security-Policy':CSP}}):route.abort());
    const page=await context.newPage();page.setDefaultTimeout(2500);
    page.on('console',m=>{if(m.type()==='error'&&report.console_errors.length<20)report.console_errors.push(m.text().slice(0,500))});
    page.on('pageerror',e=>{if(report.console_errors.length<20)report.console_errors.push(String(e).slice(0,500))});
    await page.goto(URL,{waitUntil:'load',timeout:10000});
    const work=await one(page,'[aria-label="Work"]'),remaining=await one(page,'[aria-label="Remaining work"]'),save=await one(page,'#save');
    if(await work.inputValue()!==f.work||await remaining.inputValue()!==f.initial||!await save.isEnabled())throw new InterfaceError('initial form or save action unavailable');
    await remaining.fill(f.valid);await save.click();await page.reload({waitUntil:'load',timeout:10000});
    report.assertions[`valid_saved_${i+1}`]=await (await one(page,'[aria-label="Remaining work"]')).inputValue()===f.valid;
    report.assertions[`work_preserved_after_valid_${i+1}`]=await (await one(page,'[aria-label="Work"]')).inputValue()===f.work;
    const invalidInput=await one(page,'[aria-label="Remaining work"]'),invalidSave=await one(page,'#save');
    if(!await invalidSave.isEnabled())throw new InterfaceError('save action unavailable after reload');
    await invalidInput.fill(f.invalid);await invalidSave.click();await page.reload({waitUntil:'load',timeout:10000});
    report.assertions[`invalid_rejected_${i+1}`]=await (await one(page,'[aria-label="Remaining work"]')).inputValue()===f.valid;
    report.assertions[`work_preserved_after_invalid_${i+1}`]=await (await one(page,'[aria-label="Work"]')).inputValue()===f.work;
    report.assertions[`form_reloaded_${i+1}`]=await page.locator('h1').innerText()==='Work package progress';
    await page.screenshot({path:`/output/fixture-${i+1}.png`,fullPage:true});
  }finally{await context.close()}
}
(async()=>{let browser;try{
  browser=await chromium.launch({headless:true,chromiumSandbox:false});for(let i=0;i<fixtures.length;i++)await runFixture(browser,fixtures[i],i);
  report.status='complete';report.screenshots=['fixture-1.png','fixture-2.png'];
}catch(error){report.status=report.console_errors.length?'browser_error':error instanceof InterfaceError?'interface_error':'browser_error';report.assertions={};report.error=String(error).slice(0,1500);
}finally{if(browser)await browser.close();fs.writeFileSync('/output/report.json',JSON.stringify(report,null,2));process.exitCode=report.status==='complete'?0:2}})();
