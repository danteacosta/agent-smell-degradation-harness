'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"global": {"enabled": false, "format": "DD-MM-YYYY"}, "settings": {"board": {"enabled": false, "format": "YYYY-MM-DD"}, "showWeek": false}, "cards": [{"id": "k1", "title": "Release", "due": "2026-01-01"}, {"id": "k2", "title": "Audit", "due": "2026-03-30"}, {"id": "k3", "title": "Retro", "due": "2026-12-31"}]}, "weeks": [1, 14, 53], "initial_format": "YYYY-MM-DD", "override": true, "format": "DD-MM-YYYY", "saved_format": "DD-MM-YYYY"}, {"state": {"global": {"enabled": true, "format": "DD-MM-YYYY"}, "settings": {"board": {"enabled": true, "format": "MM-DD-YYYY"}, "showWeek": true}, "cards": [{"id": "m1", "title": "Kickoff", "due": "2027-01-01"}, {"id": "m2", "title": "Review", "due": "2026-06-15"}]}, "weeks": [53, 25], "initial_format": "MM-DD-YYYY", "override": false, "format": "MM-DD-YYYY", "saved_format": "DD-MM-YYYY"}];
const report={schema_version:'wekan-week-number-immediate-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;const cards=fixture.state.cards;
  const read=()=>page.locator('#dates li').evaluateAll(ns=>ns.map(x=>[x.dataset.id,x.dataset.date,x.dataset.week]));
  const f=(s,p)=>{const [y,m,d]=s.split('-');return p.replace('YYYY',y).replace('MM',m).replace('DD',d)};
  const expect=(p,w)=>JSON.stringify(cards.map((c,i)=>[c.id,f(c.due,p),w?String(fixture.weeks[i]):'']));
  const dates=rows=>JSON.stringify(rows.map(r=>r[1]));const initialDates=JSON.stringify(cards.map(c=>f(c.due,fixture.initial_format)));
  const week0=fixture.state.settings.showWeek;
  if(JSON.stringify(await read())!==expect(fixture.initial_format,week0))throw new InterfaceError('dates missing or changed before editing');
  await (await one(page,'#show-week')).setChecked(!week0);
  const before=await read();await reload(page);const kept=await read();
  const weeks=rows=>JSON.stringify(rows.map(r=>[r[0],r[2]]));const wanted=JSON.stringify(cards.map((c,i)=>[c.id,week0?'':String(fixture.weeks[i])]));
  check(`week_toggle_applies_without_save_${n}`,weeks(before)===wanted&&weeks(kept)===wanted);
  check(`toggle_keeps_date_format_${n}`,dates(before)===initialDates&&dates(kept)===initialDates);
  await (await one(page,'#override')).setChecked(fixture.override);
  await (await one(page,'#format')).selectOption(fixture.format);
  await (await one(page,'#save')).click();await reload(page);
  check(`board_format_saved_${n}`,dates(await read())===JSON.stringify(cards.map(c=>f(c.due,fixture.saved_format))));
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
