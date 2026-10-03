'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"playbook": "Incident response"}, "tasks": ["**Review** the incident timeline", "Notify stakeholders"], "formatted": [[0, "Review the incident timeline", [["strong,b", "Review"]]]], "plain": [1]}, {"state": {"playbook": "Release checklist"}, "tasks": ["Page the on-call engineer", "Confirm *all* alerts are **resolved**"], "formatted": [[1, "Confirm all alerts are resolved", [["em,i", "all"], ["strong,b", "resolved"]]]], "plain": [0]}];
const report={schema_version:'mattermost-playbook-task-markdown-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;
  if(await page.locator('#tasks li').count()!==0)throw new InterfaceError('tasks present before adding');
  for(const text of fixture.tasks){await (await one(page,'#task-text')).fill(text);await (await one(page,'#add-task')).click()}
  await reload(page);
  const rows=await page.locator('#tasks li').evaluateAll(ns=>ns.map(li=>{const s=li.querySelector('.task-text');
    return {text:li.dataset.text,shown:s?s.textContent.replace(/\s+/g,' ').trim():'',
      parts:s?[...s.querySelectorAll('*')].map(e=>[e.tagName.toLowerCase(),e.textContent.trim()]):[]}}));
  const formatted=fixture.formatted.every(([i,shown,parts])=>{const r=rows[i];return !!r&&r.shown===shown&&!/[*_]/.test(r.shown)&&
    parts.every(([tags,word])=>r.parts.some(([tag,t])=>tags.split(',').includes(tag)&&t===word))});
  check(`markdown_rendered_${n}`,formatted);
  check(`tasks_added_in_order_${n}`,JSON.stringify(rows.map(r=>r.text))===JSON.stringify(fixture.tasks));
  check(`plain_task_shown_as_typed_${n}`,fixture.plain.every(i=>rows[i]&&rows[i].shown===fixture.tasks[i]));
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
