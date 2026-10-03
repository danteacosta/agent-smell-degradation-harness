'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"swimlanes": [{"id": "l1", "title": "Backlog"}, {"id": "l2", "title": "Doing"}, {"id": "l3", "title": "Done"}]}, "default_anchor": "l2", "default_titles": ["Review"], "explicit_anchor": "l1", "explicit_placement": "above", "explicit_titles": ["Ideas", "Inbox"]}, {"state": {"swimlanes": [{"id": "t1", "title": "Team A"}, {"id": "t2", "title": "Team B"}]}, "default_anchor": "t1", "default_titles": ["QA"], "explicit_anchor": "t2", "explicit_placement": "below", "explicit_titles": ["Support", "Ops", "Sales"]}];
const report={schema_version:'wekan-swimlane-below-default-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;const lanes=()=>page.locator('#swimlanes li').evaluateAll(ns=>ns.map(x=>x.dataset.title));
  const initial=fixture.state.swimlanes.map(l=>l.title);const title=id=>fixture.state.swimlanes.find(l=>l.id===id).title;
  const insert=(list,at,placement,titles)=>{const i=list.indexOf(at);const out=[...list];out.splice(placement==='above'?i:i+1,0,...titles);return JSON.stringify(out)};
  if(JSON.stringify(await lanes())!==JSON.stringify(initial))throw new InterfaceError('swimlanes missing or changed');
  await (await one(page,`.add-lane[data-for="${fixture.default_anchor}"]`)).click();
  await (await one(page,'#titles')).fill(fixture.default_titles.join('\n'));
  await (await one(page,'#save')).click();await reload(page);
  const a=await lanes();
  check(`untouched_popup_inserts_below_${n}`,JSON.stringify(a)===insert(initial,title(fixture.default_anchor),'below',fixture.default_titles));
  await (await one(page,`.add-lane[data-for="${fixture.explicit_anchor}"]`)).click();
  await (await one(page,`#placement-${fixture.explicit_placement}`)).check();
  await (await one(page,'#titles')).fill(fixture.explicit_titles.join('\n'));
  await (await one(page,'#save')).click();await reload(page);
  const b=await lanes();
  check(`chosen_placement_keeps_order_${n}`,JSON.stringify(b)===insert(a,title(fixture.explicit_anchor),fixture.explicit_placement,fixture.explicit_titles));
  check(`existing_lanes_kept_${n}`,JSON.stringify(b.filter(t=>initial.includes(t)))===JSON.stringify(initial));
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
