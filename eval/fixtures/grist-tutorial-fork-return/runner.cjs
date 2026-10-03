'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"user": {"id": "12345", "name": "Sam"}, "docs": [{"id": "woXtXUBmiN5T", "name": "Intro to formulas", "rows": [{"id": "s1", "label": "Step 1", "value": "=$Price * 2"}, {"id": "s2", "label": "Step 2", "value": ""}]}], "forks": []}, "doc": "woXtXUBmiN5T", "edit": ["s2", "=SUM($Price)"]}, {"state": {"user": {"id": "12345", "name": "Sam"}, "docs": [{"id": "kQ3pLrT8vZ2m", "name": "Lookups tutorial", "rows": [{"id": "a", "label": "Answer A", "value": ""}, {"id": "b", "label": "Answer B", "value": ""}]}], "forks": [{"id": "kQ3pLrT8vZ2m~7hGtYe2LmQ~777", "docId": "kQ3pLrT8vZ2m", "forkId": "7hGtYe2LmQ", "userId": "777", "rows": [{"id": "a", "label": "Answer A", "value": "other user"}, {"id": "b", "label": "Answer B", "value": ""}]}, {"id": "kQ3pLrT8vZ2m~1eYN9joCXk~12345", "docId": "kQ3pLrT8vZ2m", "forkId": "1eYN9joCXk", "userId": "12345", "rows": [{"id": "a", "label": "Answer A", "value": "$Name"}, {"id": "b", "label": "Answer B", "value": "lookupOne"}]}]}, "doc": "kQ3pLrT8vZ2m", "own": "kQ3pLrT8vZ2m~1eYN9joCXk~12345", "edit": ["b", "lookupOne"]}];
const report={schema_version:'grist-tutorial-fork-return-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;const base='https://docs.getgrist.com/doc/'+fixture.doc;const uid=fixture.state.user.id;
  const original=Object.fromEntries(fixture.state.docs[0].rows.map(r=>[r.id,r.value]));
  const view=()=>page.locator('#view').evaluate(v=>({shown:v.dataset.shown,doc:v.dataset.doc,user:v.dataset.forkUser,cells:Object.fromEntries([...v.querySelectorAll('input[data-row]')].map(i=>[i.dataset.row,i.dataset.stored]))}));
  if((await view()).shown!=='')throw new InterfaceError('a document is open before navigation');
  async function go(url){await (await one(page,'#address')).fill(url);await (await one(page,'#go')).click();return view()}
  async function close(){await (await one(page,'#close')).click();if((await view()).shown!=='')throw new InterfaceError('close did not close the document')}
  const isOwnFork=v=>v.doc===fixture.doc&&v.user===uid&&v.shown!==fixture.doc;
  if(n===1){
    const first=await go(base);const ok=isOwnFork(first);
    check('first_visit_opens_own_fork_1',ok);
    if(ok){const input=await one(page,`#view input[data-row="${fixture.edit[0]}"]`);await input.fill(fixture.edit[1]);await input.press('Tab')}
    await close();
    const back=await go(base);
    check('returns_to_fork_1',ok&&back.shown===first.shown&&back.cells[fixture.edit[0]]===fixture.edit[1]);
  }else{
    const f=await go('https://docs.getgrist.com/doc/'+fixture.own);
    check('fork_url_opens_fork_2',f.shown===fixture.own);
    await close();
    const back=await go(base);
    check('returns_to_fork_2',back.shown===fixture.own&&back.cells[fixture.edit[0]]===fixture.edit[1]);
  }
  await close();
  const def=await go(base+'/m/default');
  check(`default_mode_original_${n}`,def.shown===fixture.doc&&JSON.stringify(def.cells)===JSON.stringify(original));
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
