'use strict';
const fs=require('node:fs');
const crypto=require('node:crypto');
const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');
const report={schema_version:'strictdoc-stats-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),cases:[],
  isolation:'offline non-root resource-bounded Docker; Chromium sandbox disabled'};
const {clocks,stats,expected,groups,accepted_dates}=require('./contract.json');
let browser;
class InterfaceError extends Error{}
const normalize=s=>String(s).replace(/(\d)t(?=\d)/gi,'$1 ')
  .replace(/(\d+)(st|nd|rd|th)\b/gi,'$1').normalize('NFD').replace(/[\u0300-\u036f]/g,'')
  .toLowerCase().replace(/[^\p{L}\p{N}]+/gu,' ').trim().replace(/\s+/g,' ');
async function visibleText(page,selector=null){
  return page.evaluate(selector=>{
    // Pointer hit testing must also see visual covers whose pointer-events are none.
    // This observation-only sheet changes neither layout nor pixels and is removed.
    const hitSheet=document.createElement('style');
    hitSheet.textContent='*{pointer-events:auto!important}';document.head.append(hitSheet);
    const root=selector?document.querySelector(selector):document.body;
    const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
    const values=[];let node;
    try{while((node=walker.nextNode())){
      if(!node.textContent.trim())continue;
      let parent=node.parentElement;let shown=true;
      const textParent=parent;
      const color=getComputedStyle(parent);
      const transparent=value=>value==='transparent'||/^rgba\([^)]*[,/]\s*0(?:\.0+)?\s*\)$/.test(value);
      if(transparent(color.color)||transparent(color.webkitTextFillColor)||Number.parseFloat(color.fontSize)===0)continue;
      const clip={left:0,top:0,right:innerWidth,bottom:innerHeight};
      while(parent){
        if(['SCRIPT','STYLE','TEMPLATE','NOSCRIPT'].includes(parent.tagName)){
          shown=false;break;
        }
        const style=getComputedStyle(parent);
        if(style.display==='none'||style.visibility!=='visible'||Number(style.opacity)===0
            ||style.contentVisibility==='hidden'){
          shown=false;break;
        }
        const box=parent.getBoundingClientRect();
        if(style.overflowX!=='visible'){
          clip.left=Math.max(clip.left,box.left);clip.right=Math.min(clip.right,box.right);
        }
        if(style.overflowY!=='visible'){
          clip.top=Math.max(clip.top,box.top);clip.bottom=Math.min(clip.bottom,box.bottom);
        }
        parent=parent.parentElement;
      }
      if(!shown)continue;
      const range=document.createRange();let fragment='';
      for(let offset=0;offset<node.textContent.length;){
        const character=String.fromCodePoint(node.textContent.codePointAt(offset));
        range.setStart(node,offset);offset+=character.length;range.setEnd(node,offset);
        if(/\s/.test(character)){fragment+=' ';continue;}
        const visible=[...range.getClientRects()].some(rect=>{
          if(rect.width<=0||rect.height<=0||rect.left<clip.left||rect.right>clip.right
              ||rect.top<clip.top||rect.bottom>clip.bottom)return false;
          return [0.2,0.5,0.8].every(x=>[0.25,0.5,0.75].every(y=>
            document.elementFromPoint(rect.left+rect.width*x,rect.top+rect.height*y)===textParent));
        });
        fragment+=visible?character:' ';
      }
      values.push(fragment);
    }}finally{hitSheet.remove();}
    return values.join(' ').replace(/\s+/g,' ');
  },selector);
}
async function inspectPageText(page){
  const size=await page.evaluate(()=>({height:document.documentElement.scrollHeight,
    width:document.documentElement.scrollWidth}));
  if(size.height>8000||size.width>1000)
    throw new InterfaceError('screen exceeds bounded scrolling surface');
  const fragments=[];const scrolls=[];
  for(let y=0;y<size.height;y+=600){
    await page.evaluate(y=>window.scrollTo(0,y),y);await page.waitForTimeout(50);
    const actual=await page.evaluate(()=>scrollY);
    if(scrolls.includes(actual))continue;
    scrolls.push(actual);fragments.push(await visibleText(page));
  }
  const text=[...new Set(fragments)].join(' ');
  if(text.length>20000)throw new InterfaceError('rendered text exceeds observation bound');
  await page.evaluate(()=>window.scrollTo(0,0));
  return {text,scrolls};
}
async function runClock(iso,index){
  const context=await browser.newContext({viewport:{width:1000,height:720},
    timezoneId:'UTC',serviceWorkers:'block',acceptDownloads:false});
  await context.addInitScript(stats=>{window.projectStatistics=stats;},stats);
  await context.route('**/*',route=>route.request().url()==='http://fixture.invalid/' &&
    route.request().isNavigationRequest()
    ? route.fulfill({body:html,contentType:'text/html',headers:{'Content-Security-Policy':
      "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"}})
    : route.abort());
  try{
    const page=await context.newPage();page.setDefaultTimeout(2500);
    await page.clock.setFixedTime(new Date(iso));
    const errors=[];
    page.on('console',message=>{if(message.type()==='error'&&errors.length<20)
      errors.push(message.text().slice(0,500));});
    page.on('pageerror',error=>{if(errors.length<20)errors.push(String(error).slice(0,500));});
    page.on('dialog',dialog=>dialog.dismiss());
    await page.goto('http://fixture.invalid/',{waitUntil:'load',timeout:10000});
    await page.waitForTimeout(300);
    const observed={};
    for(const key of Object.keys(expected)){
      const item=page.locator(`[data-stat="${key}"]`);
      if(await item.count()!==1||!await item.isVisible())
        throw new InterfaceError(`one visible data-stat=${key} required`);
      await item.scrollIntoViewIfNeeded();
      const raw=(await item.innerText()).trim().replace(/\s+/g,' ');
      observed[key]=(await visibleText(page,`[data-stat="${key}"]`)).trim().replace(/\s+/g,' ');
      if(!observed[key]||observed[key]!==raw)
        throw new InterfaceError(`data-stat=${key} value is not fully observable`);
    }
    const {text,scrolls}=await inspectPageText(page);
    const clockId=index===0?'clock-one':'clock-two';
    const matched=accepted_dates[clockId].find(form=>(' '+normalize(text)+' ').includes(' '+form+' '))||null;
    const screenshot=`clock-${index===0?'one':'two'}.png`;
    await page.screenshot({path:`/output/${screenshot}`,fullPage:true});
    return {clock_id:clockId,observed,date_visible:Boolean(matched),
      matched_date:matched,visible_text:text,scroll_positions:scrolls,screenshot,
      visible_text_sha256:crypto.createHash('sha256').update(text).digest('hex'),
      console_errors:errors};
  }finally{await context.close();}
}
(async()=>{
  try{
    browser=await chromium.launch({headless:true,chromiumSandbox:false});
    const observations=[];
    for(let index=0;index<clocks.length;index++)
      observations.push(await runClock(clocks[index],index));
    report.observations=observations;
    for(const [id,keys] of Object.entries(groups))
      report.cases.push({id,status:observations.every(obs=>
        keys.every(key=>obs.observed[key]===expected[key]))?'passed':'failed'});
    report.cases.push({id:'generation_date_visible',
      status:observations.every(obs=>obs.date_visible)?'passed':'failed'});
    report.status='complete';
  }catch(error){
    report.status=error instanceof InterfaceError?'interface_error':'browser_error';
    report.error=String(error).slice(0,1500);report.cases=[];
  }finally{
    if(browser)await browser.close();
    fs.writeFileSync('/output/report.json',JSON.stringify(report,null,2));
    process.exitCode=report.status!=='complete'?2:report.cases.some(c=>c.status!=='passed')?1:0;
  }
})();
