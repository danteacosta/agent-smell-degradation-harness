'use strict';
const fs=require('node:fs');
const crypto=require('node:crypto');
const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');
const URL='http://localhost/';
const CLOCK='2032-04-17T12:00:00Z';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[
  [{id:'task-71',title:'Review release',dueDate:'2032-04-15'},
   {id:'task-72',title:'Plan launch',dueDate:'2032-04-20'}],
  [{id:'task-83',title:'Check migration',dueDate:'2032-03-30'},
   {id:'task-84',title:'Prepare workshop',dueDate:'2032-05-01'}],
];
const report={schema_version:'kanboard-due-date-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
function rgb(color){
  const match=/^rgba?\(\s*(\d{1,3})[ ,]+(\d{1,3})[ ,]+(\d{1,3})(?:[ ,/]+([\d.]+))?\s*\)$/.exec(color);
  if(!match)throw new InterfaceError('unsupported computed foreground color');
  const values=match.slice(1,4).map(Number);
  if(values.some(value=>value>255)|| (match[4]!==undefined&&Number(match[4])<0.9))
    throw new InterfaceError('non-opaque or malformed due-date color');
  return values;
}
function red([r,g,b]){return r>=100&&r>=1.5*g&&r>=1.5*b&&g<=160&&b<=160}
function black([r,g,b]){return Math.max(r,g,b)<=70}
async function runFixture(browser,tasks,index){
  const context=await browser.newContext({viewport:{width:1000,height:720},timezoneId:'UTC',serviceWorkers:'block'});
  try{
    await context.addInitScript(items=>Object.defineProperty(window,'boardTasks',
      {value:Object.freeze(items.map(item=>Object.freeze(item))),writable:false}),tasks);
    await context.route('**/*',route=>route.request().url()===URL&&route.request().isNavigationRequest()
      ?route.fulfill({body:html,contentType:'text/html',headers:{'Content-Security-Policy':CSP}}):route.abort());
    const page=await context.newPage();page.setDefaultTimeout(2500);
    await page.clock.setFixedTime(new Date(CLOCK));
    page.on('console',message=>{if(message.type()==='error'&&report.console_errors.length<20)
      report.console_errors.push(message.text().slice(0,500))});
    page.on('pageerror',error=>{if(report.console_errors.length<20)
      report.console_errors.push(String(error).slice(0,500))});
    await page.goto(URL,{waitUntil:'load',timeout:10000});
    const titles=[];const dueTexts=[];const colors=[];
    if(await page.locator('[data-task-id]').count()!==tasks.length)
      throw new InterfaceError('unexpected number of task cards');
    for(const task of tasks){
      const card=page.locator(`[data-task-id="${task.id}"]`);
      if(await card.count()!==1||!await card.isVisible())throw new InterfaceError('one visible task card required');
      titles.push((await card.innerText()).includes(task.title));
      const due=card.locator('[data-role="due-date"]');
      if(await due.count()!==1||!await due.isVisible())throw new InterfaceError('one visible due-date text required');
      await due.scrollIntoViewIfNeeded();
      const observation=await due.evaluate(element=>{
        const box=element.getBoundingClientRect();
        const point=document.elementFromPoint(box.left+box.width/2,box.top+box.height/2);
        return {visible:box.width>0&&box.height>0&&Boolean(point)&&
          (point===element||element.contains(point)),color:getComputedStyle(element).color};
      });
      if(!observation.visible)throw new InterfaceError('due-date text is covered or clipped');
      dueTexts.push((await due.innerText()).trim()===task.dueDate);
      colors.push(rgb(observation.color));
    }
    const suffix=index+1;
    report.assertions[`task_titles_${suffix}`]=titles.every(Boolean);
    report.assertions[`due_text_${suffix}`]=dueTexts.every(Boolean);
    report.assertions[`overdue_red_${suffix}`]=red(colors[0]);
    report.assertions[`upcoming_black_${suffix}`]=black(colors[1]);
    await page.screenshot({path:`/output/fixture-${suffix}.png`,fullPage:true});
  }finally{await context.close()}
}
(async()=>{let browser;try{
  browser=await chromium.launch({headless:true,chromiumSandbox:false});
  for(let index=0;index<fixtures.length;index++)await runFixture(browser,fixtures[index],index);
  report.status='complete';report.screenshots=['fixture-1.png','fixture-2.png'];
}catch(error){report.status=report.console_errors.length?'browser_error':error instanceof InterfaceError?'interface_error':'browser_error';
  report.assertions={};report.error=String(error).slice(0,1500);
}finally{if(browser)await browser.close();fs.writeFileSync('/output/report.json',JSON.stringify(report,null,2));
  process.exitCode=report.status==='complete'?0:2}})();
