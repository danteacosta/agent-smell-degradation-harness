'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"linkifiers": [{"pattern": "#(?<id>[0-9]+)", "urlTemplate": "https://github.com/zulip/zulip/issues/{id}", "linkText": "#{id}"}, {"pattern": "RT(?<id>[0-9]+)", "urlTemplate": "https://rt.example.org/Ticket/Display.html?id={id}", "linkText": null}]}, "messages": [{"typed": "Fixed in ", "paste": "https://github.com/zulip/zulip/issues/2468", "expect": "Fixed in #2468", "kind": "converted", "links": [["#2468", "https://github.com/zulip/zulip/issues/2468"]]}, {"typed": "Ticket: ", "paste": "https://rt.example.org/Ticket/Display.html?id=77", "expect": "Ticket: https://rt.example.org/Ticket/Display.html?id=77", "kind": "unmatched"}, {"typed": "See #1357 and RT42", "paste": null, "expect": "See #1357 and RT42", "kind": "typed", "links": [["#1357", "https://github.com/zulip/zulip/issues/1357"], ["RT42", "https://rt.example.org/Ticket/Display.html?id=42"]]}]}, {"state": {"linkifiers": [{"pattern": "#F(?<id>[0-9]+)", "urlTemplate": "https://github.com/zulip/zulip-flutter/issues/{id}", "linkText": "#F{id}"}, {"pattern": "(?<org>[a-zA-Z0-9_-]+)/(?<repo>[a-zA-Z0-9_-]+)#(?<id>[0-9]+)", "urlTemplate": "https://github.com/{org}/{repo}/pull/{id}", "linkText": "{org}/{repo}#{id}"}, {"pattern": "CASE-(?<id>[0-9]+)", "urlTemplate": "https://support.example.com/cases/{id}", "linkText": null}]}, "messages": [{"typed": "Merged as ", "paste": "https://github.com/django/django/pull/123", "expect": "Merged as django/django#123", "kind": "converted", "links": [["django/django#123", "https://github.com/django/django/pull/123"]]}, {"typed": "Tracked in ", "paste": "https://github.com/zulip/zulip-flutter/issues/245", "expect": "Tracked in #F245", "kind": "converted", "links": [["#F245", "https://github.com/zulip/zulip-flutter/issues/245"]]}, {"typed": "Customer report: ", "paste": "https://support.example.com/cases/5150", "expect": "Customer report: https://support.example.com/cases/5150", "kind": "unmatched"}, {"typed": "Duplicate of #F12, see CASE-9", "paste": null, "expect": "Duplicate of #F12, see CASE-9", "kind": "typed", "links": [["#F12", "https://github.com/zulip/zulip-flutter/issues/12"], ["CASE-9", "https://support.example.com/cases/9"]]}]}];
const report={schema_version:'zulip-reverse-linkifier-paste-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;
  const read=()=>page.locator('#messages li').evaluateAll(ns=>ns.map(li=>({text:li.textContent,links:[...li.querySelectorAll('a')].map(a=>[a.textContent,a.getAttribute('href')])})));
  if((await read()).length!==0)throw new InterfaceError('messages present before sending');
  async function paste(text){
    await page.locator('#compose').evaluate((box,t)=>{box.focus();box.setSelectionRange(box.value.length,box.value.length);
      const data=new DataTransfer();data.setData('text/plain',t);
      const event=new ClipboardEvent('paste',{clipboardData:data,bubbles:true,cancelable:true});
      if(box.dispatchEvent(event)){box.setRangeText(t,box.selectionStart,box.selectionEnd,'end');box.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertFromPaste',data:t}))}},text);
    await page.waitForTimeout(150)}
  let immediate=true;
  for(const m of fixture.messages){
    await (await one(page,'#compose')).fill(m.typed);
    if(m.paste){await paste(m.paste);if(m.kind==='converted')immediate=immediate&&(await page.locator('#compose').inputValue())===m.expect;}
    await (await one(page,'#send')).click();await page.waitForTimeout(100);
  }
  await reload(page);
  const got=await read();const at=i=>got[i]||{text:null,links:[]};
  const idx=kind=>fixture.messages.map((m,i)=>m.kind===kind?i:-1).filter(i=>i>=0);
  check(`pasted_url_converted_${n}`,immediate&&idx('converted').every(i=>at(i).text===fixture.messages[i].expect&&JSON.stringify(at(i).links)===JSON.stringify(fixture.messages[i].links)));
  check(`unmatched_paste_kept_${n}`,idx('unmatched').every(i=>at(i).text===fixture.messages[i].expect));
  check(`typed_reference_linked_${n}`,idx('typed').every(i=>at(i).text===fixture.messages[i].expect&&JSON.stringify(at(i).links)===JSON.stringify(fixture.messages[i].links)));
  check(`one_message_per_send_${n}`,got.length===fixture.messages.length);
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
