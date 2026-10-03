'use strict';
const fs=require('node:fs');const crypto=require('node:crypto');const {chromium}=require('playwright');
const html=fs.readFileSync('/input/app.html');const URL='http://localhost/';
const CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const fixtures=[{"state": {"grid": {"columns": ["Item", "Qty", "Price"], "rows": [{"id": "r1", "cells": {"Item": "Apples", "Qty": 4, "Price": 1.2}}, {"id": "r2", "cells": {"Item": "Pears", "Qty": 2, "Price": 1.5}}, {"id": "r3", "cells": {"Item": "Plums", "Qty": 9, "Price": 0.8}}]}}, "steps": [["shift_f10_opens_context_menu_1", "r2", "Qty", "Shift+F10", "context"], ["menu_key_opens_context_menu_1", "r1", "Item", "ContextMenu", "context"], ["column_menu_shortcut_1", "r3", "Price", "Control+Shift+F10", "column"], ["row_menu_shortcut_1", "r1", "Qty", "Alt+Shift+F10", "row"]]}, {"state": {"grid": {"columns": ["Name", "City"], "rows": [{"id": "p1", "cells": {"Name": "Ines", "City": "Porto"}}, {"id": "p2", "cells": {"Name": "Kofi", "City": "Accra"}}]}}, "steps": [["column_menu_shortcut_2", "p1", "City", "Control+ContextMenu", "column"], ["shift_f10_opens_context_menu_2", "p2", "City", "Shift+F10", "context"], ["row_menu_shortcut_2", "p2", "Name", "Alt+ContextMenu", "row"], ["menu_key_opens_context_menu_2", "p1", "Name", "ContextMenu", "context"]]}];
const report={schema_version:'grist-context-menu-shortcut-browser/v1',status:'browser_error',
  app_sha256:crypto.createHash('sha256').update(html).digest('hex'),assertions:{},console_errors:[]};
class InterfaceError extends Error{}
async function one(page,selector){const node=page.locator(selector);if(await node.count()!==1||!await node.isVisible())throw new InterfaceError(`one visible ${selector} required`);return node}
function check(name,value){report.assertions[name]=value===true}
async function reload(page){await page.reload({waitUntil:'load',timeout:10000})}
async function journey(page,fixture,index){
  const menu=()=>page.locator('#menu').evaluate(x=>({kind:x.dataset.kind,row:x.dataset.row,col:x.dataset.col}));
  const rows=fixture.state.grid.rows.length,cols=fixture.state.grid.columns.length;
  if((await menu()).kind!==''||await page.locator('#grid td').count()!==rows*cols)throw new InterfaceError('grid missing or menu open before the key presses');
  for(const [name,row,col,key,kind] of fixture.steps){
    await (await one(page,`#grid td[data-row="${row}"][data-col="${col}"]`)).click();
    if((await menu()).kind!=='')throw new InterfaceError('menu still open after moving the cursor');
    await page.keyboard.press(key);
    const m=await menu();const items=page.locator('#menu [role=menuitem]');
    const visible=await page.locator('#menu').isVisible()&&await items.count()>0;
    const itemsVisible=visible&&await items.evaluateAll(ns=>ns.every(x=>x.checkVisibility()));
    check(name,itemsVisible&&m.kind===kind&&m.row===row&&m.col===col);
  }
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
