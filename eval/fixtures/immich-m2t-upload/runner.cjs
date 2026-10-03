'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {}, "files": [["holiday.m2t", "application/octet-stream", true, true], ["clip.mov", "video/quicktime", false, true], ["notes.txt", "text/plain", false, false]]}, {"state": {}, "files": [["race.m2t", "application/octet-stream", true, true], ["match.mts", "video/mp2t", false, true], ["scan.pdf", "application/pdf", false, false]]}];
const report={schema_version:'immich-m2t-upload-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;
  if(await page.locator('#results li').count()!==0)throw new InterfaceError('results present before upload');
  const input=page.locator('#files');if(await input.count()!==1)throw new InterfaceError('one file input required');
  await input.setInputFiles(fixture.files.map(([name,mimeType])=>({name,mimeType,buffer:Buffer.from('test video '+name)})));
  await page.waitForTimeout(300);await reload(page);
  const rows=await page.locator('#results li').evaluateAll(ns=>ns.map(x=>[x.dataset.name,x.dataset.status]));
  const status=Object.fromEntries(rows);
  check(`m2t_accepted_${n}`,fixture.files.filter(f=>f[2]).every(f=>status[f[0]]==='accepted'));
  check(`other_video_accepted_${n}`,fixture.files.filter(f=>!f[2]&&f[3]).every(f=>status[f[0]]==='accepted'));
  check(`non_video_rejected_${n}`,fixture.files.filter(f=>!f[3]).every(f=>status[f[0]]==='rejected'));
  check(`each_file_decided_once_${n}`,rows.length===fixture.files.length&&new Set(rows.map(r=>r[0])).size===rows.length);
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
