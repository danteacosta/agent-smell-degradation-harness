'use strict';
const fs = require('node:fs');
const {chromium} = require('playwright');
const html = fs.readFileSync('/input/app.html');
const URL='http://fixture.invalid/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
(async()=>{
 const browser=await chromium.launch({headless:true,chromiumSandbox:false});
 const context=await browser.newContext({viewport:{width:1000,height:720},timezoneId:'UTC',serviceWorkers:'block'});
 await context.addInitScript(()=>Object.defineProperty(window,'initialState',{value:{tasks:[
  {id:'task-target',title:'Release candidate',closed:false,subtasks:[
   {id:'todo-subtask',title:'Review',status:'Todo'},
   {id:'progress-subtask',title:'Package',status:'In progress'},
   {id:'done-subtask',title:'Tag',status:'Done'}]},
  {id:'task-control',title:'Unrelated task',closed:false,subtasks:[]}
 ]}}));
 await context.route('**/*',route=>route.request().url()===URL&&route.request().isNavigationRequest()?route.fulfill({body:html,contentType:'text/html',headers:{'Content-Security-Policy':CSP}}):route.abort());
 const page=await context.newPage(); page.setDefaultTimeout(2500);
 await page.goto(URL,{waitUntil:'load',timeout:10000}); await page.waitForTimeout(150);
 const task=page.locator('[data-task-id="task-target"]');
 await task.getByRole('button',{name:'Close task',exact:true}).click();
 await page.getByRole('button',{name:'Closed tasks',exact:true}).click();
 await page.screenshot({path:'/output/closed-task.png',fullPage:true});
 await context.close(); await browser.close();
})();
