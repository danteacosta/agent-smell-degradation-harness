'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"actor": {"username": "maria", "superuser": false}, "user": {"username": "bob", "firstName": "Bob", "superuser": false}}, "kind": "non_superuser", "first_name": "Robert"}, {"state": {"actor": {"username": "admin", "superuser": true}, "user": {"username": "carla", "firstName": "Carla", "superuser": false}}, "kind": "superuser", "first_name": "Carla Maria"}];
const report={schema_version:'paperless-superuser-grant-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;const stored=()=>page.locator('#stored').evaluate(x=>({...x.dataset}));
  const initial=await stored();
  if(initial.superuser!=='false'||initial.username!==fixture.state.user.username)throw new InterfaceError('user missing or already superuser');
  await (await one(page,'#first-name')).fill(fixture.first_name);
  const box=page.locator('#superuser');
  if(await box.count()===1&&await box.isVisible()&&await box.isEnabled())await box.check();
  await (await one(page,'#save')).click();await reload(page);
  const after=await stored();
  if(fixture.kind==='non_superuser'){
    check('non_superuser_cannot_grant_1',after.superuser==='false');
    check('username_preserved_1',after.username===fixture.state.user.username);
  }else{
    check('superuser_can_grant_2',after.superuser==='true');
    check('first_name_saved_2',after.firstName===fixture.first_name);
    check('username_preserved_2',after.username===fixture.state.user.username);
  }
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
