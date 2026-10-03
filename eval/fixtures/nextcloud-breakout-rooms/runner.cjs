'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"conversation": "Product team", "moderator": "Alice", "participants": [{"id": "p1", "name": "Bob"}, {"id": "p2", "name": "Carol"}, {"id": "p3", "name": "Dan"}, {"id": "p4", "name": "Erin"}, {"id": "p5", "name": "Femi"}]}, "count": 2}, {"state": {"conversation": "Workshop", "moderator": "Grace", "participants": [{"id": "q1", "name": "Hana"}, {"id": "q2", "name": "Ivan"}, {"id": "q3", "name": "Jon"}, {"id": "q4", "name": "Kemal"}, {"id": "q5", "name": "Lina"}, {"id": "q6", "name": "Mo"}, {"id": "q7", "name": "Nora"}]}, "count": 3}];
const report={schema_version:'nextcloud-breakout-rooms-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;const ids=fixture.state.participants.map(p=>p.id);
  const read=()=>page.locator('#rooms li').evaluateAll(ns=>ns.map(x=>({name:x.dataset.name,participants:x.dataset.participants?x.dataset.participants.split(','):[]})));
  if((await read()).length!==0||await page.locator('#participants li[data-id]').count()!==ids.length)throw new InterfaceError('participants missing or rooms present before setup');
  await (await one(page,'#room-count')).fill(String(fixture.count));await (await one(page,'#create-rooms')).click();await reload(page);
  const rooms=await read();const assigned=rooms.flatMap(r=>r.participants);
  check(`requested_rooms_created_${n}`,rooms.length===fixture.count&&new Set(rooms.map(r=>r.name)).size===rooms.length);
  check(`each_participant_in_one_room_${n}`,assigned.length===ids.length&&ids.every(id=>assigned.includes(id)));
  check(`rooms_are_smaller_groups_${n}`,rooms.length>1&&rooms.every(r=>r.participants.length>0&&r.participants.length<ids.length));
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
