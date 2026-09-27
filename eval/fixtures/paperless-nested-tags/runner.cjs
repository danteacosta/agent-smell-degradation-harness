'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[
  {title:'Invoice 2026',child:'Travel',parent:'Finance',unrelated:'Archive'},
  {title:'Research Notes',child:'Draft',parent:'Thesis',unrelated:'Personal'},
];
const report={schema_version:'paperless-nested-tags-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
async function runFixture(browser,fixture,index){const context=await browser.newContext({viewport:{width:1000,height:720},timezoneId:'UTC',serviceWorkers:'block'});
  try{
    await context.addInitScript(initial=>Object.defineProperty(window,'initialState',{value:initial}),{
      documentTitle:fixture.title,child:fixture.child,parent:fixture.parent,
      hierarchy:{[fixture.child]:fixture.parent,[fixture.parent]:null,[fixture.unrelated]:null}});
    await context.route('**/*',route=>route.request().url()===URL&&route.request().isNavigationRequest()
      ?route.fulfill({body:html,contentType:'text/html',headers:{'Content-Security-Policy':CSP}}):route.abort());
    const page=await context.newPage();page.setDefaultTimeout(2500);
    page.on('console',m=>{if(m.type()==='error'&&report.console_errors.length<20)report.console_errors.push(m.text().slice(0,500))});
    page.on('pageerror',e=>{if(report.console_errors.length<20)report.console_errors.push(String(e).slice(0,500))});
    await page.goto(URL,{waitUntil:'load',timeout:10000});
    if(await (await one(page,'#document-title')).innerText()!==fixture.title||
       await (await one(page,'#hierarchy')).innerText()!==`${fixture.child} → ${fixture.parent}`||
       await page.locator('#assigned .tag').count()!==0||
       !await page.evaluate(()=>typeof assignBehavior==='function'))throw new InterfaceError('initial tag UI unavailable or preassigned');
    await (await one(page,'#assign-child')).click();await page.reload({waitUntil:'load',timeout:10000});
    const tags=await page.locator('#assigned .tag').evaluateAll(nodes=>nodes.map(node=>({name:node.textContent,id:node.dataset.tag})));
    report.assertions[`child_visible_${index+1}`]=tags.filter(t=>t.name===fixture.child&&t.id===fixture.child).length===1;
    report.assertions[`parent_visible_${index+1}`]=tags.filter(t=>t.name===fixture.parent&&t.id===fixture.parent).length===1;
    report.assertions[`unrelated_absent_${index+1}`]=!tags.some(t=>t.name===fixture.unrelated||t.id===fixture.unrelated);
    report.assertions[`no_duplicate_tags_${index+1}`]=tags.every(t=>t.name===t.id)&&new Set(tags.map(t=>t.id)).size===tags.length;
    report.assertions[`document_preserved_${index+1}`]=await (await one(page,'#document-title')).innerText()===fixture.title;
    report.assertions[`hierarchy_preserved_${index+1}`]=await (await one(page,'#hierarchy')).innerText()===`${fixture.child} → ${fixture.parent}`;
    await page.screenshot({path:`/output/fixture-${index+1}.png`,fullPage:true});
  }finally{await context.close()}
}
(async()=>{let browser;try{browser=await chromium.launch({headless:true,chromiumSandbox:false});
  for(let i=0;i<fixtures.length;i++)await runFixture(browser,fixtures[i],i);
  report.status='complete';report.screenshots=['fixture-1.png','fixture-2.png'];
}catch(error){report.status=report.console_errors.length?'browser_error':error instanceof InterfaceError?'interface_error':'browser_error';report.assertions={};report.error=String(error).slice(0,1500);
}finally{if(browser)await browser.close();fs.writeFileSync('/output/report.json',JSON.stringify(report,null,2));process.exitCode=report.status==='complete'?0:2}})();
