'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"user": "alice", "devices": [{"id": "s1", "name": "Firefox on Linux"}], "passwords": ["Xk7pQ-2mW9z-Lr4Tb-8vNc1-Hy3Ds"]}, "create": ["Laptop sync client"], "reveal": ["Laptop sync client"]}, {"state": {"user": "bruno", "devices": [{"id": "s7", "name": "Chrome on Windows"}, {"id": "s8", "name": "Android phone"}], "passwords": ["Pq2Rt-Vw8Yx-Bn5Mk-Jh4Gf-Dc6Sa", "Zt3Lm-Qa9Ws-Ed7Rf-Tg2Yh-Uj5Ik"]}, "create": ["Desktop client", "Calendar app"], "reveal": ["Desktop client", "Calendar app", "Android phone"]}];
const report={schema_version:'nextcloud-device-password-once-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;const pw=fixture.state.passwords;
  const rows=()=>page.locator('#devices li').evaluateAll(ns=>ns.map(x=>x.dataset.name));
  const cred=()=>page.locator('#credentials').evaluate(x=>({hidden:x.hidden,password:x.dataset.password}));
  if(JSON.stringify(await rows())!==JSON.stringify(fixture.state.devices.map(d=>d.name))||!(await cred()).hidden)throw new InterfaceError('device list missing or password shown before creating');
  let shownAtCreation=true;
  for(const [i,name] of fixture.create.entries()){
    await (await one(page,'#app-name')).fill(name);await (await one(page,'#create')).click();
    const c=await cred();shownAtCreation=shownAtCreation&&!c.hidden&&c.password===pw[i];
    const close=page.locator('#close');if(await close.isVisible())await close.click();
  }
  let notRevealed=true;
  const reveal=async()=>{for(const name of fixture.reveal){const b=page.locator(`#devices li[data-name="${name}"] button.show`);
      if(await b.count()===1&&await b.isVisible()&&await b.isEnabled())await b.click();
      const text=await page.evaluate(()=>document.body.innerText);const c=await cred();
      notRevealed=notRevealed&&pw.every(p=>!text.includes(p)&&!c.password.includes(p))}};
  await reveal();await reload(page);await reveal();
  check(`password_not_revealed_later_${n}`,notRevealed);
  check(`password_shown_at_creation_${n}`,shownAtCreation);
  check(`devices_listed_${n}`,JSON.stringify(await rows())===JSON.stringify([...fixture.state.devices.map(d=>d.name),...fixture.create]));
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
