'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"system": {"colorScheme": "dark", "contrast": "more"}}, "manual": {"mode": "light", "contrast": false, "theme": "light"}}, {"state": {"system": {"colorScheme": "light", "contrast": "no-preference"}}, "manual": {"mode": "dark", "contrast": true, "theme": "dark_high_contrast"}}];
const report={schema_version:'openproject-auto-theme-contrast-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;const applied=()=>page.locator('#applied').evaluate(x=>x.dataset.theme);
  if(await applied()!=='light')throw new InterfaceError('theme applied before any update');
  const setContrast=async on=>{const box=page.locator('#increase-contrast');
    if(await box.count()===1&&await box.isVisible()&&await box.isEnabled()){if(on)await box.check();else await box.uncheck()}};
  await (await one(page,'#color-mode')).selectOption(fixture.manual.mode);await setContrast(fixture.manual.contrast);
  await (await one(page,'#update')).click();await reload(page);
  check(`manual_mode_applied_${n}`,await applied()===fixture.manual.theme);
  await (await one(page,'#color-mode')).selectOption('auto');await setContrast(false);
  await (await one(page,'#update')).click();await reload(page);
  const theme=String(await applied());const os=fixture.state.system;
  check(`auto_follows_os_scheme_${n}`,theme.split('_')[0]===os.colorScheme);
  check(`auto_follows_os_contrast_${n}`,theme.endsWith('_high_contrast')===(os.contrast==='more'));
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
