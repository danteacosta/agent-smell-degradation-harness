'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const ORIGIN='http://localhost';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[
  {authored:{id:'authored-a',title:'Alice builds a parser',author:{username:'alice'},favoritedBy:[]},favorite:{id:'favorite-a',title:'Bob tests a parser',author:{username:'bob'},favoritedBy:['alice']}},
  {authored:{id:'authored-b',title:'Alice writes a guide',author:{username:'alice'},favoritedBy:[]},favorite:{id:'favorite-b',title:'Carol ships a client',author:{username:'carol'},favoritedBy:['alice']}},
];
const report={schema_version:'realworld-favorites-browser/v2',status:'browser_error',app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
async function runFixture(browser,fixture,index){
  const context=await browser.newContext({viewport:{width:1000,height:720},timezoneId:'UTC',serviceWorkers:'block'});
  try{
    await context.addInitScript(initial=>Object.defineProperty(window,'initialState',{value:initial}),{articles:[fixture.authored,fixture.favorite]});
    await context.route('**/*',route=>route.request().url().startsWith(ORIGIN+'/profile/alice')&&route.request().isNavigationRequest()
      ?route.fulfill({body:html,contentType:'text/html',headers:{'Content-Security-Policy':CSP}}):route.abort());
    const page=await context.newPage();page.setDefaultTimeout(2500);
    page.on('console',m=>{if(m.type()==='error'&&report.console_errors.length<20)report.console_errors.push(m.text().slice(0,500))});
    page.on('pageerror',e=>{if(report.console_errors.length<20)report.console_errors.push(String(e).slice(0,500))});
    await page.goto(ORIGIN+'/profile/alice',{waitUntil:'load',timeout:10000});
    const handler=await page.evaluate(()=>typeof routeHandler==='function');if(!handler)throw new InterfaceError('route handler missing');
    const authored=await one(page,`[data-article-id="${fixture.authored.id}"] h2`);
    if(await authored.innerText()!==fixture.authored.title||await page.locator('[data-article-id]').count()!==1)throw new InterfaceError('authored route precondition');
    await (await one(page,'#favorites-link')).click();
    if(page.url()!==ORIGIN+'/profile/alice/favorites')throw new InterfaceError('favorites route unreachable');
    await page.reload({waitUntil:'load',timeout:10000});
    const rows=page.locator('[data-article-id]');const ids=await rows.evaluateAll(nodes=>nodes.map(node=>node.getAttribute('data-article-id')));
    const favorite=page.locator(`[data-article-id="${fixture.favorite.id}"] h2`);
    report.assertions[`favorite_listed_${index+1}`]=await favorite.count()===1&&await favorite.innerText()===fixture.favorite.title;
    report.assertions[`authored_only_excluded_${index+1}`]=!ids.includes(fixture.authored.id);
    report.assertions[`profile_preserved_${index+1}`]=await (await one(page,'#profile-name')).innerText()==='alice';
    report.assertions[`navigation_preserved_${index+1}`]=await (await one(page,'#authored-link')).getAttribute('href')==='/profile/alice'&&await (await one(page,'#favorites-link')).getAttribute('href')==='/profile/alice/favorites';
    report.assertions[`unique_article_ids_${index+1}`]=ids.every(Boolean)&&new Set(ids).size===ids.length;
    await page.screenshot({path:`/output/fixture-${index+1}.png`,fullPage:true});
  }finally{await context.close()}
}
(async()=>{let browser;try{browser=await chromium.launch({headless:true,chromiumSandbox:false});
  for(let i=0;i<fixtures.length;i++)await runFixture(browser,fixtures[i],i);
  report.status='complete';report.screenshots=['fixture-1.png','fixture-2.png'];
}catch(error){report.status=report.console_errors.length?'browser_error':error instanceof InterfaceError?'interface_error':'browser_error';report.assertions={};report.error=String(error).slice(0,1500);
}finally{if(browser)await browser.close();fs.writeFileSync('/output/report.json',JSON.stringify(report,null,2));process.exitCode=report.status==='complete'?0:2}})();
