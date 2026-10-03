'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"settings": {"sortOrder": "newest", "sortFavoritesUp": false}, "messages": [{"id": "m1", "from": "Ana", "subject": "Quarterly numbers", "date": "2026-09-01T08:00:00Z", "favorite": false}, {"id": "m2", "from": "Ben", "subject": "Lunch on Friday", "date": "2026-09-03T12:30:00Z", "favorite": false}, {"id": "m3", "from": "Chen", "subject": "Contract draft", "date": "2026-09-02T09:15:00Z", "favorite": true}, {"id": "m4", "from": "Dora", "subject": "Server maintenance", "date": "2026-09-05T18:00:00Z", "favorite": false}, {"id": "m5", "from": "Emil", "subject": "Travel booking", "date": "2026-08-28T07:45:00Z", "favorite": true}, {"id": "m6", "from": "Fay", "subject": "Newsletter", "date": "2026-09-04T06:00:00Z", "favorite": false}]}, "order": "newest"}, {"state": {"settings": {"sortOrder": "newest", "sortFavoritesUp": false}, "messages": [{"id": "n1", "from": "Gil", "subject": "Invoice 4471", "date": "2026-07-14T10:00:00Z", "favorite": true}, {"id": "n2", "from": "Hanne", "subject": "Team photo", "date": "2026-07-10T16:20:00Z", "favorite": false}, {"id": "n3", "from": "Igor", "subject": "Release notes", "date": "2026-07-12T11:05:00Z", "favorite": false}, {"id": "n4", "from": "Jana", "subject": "Board agenda", "date": "2026-07-16T08:40:00Z", "favorite": true}, {"id": "n5", "from": "Kai", "subject": "Parking permit", "date": "2026-07-11T13:00:00Z", "favorite": false}]}, "order": "oldest"}];
const report={schema_version:'nextcloud-mail-favorites-up-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;const msgs=fixture.state.messages;
  const groups=()=>page.locator('#list > section').evaluateAll(ns=>ns.map(x=>x.dataset.ids?x.dataset.ids.split(','):[]).filter(g=>g.length));
  if((await groups()).length!==0||await page.locator('#favorites-up').isChecked())throw new InterfaceError('message list shown or favorites setting on before opening');
  const sorted=[...msgs].sort((a,b)=>fixture.order==='newest'?b.date.localeCompare(a.date):a.date.localeCompare(b.date)).map(m=>m.id);
  await (await one(page,'#open-inbox')).click();
  if(fixture.order==='oldest')await (await one(page,'#sort-order')).selectOption('oldest');
  let g=await groups();
  const offOk=JSON.stringify(g.flat())===JSON.stringify(sorted);
  await (await one(page,'#favorites-up')).check();
  g=await groups();const fav=new Set(msgs.filter(m=>m.favorite).map(m=>m.id));
  check(`favorites_in_top_section_${n}`,g.length===2&&g[0].length===fav.size&&g[0].every(id=>fav.has(id))&&g[1].every(id=>!fav.has(id)));
  check(`order_without_favorites_up_${n}`,offOk);
  check(`every_message_listed_once_${n}`,g.flat().length===msgs.length&&new Set(g.flat()).size===msgs.length);
  const flat=g.flat();const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
  check(`sort_order_kept_${n}`,flat.length>0&&same(flat.filter(id=>fav.has(id)),sorted.filter(id=>fav.has(id)))&&same(flat.filter(id=>!fav.has(id)),sorted.filter(id=>!fav.has(id))));
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
