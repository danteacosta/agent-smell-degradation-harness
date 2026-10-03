'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"user": {"username": "ana", "language": "en"}, "channel": {"name": "global-ops", "messages": [{"id": "m1", "author": "lucas", "language": "pt", "text": "Bom dia, equipe!"}, {"id": "m2", "author": "ana", "language": "en", "text": "Deploy finished at 09:00."}, {"id": "m3", "author": "sofia", "language": "es", "text": "¿Quién revisa el cambio?"}]}, "translations": [{"text": "Bom dia, equipe!", "language": "en", "translation": "Good morning, team!"}, {"text": "¿Quién revisa el cambio?", "language": "en", "translation": "Who is reviewing the change?"}, {"text": "Deploy finished at 09:00.", "language": "pt", "translation": "Implantação concluída às 09:00."}]}, "foreign": {"m1": "Good morning, team!", "m3": "Who is reviewing the change?"}, "own": ["m2"]}, {"state": {"user": {"username": "jonas", "language": "de"}, "channel": {"name": "release-train", "messages": [{"id": "n1", "author": "mia", "language": "en", "text": "Release notes are ready."}, {"id": "n2", "author": "jonas", "language": "de", "text": "Danke, ich schaue es mir an."}, {"id": "n3", "author": "luc", "language": "fr", "text": "Réunion demain à 15 h."}]}, "translations": [{"text": "Release notes are ready.", "language": "de", "translation": "Die Versionshinweise sind fertig."}, {"text": "Réunion demain à 15 h.", "language": "de", "translation": "Besprechung morgen um 15 Uhr."}, {"text": "Réunion demain à 15 h.", "language": "en", "translation": "Meeting tomorrow at 3 pm."}]}, "foreign": {"n1": "Die Versionshinweise sind fertig.", "n3": "Besprechung morgen um 15 Uhr."}, "own": ["n2"]}];
const report={schema_version:'mattermost-channel-autotranslate-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;const msgs=fixture.state.channel.messages;
  if(await page.locator('#messages li').count()!==0)throw new InterfaceError('messages shown before opening the channel');
  await (await one(page,'#open')).click();
  const rows=await page.locator('#messages li').evaluateAll(ns=>ns.map(x=>[x.dataset.id,x.innerText,x.checkVisibility()]));
  const shown=Object.fromEntries(rows.map(([id,text,visible])=>[id,visible?text:null]));
  check(`foreign_messages_translated_${n}`,Object.entries(fixture.foreign).every(([id,text])=>shown[id]===msgs.find(m=>m.id===id).author+': '+text));
  check(`own_language_messages_unchanged_${n}`,fixture.own.every(id=>shown[id]===msgs.find(m=>m.id===id).author+': '+msgs.find(m=>m.id===id).text));
  check(`all_messages_in_order_${n}`,rows.every(r=>r[2])&&JSON.stringify(rows.map(r=>r[0]))===JSON.stringify(msgs.map(m=>m.id)));
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
