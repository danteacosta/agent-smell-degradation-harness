'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/article/test';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[
  {title:'About testing',id:'comment-21',body:'First comment',author:'alice',other:'bruno'},
  {title:'Second article',id:'comment-73',body:'Different discussion',author:'maria',other:'joao'},
];
const shots=['fixture-1.png','fixture-2.png','fixture-3.png','fixture-4.png'];
const report={schema_version:'realworld-comment-delete-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
async function session(browser,fixture,viewer,shot){const context=await browser.newContext({viewport:{width:1000,height:720},timezoneId:'UTC',serviceWorkers:'block'});
  try{
    await context.addInitScript(initial=>Object.defineProperty(window,'initialState',{value:initial}),{
      articleTitle:fixture.title,viewer,comments:[{id:fixture.id,body:fixture.body,author:{username:fixture.author}}]});
    await context.route('**/*',route=>route.request().url()===URL&&route.request().isNavigationRequest()
      ?route.fulfill({body:html,contentType:'text/html',headers:{'Content-Security-Policy':CSP}}):route.abort());
    const page=await context.newPage();page.setDefaultTimeout(2500);
    page.on('console',m=>{if(m.type()==='error'&&report.console_errors.length<20)report.console_errors.push(m.text().slice(0,500))});
    page.on('pageerror',e=>{if(report.console_errors.length<20)report.console_errors.push(String(e).slice(0,500))});
    await page.goto(URL,{waitUntil:'load',timeout:10000});
    if(!await page.evaluate(()=>typeof viewHandler==='function'))throw new InterfaceError('view handler unavailable');
    const row=await one(page,`[data-comment-id="${fixture.id}"]`);
    const buttons=row.locator('button');let visibleButtons=0;
    for(let j=0;j<await buttons.count();j++){
      const button=buttons.nth(j),label=(await button.textContent()||'')+' '+(await button.getAttribute('aria-label')||'');
      if(/delete/i.test(label)&&await button.isVisible())visibleButtons++;
    }
    const visible=visibleButtons===1;
    const comment=await row.locator('.comment-body').innerText();
    const author=await row.locator('.comment-author').innerText();
    const title=await (await one(page,'#article-title')).innerText();
    const identity=await (await one(page,'#viewer')).innerText();
    await page.screenshot({path:`/output/${shot}`,fullPage:true});
    return {visible,buttonCount:visibleButtons,comment:comment===fixture.body&&author===fixture.author,
      title:title===fixture.title,identity:identity==='Signed in as '+viewer,
      oneComment:await page.locator('[data-comment-id]').count()===1};
  }finally{await context.close()}
}
(async()=>{let browser;try{browser=await chromium.launch({headless:true,chromiumSandbox:false});
  for(let i=0;i<fixtures.length;i++){
    const f=fixtures[i],author=await session(browser,f,f.author,shots[i*2]),other=await session(browser,f,f.other,shots[i*2+1]);
    report.assertions[`author_delete_visible_${i+1}`]=author.visible&&author.buttonCount===1;
    report.assertions[`other_delete_hidden_${i+1}`]=!other.visible&&other.buttonCount===0;
    report.assertions[`comment_visible_${i+1}`]=author.comment&&other.comment;
    report.assertions[`article_preserved_${i+1}`]=author.title&&other.title;
    report.assertions[`viewer_preserved_${i+1}`]=author.identity&&other.identity;
    report.assertions[`one_comment_${i+1}`]=author.oneComment&&other.oneComment;
  }
  report.status='complete';report.screenshots=shots;
}catch(error){report.status=report.console_errors.length?'browser_error':error instanceof InterfaceError?'interface_error':'browser_error';report.assertions={};report.error=String(error).slice(0,1500);
}finally{if(browser)await browser.close();fs.writeFileSync('/output/report.json',JSON.stringify(report,null,2));process.exitCode=report.status==='complete'?0:2}})();
