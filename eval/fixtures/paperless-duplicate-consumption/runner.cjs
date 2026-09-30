'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[
  {original:'Original Invoice.pdf',upload:'Invoice Copy.pdf',control:'Budget.csv',checksum:'same-a'},
  {original:'Signed Form.pdf',upload:'Form Copy.pdf',control:'Notes.txt',checksum:'same-b'},
];
const report={schema_version:'paperless-duplicate-consumption-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
async function runFixture(browser,fixture,index){const context=await browser.newContext({viewport:{width:1000,height:720},timezoneId:'UTC',serviceWorkers:'block'});
  try{
    await context.addInitScript(initial=>Object.defineProperty(window,'initialState',{value:initial}),{
      documents:[{id:'original',title:fixture.original,checksum:fixture.checksum},{id:'control',title:fixture.control,checksum:'other'}],
      upload:{name:fixture.upload,checksum:fixture.checksum}});
    await context.route('**/*',route=>route.request().url()===URL&&route.request().isNavigationRequest()
      ?route.fulfill({body:html,contentType:'text/html',headers:{'Content-Security-Policy':CSP}}):route.abort());
    const page=await context.newPage();page.setDefaultTimeout(2500);
    page.on('console',m=>{if(m.type()==='error'&&report.console_errors.length<20)report.console_errors.push(m.text().slice(0,500))});
    page.on('pageerror',e=>{if(report.console_errors.length<20)report.console_errors.push(String(e).slice(0,500))});
    await page.goto(URL,{waitUntil:'load',timeout:10000});
    const original=await one(page,'[data-document-id="original"]');const control=await one(page,'[data-document-id="control"]');
    if(await original.locator('h2').innerText()!==fixture.original||await control.locator('h2').innerText()!==fixture.control)
      throw new InterfaceError('initial document fixture mismatch');
    const pre=await page.evaluate(()=>({registered:typeof uploadBehavior==='function',count:app.documents().length}));
    if(!pre.registered||pre.count!==2||await page.locator('[data-document-id]').count()!==2)
      throw new InterfaceError('upload must create a new record only after click');
    await (await one(page,'#upload')).click();await page.reload({waitUntil:'load',timeout:10000});
    const rows=page.locator('[data-document-id]');
    const ids=await rows.evaluateAll(nodes=>nodes.map(node=>node.getAttribute('data-document-id')));
    const newIds=ids.filter(id=>id!=='original'&&id!=='control');
    report.assertions[`duplicate_consumed_${index+1}`]=newIds.length===1&&Boolean(newIds[0])&&
      await page.locator(`[data-document-id="${newIds[0]}"] h2`).count()===1&&
      await page.locator(`[data-document-id="${newIds[0]}"] h2`).innerText()===fixture.upload;
    report.assertions[`original_preserved_${index+1}`]=await page.locator('[data-document-id="original"] h2').count()===1&&
      await page.locator('[data-document-id="original"] h2').innerText()===fixture.original;
    report.assertions[`control_preserved_${index+1}`]=await page.locator('[data-document-id="control"] h2').count()===1&&
      await page.locator('[data-document-id="control"] h2').innerText()===fixture.control;
    report.assertions[`unique_identity_${index+1}`]=ids.every(Boolean)&&new Set(ids).size===ids.length;
    await page.screenshot({path:`/output/fixture-${index+1}.png`,fullPage:true});
  }finally{await context.close()}
}
(async()=>{let browser;try{browser=await chromium.launch({headless:true,chromiumSandbox:false});
  for(let i=0;i<fixtures.length;i++)await runFixture(browser,fixtures[i],i);
  report.status='complete';report.screenshots=['fixture-1.png','fixture-2.png'];
}catch(error){report.status=report.console_errors.length?'browser_error':error instanceof InterfaceError?'interface_error':'browser_error';report.assertions={};report.error=String(error).slice(0,1500);
}finally{if(browser)await browser.close();fs.writeFileSync('/output/report.json',JSON.stringify(report,null,2));process.exitCode=report.status==='complete'?0:2}})();
