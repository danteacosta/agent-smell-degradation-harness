'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"rule": {"type": "ingredient", "value": "Fish"}, "recipes": [{"id": "r1", "name": "Salmon bowl", "ingredients": [{"food": "Salmon", "label": "Fish"}, {"food": "Rice", "label": "Grain"}]}, {"id": "r2", "name": "Tuna pasta", "ingredients": [{"food": "Tuna", "label": "Fish"}, {"food": "Pasta", "label": "Grain"}]}, {"id": "r3", "name": "Fish pie", "ingredients": [{"food": "Fish", "label": "Fish"}, {"food": "Potato", "label": "Vegetable"}]}, {"id": "r4", "name": "Chicken curry", "ingredients": [{"food": "Chicken", "label": "Meat"}, {"food": "Rice", "label": "Grain"}]}]}, "by_label": ["r1", "r2"], "by_food": ["r3"], "excluded": ["r4"]}, {"state": {"rule": {"type": "ingredient", "value": "Citrus"}, "recipes": [{"id": "s1", "name": "Lemon tart", "ingredients": [{"food": "Lemon", "label": "Citrus"}, {"food": "Flour", "label": "Baking"}]}, {"id": "s2", "name": "Orange cake", "ingredients": [{"food": "Orange", "label": "Citrus"}]}, {"id": "s3", "name": "Apple pie", "ingredients": [{"food": "Apple", "label": "Fruit"}]}, {"id": "s4", "name": "Citrus salad", "ingredients": [{"food": "Citrus", "label": "Citrus"}]}]}, "by_label": ["s1", "s2"], "by_food": ["s4"], "excluded": ["s3"]}];
const report={schema_version:'mealie-planner-food-label-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const n=index+1;
  if(await page.locator('#pool li').count()!==0)throw new InterfaceError('pool shown before preview');
  await (await one(page,'#preview')).click();
  const got=await page.locator('#pool li').evaluateAll(ns=>ns.map(x=>x.dataset.id));
  check(`food_label_matches_included_${n}`,fixture.by_label.every(id=>got.includes(id)));
  check(`food_name_matches_included_${n}`,fixture.by_food.every(id=>got.includes(id)));
  check(`non_matching_excluded_${n}`,fixture.excluded.every(id=>!got.includes(id))&&new Set(got).size===got.length);
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
