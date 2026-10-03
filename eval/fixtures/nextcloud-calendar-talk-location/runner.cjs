'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"tokenPrefix": "nw", "conversations": [{"token": "t1a9", "name": "Team weekly"}, {"token": "t2b7", "name": "Design"}]}, "events": [{"title": "Weekly sync", "start": "2026-10-12T09:00", "type": "talk", "value": "Team weekly"}, {"title": "Sprint review", "start": "2026-10-16T14:00", "type": "talk", "value": "Sprint review"}]}, {"state": {"tokenPrefix": "ev", "conversations": [{"token": "k4c2", "name": "Ops"}, {"token": "k5d8", "name": "Release planning"}]}, "events": [{"title": "Board meeting", "start": "2026-11-03T10:30", "type": "address", "value": "Room 4.2"}, {"title": "Release party", "start": "2026-11-07T18:00", "type": "talk", "value": "Release party"}]}];
const report={schema_version:'nextcloud-calendar-talk-location-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;const LINK='https://cloud.example.com/call/';const c0=fixture.state.conversations;
  const convs=()=>page.locator('#conversations li').evaluateAll(ns=>ns.map(x=>({token:x.dataset.token,name:x.dataset.name})));
  const events=()=>page.locator('#events li').evaluateAll(ns=>ns.map(x=>({title:x.dataset.title,start:x.dataset.start,location:x.dataset.location})));
  if(JSON.stringify(await convs())!==JSON.stringify(c0)||(await events()).length!==0)throw new InterfaceError('conversations missing or events present before saving');
  const save=async e=>{await (await one(page,'#event-title')).fill(e.title);await (await one(page,'#event-start')).fill(e.start);
    await (await one(page,`input[name=location-type][value=${e.type}]`)).check();await (await one(page,'#location')).fill(e.value);
    await (await one(page,'#save-event')).click();await reload(page)};
  const [first,second]=fixture.events;
  await save(first);let cs=await convs();let evs=await events();const e1=evs.filter(e=>e.title===first.title);
  if(first.type==='talk'){const t=c0.find(c=>c.name===first.value).token;
    check(`existing_conversation_linked_${n}`,e1.length===1&&e1[0].location===LINK+t);
    check(`existing_conversation_not_duplicated_${n}`,JSON.stringify(cs)===JSON.stringify(c0));
  }else check(`address_location_kept_${n}`,e1.length===1&&e1[0].location===first.value&&JSON.stringify(cs)===JSON.stringify(c0));
  await save(second);cs=await convs();evs=await events();const e2=evs.filter(e=>e.title===second.title);const made=cs.filter(c=>c.name===second.value);
  check(`new_conversation_created_${n}`,made.length===1&&!c0.some(c=>c.token===made[0].token)&&e2.length===1&&e2[0].location===LINK+made[0].token);
  check(`events_saved_${n}`,evs.length===2&&[first,second].every(f=>evs.filter(e=>e.title===f.title&&e.start===f.start).length===1));
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
