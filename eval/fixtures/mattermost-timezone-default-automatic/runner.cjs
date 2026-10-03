'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"timezone": null, "computerTimezone": "Europe/Lisbon", "zones": ["America/New_York", "Europe/Lisbon", "Asia/Tokyo"]}, "zone": "Asia/Tokyo"}, {"state": {"timezone": null, "computerTimezone": "Australia/Sydney", "zones": ["America/Sao_Paulo", "Europe/Berlin", "Australia/Sydney"]}, "zone": "America/Sao_Paulo"}];
const report={schema_version:'mattermost-timezone-default-automatic-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;const stored=()=>page.locator('#current').evaluate(x=>JSON.parse(x.dataset.pref));
  if(await stored()!==null||await page.locator('#editor').isVisible())throw new InterfaceError('timezone preference saved before editing');
  await (await one(page,'#edit')).click();await (await one(page,'#save')).click();await reload(page);
  const first=await stored();
  check(`untouched_save_keeps_automatic_${n}`,first!==null&&first.automatic===true);
  await (await one(page,'#edit')).click();await (await one(page,'#automatic')).setChecked(false);
  await (await one(page,'#manual-timezone')).selectOption(fixture.zone);await (await one(page,'#save')).click();await reload(page);
  const second=await stored();
  check(`manual_timezone_saved_${n}`,second!==null&&second.automatic===false&&second.manualTimezone===fixture.zone);
  await (await one(page,'#edit')).click();await (await one(page,'#save')).click();await reload(page);
  const third=await stored();
  check(`saved_choice_kept_on_reopen_${n}`,third!==null&&third.automatic===false&&third.manualTimezone===fixture.zone);
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
