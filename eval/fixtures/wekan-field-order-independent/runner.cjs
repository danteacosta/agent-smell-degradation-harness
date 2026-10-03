'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"orders": {"minicard": ["dates", "cover", "labels", "customFields", "members", "description"], "card": ["labels", "dates", "members", "customFields", "description"]}}, "minicard_moves": [["members", "up"], ["members", "up"]], "card_moves": [["labels", "down"]]}, {"state": {"orders": {"minicard": ["cover", "labels", "dates", "members", "customFields", "description"], "card": ["description", "customFields", "members", "dates", "labels"]}}, "minicard_moves": [["dates", "down"]], "card_moves": [["labels", "up"], ["labels", "up"]]}];
const report={schema_version:'wekan-field-order-independent-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;
  const read=async()=>({minicard:await page.locator('#minicard-preview .field').evaluateAll(ns=>ns.map(x=>x.dataset.key)),
    card:await page.locator('#card-preview .field').evaluateAll(ns=>ns.map(x=>x.dataset.key))});
  const move=(list,[key,dir])=>{const out=[...list];const i=out.indexOf(key);const j=dir==='up'?i-1:i+1;if(i>=0&&j>=0&&j<out.length)[out[i],out[j]]=[out[j],out[i]];return out};
  const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);const o=fixture.state.orders;
  if(!same(await read(),{minicard:o.minicard,card:o.card}))throw new InterfaceError('field orders missing or changed');
  const press=async(side,[key,dir])=>(await one(page,`#${side}-list li[data-key="${key}"] button.${dir}`)).click();
  for(const m of fixture.minicard_moves)await press('minicard',m);
  await reload(page);const a=await read();
  check(`minicard_move_applied_${n}`,same(a.minicard,fixture.minicard_moves.reduce(move,o.minicard)));
  check(`card_unchanged_by_minicard_move_${n}`,same(a.card,o.card));
  for(const m of fixture.card_moves)await press('card',m);
  await reload(page);const b=await read();
  check(`card_move_applied_${n}`,same(b.card,fixture.card_moves.reduce(move,a.card)));
  check(`minicard_unchanged_by_card_move_${n}`,same(b.minicard,a.minicard));
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
