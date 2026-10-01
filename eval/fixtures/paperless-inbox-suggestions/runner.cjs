'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/documents/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[
  {document:{id:'doc-41',title:'Tax receipt',tags:['inbox']},availableSuggestions:[{id:'tag-7',label:'Taxes'}]},
  {document:{id:'doc-86',title:'Travel invoice',tags:['inbox','travel']},availableSuggestions:[{id:'tag-9',label:'Travel'}]},
];
const report={schema_version:'paperless-inbox-suggestions-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function inspect(browser,fixture,index){
  const context=await browser.newContext({viewport:{width:1000,height:720},timezoneId:'UTC',serviceWorkers:'block'});
  try{
    await context.addInitScript(initial=>Object.defineProperty(window,'initialState',
      {value:Object.freeze(initial),writable:false}),fixture);
    await context.route('**/*',route=>route.request().url()===URL&&route.request().isNavigationRequest()
      ?route.fulfill({body:html,contentType:'text/html',headers:{'Content-Security-Policy':CSP}}):route.abort());
    const page=await context.newPage();page.setDefaultTimeout(2500);
    page.on('console',message=>{if(message.type()==='error'&&report.console_errors.length<20)
      report.console_errors.push(message.text().slice(0,500))});
    page.on('pageerror',error=>{if(report.console_errors.length<20)
      report.console_errors.push(String(error).slice(0,500))});
    await page.goto(URL,{waitUntil:'load',timeout:10000});
    const title=page.locator('#document-title'),identity=page.locator('#document-id');
    const button=page.locator('#suggest-button'),area=page.locator('#suggestions');
    if(await title.count()!==1||!await title.isVisible()||await identity.count()!==1||!await identity.isVisible()
      ||await button.count()!==1||!await button.isVisible()||await area.count()!==1||!await area.isVisible())
      throw new InterfaceError('document detail controls unavailable');
    const ids=await page.evaluate(()=>app.observedRequestIds());
    const suggestion=area.locator(`[data-suggestion-id="${fixture.availableSuggestions[0].id}"]`);
    report.assertions[`request_once_${index}`]=Array.isArray(ids)&&ids.length===1&&ids[0]===fixture.document.id;
    report.assertions[`suggestion_visible_${index}`]=await suggestion.count()===1&&await suggestion.isVisible()
      &&(await suggestion.innerText()).trim()===fixture.availableSuggestions[0].label;
    report.assertions[`document_title_${index}`]=(await title.innerText()).trim()===fixture.document.title;
    report.assertions[`document_id_${index}`]=(await identity.innerText()).trim()==='Document '+fixture.document.id;
    report.assertions[`suggest_button_${index}`]=(await button.innerText()).trim()==='Suggest';
    await page.screenshot({path:`/output/fixture-${index}.png`,fullPage:true});
  }finally{await context.close()}
}
(async()=>{let browser;try{
  browser=await chromium.launch({headless:true,chromiumSandbox:false});
  for(let index=0;index<fixtures.length;index++)await inspect(browser,fixtures[index],index+1);
  report.status='complete';report.screenshots=['fixture-1.png','fixture-2.png'];
}catch(error){report.status=report.console_errors.length?'browser_error':error instanceof InterfaceError?'interface_error':'browser_error';
  report.assertions={};report.error=String(error).slice(0,1500);
}finally{if(browser)await browser.close();fs.writeFileSync('/output/report.json',JSON.stringify(report,null,2));
  process.exitCode=report.status==='complete'?0:2}})();
