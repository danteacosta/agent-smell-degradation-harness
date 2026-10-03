"""Grist selection cases (six admitted Grist rules; arm A from the frame-end help snapshot)."""

SNAPSHOT = "b047726e32"

CONTEXT_MENU = {
    "case": "grist-context-menu-shortcut",
    "candidate_id": "rc-4aac15b7b503",
    "project_id": "grist",
    "source": {"commit": "bcdbeb35ac", "file": "help/en/docs/keyboard-shortcuts.md",
               "snapshot": SNAPSHOT, "snapshot_file": "help/en/docs/keyboard-shortcuts.md"},
    "title": "Orders grid",
    "register": "app.onKey",
    "control": "grid (key presses while the grid has focus)",
    "body": '<h1>Orders</h1><table id="grid" tabindex="0" aria-label="Grid"><thead><tr></tr></thead><tbody></tbody></table>'
            '<div id="menu" role="menu"></div>',
    "state_js": r"""
const grid=window.initialState.grid;let cursor={row:0,col:0};let menu=null;
const ITEMS={context:['Cut','Copy','Paste','Insert row above','Insert row below','Delete row'],column:['Sort A-Z','Sort Z-A','Rename column','Hide column'],row:['Insert row above','Insert row below','Duplicate row','Delete row']};
const app=Object.freeze({
  onKey:register,
  cursor(){return {rowId:grid.rows[cursor.row].id,colId:grid.columns[cursor.col]}},
  openMenu(kind){if(!(kind in ITEMS))throw new Error('kind must be context, column or row');menu={kind,rowId:grid.rows[cursor.row].id,colId:grid.columns[cursor.col]};render()},
  closeMenu(){menu=null;render()}
});
function render(){
  document.querySelector('#grid thead tr').replaceChildren(el('th',{},'#'),...grid.columns.map(c=>el('th',{},c)));
  const body=document.querySelector('#grid tbody');body.replaceChildren();
  grid.rows.forEach((r,i)=>{const tr=el('tr');tr.append(el('th',{},String(i+1)));
    grid.columns.forEach((c,j)=>{const attrs={'data-row':r.id,'data-col':c,'data-r':i,'data-c':j};if(i===cursor.row&&j===cursor.col)attrs.style='outline:2px solid #16b378';tr.append(el('td',attrs,String(r.cells[c])))});body.append(tr)});
  const m=document.querySelector('#menu');m.hidden=!menu;m.dataset.kind=menu?menu.kind:'';m.dataset.row=menu?menu.rowId:'';m.dataset.col=menu?menu.colId:'';
  m.replaceChildren(...(menu?ITEMS[menu.kind].map(t=>el('div',{role:'menuitem'},t)):[]));
}
document.querySelector('#grid').addEventListener('click',e=>{const td=e.target.closest('td');if(!td)return;cursor={row:Number(td.dataset.r),col:Number(td.dataset.c)};menu=null;render()});
document.querySelector('#grid').addEventListener('keydown',e=>{if(behavior)behavior({key:e.key,shiftKey:e.shiftKey,ctrlKey:e.ctrlKey,altKey:e.altKey,metaKey:e.metaKey})});
""",
    "fixtures": [
        {"state": {"grid": {"columns": ["Item", "Qty", "Price"], "rows": [
            {"id": "r1", "cells": {"Item": "Apples", "Qty": 4, "Price": 1.2}},
            {"id": "r2", "cells": {"Item": "Pears", "Qty": 2, "Price": 1.5}},
            {"id": "r3", "cells": {"Item": "Plums", "Qty": 9, "Price": 0.8}}]}},
         "steps": [["shift_f10_opens_context_menu_1", "r2", "Qty", "Shift+F10", "context"],
                   ["menu_key_opens_context_menu_1", "r1", "Item", "ContextMenu", "context"],
                   ["column_menu_shortcut_1", "r3", "Price", "Control+Shift+F10", "column"],
                   ["row_menu_shortcut_1", "r1", "Qty", "Alt+Shift+F10", "row"]]},
        {"state": {"grid": {"columns": ["Name", "City"], "rows": [
            {"id": "p1", "cells": {"Name": "Ines", "City": "Porto"}},
            {"id": "p2", "cells": {"Name": "Kofi", "City": "Accra"}}]}},
         "steps": [["column_menu_shortcut_2", "p1", "City", "Control+ContextMenu", "column"],
                   ["shift_f10_opens_context_menu_2", "p2", "City", "Shift+F10", "context"],
                   ["row_menu_shortcut_2", "p2", "Name", "Alt+ContextMenu", "row"],
                   ["menu_key_opens_context_menu_2", "p1", "Name", "ContextMenu", "context"]]},
    ],
    "journey_js": r"""
  const menu=()=>page.locator('#menu').evaluate(x=>({kind:x.dataset.kind,row:x.dataset.row,col:x.dataset.col}));
  const rows=fixture.state.grid.rows.length,cols=fixture.state.grid.columns.length;
  if((await menu()).kind!==''||await page.locator('#grid td').count()!==rows*cols)throw new InterfaceError('grid missing or menu open before the key presses');
  for(const [name,row,col,key,kind] of fixture.steps){
    await (await one(page,`#grid td[data-row="${row}"][data-col="${col}"]`)).click();
    if((await menu()).kind!=='')throw new InterfaceError('menu still open after moving the cursor');
    await page.keyboard.press(key);
    const m=await menu();check(name,m.kind===kind&&m.row===row&&m.col===col);
  }
""",
    "target": ["shift_f10_opens_context_menu_1", "shift_f10_opens_context_menu_2"],
    "non_target": ["menu_key_opens_context_menu_1", "column_menu_shortcut_1", "row_menu_shortcut_1",
                   "column_menu_shortcut_2", "row_menu_shortcut_2", "menu_key_opens_context_menu_2"],
    "controls": {
        "reference": ("app.onKey(e=>{if(!(e.key==='ContextMenu'||(e.key==='F10'&&e.shiftKey)))return;if(e.ctrlKey)app.openMenu('column');else if(e.altKey)app.openMenu('row');else app.openMenu('context')});", "pass"),
        "alternative": ("const SHORTCUTS={'ContextMenu':'context','Shift+F10':'context','Ctrl+ContextMenu':'column','Ctrl+Shift+F10':'column','Alt+ContextMenu':'row','Alt+Shift+F10':'row'};app.onKey(function(e){var name=(e.ctrlKey?'Ctrl+':'')+(e.altKey?'Alt+':'')+(e.shiftKey?'Shift+':'')+e.key;if(SHORTCUTS[name])app.openMenu(SHORTCUTS[name])});", "pass"),
        "target-mutant": ("app.onKey(e=>{const kind=e.ctrlKey?'column':e.altKey?'row':'context';if(e.key==='ContextMenu')app.openMenu(kind);else if(e.key==='F10'&&e.shiftKey&&kind!=='context')app.openMenu(kind)});", "target_only_failure"),
        "non-target-mutant": ("app.onKey(e=>{if(e.key==='ContextMenu'||(e.key==='F10'&&e.shiftKey))app.openMenu('context')});", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement the grid's menu keyboard shortcuts (Windows key bindings). The handler receives each key press "
             "in the grid as {key, shiftKey, ctrlKey, altKey, metaKey}; open the matching menu for the cursor cell with "
             "app.openMenu(kind), where kind is 'context', 'column' or 'row'. Menu or Shift + F10: Open the context "
             "menu. Ctrl + Menu or Ctrl + Shift + F10: Open the current column menu. Alt + Menu or Alt + Shift + F10: "
             "Open the current row menu.",
        "B": "Key presses in the grid reach the handler as {key, shiftKey, ctrlKey, altKey, metaKey}, and the "
             "Windows key bindings apply; each shortcut opens its menu for the cell under the cursor through "
             "app.openMenu(kind), with kind 'context', 'column' or 'row'. The current row menu opens with "
             "Alt + Shift + F10 or Alt + Menu, the current column menu with Ctrl + Shift + F10 or Ctrl + Menu, and "
             "the context menu with Shift + F10 or the Menu key.",
        "C": "Implement the grid's menu keyboard shortcuts (Windows key bindings). The handler receives each key press "
             "in the grid as {key, shiftKey, ctrlKey, altKey, metaKey}; open the matching menu for the cursor cell with "
             "app.openMenu(kind), where kind is 'context', 'column' or 'row'. Menu: Open the context "
             "menu. Ctrl + Menu or Ctrl + Shift + F10: Open the current column menu. Alt + Menu or Alt + Shift + F10: "
             "Open the current row menu.",
    },
}

PAGE_COLLAPSE = {
    "case": "grist-page-default-collapse",
    "candidate_id": "rc-7b485b51412f",
    "project_id": "grist",
    "source": {"commit": "537c682145", "file": "help/en/docs/page-widgets.md",
               "snapshot": SNAPSHOT, "snapshot_file": "help/en/docs/page-widgets.md"},
    "title": "Pages",
    "register": "app.onPages",
    "control": "page list (document opening and the three-dot page menu)",
    "body": '<h1>Raw data</h1><nav aria-label="Pages"><ul id="pages"></ul></nav><div id="page-menu" role="menu" hidden></div>',
    "state_js": r"""
const pages=window.initialState.pages;let settings=load({});const expanded={};let menuFor=null;let menuItems=[];
function known(id){if(!pages.some(p=>p.id===id))throw new Error('unknown page')}
const app=Object.freeze({
  onPages:register,
  pages(){return structuredClone(pages)},
  pageSettings(id){known(id);return structuredClone(settings[id]||{})},
  savePageSetting(id,name,value){known(id);if(typeof name!=='string'||!name)throw new Error('setting name required');settings[id]={...(settings[id]||{}),[name]:value};store(settings)},
  setExpanded(id,open){known(id);expanded[id]=open===true;render()},
  showMenu(items){if(!Array.isArray(items)||!items.every(i=>i&&typeof i.label==='string'&&typeof i.run==='function'))throw new Error('menu items need label and run');menuItems=items.slice();render()}
});
function render(){
  const list=document.querySelector('#pages');list.replaceChildren();
  for(const p of pages.filter(p=>p.parent===null)){
    const kids=pages.filter(c=>c.parent===p.id);const open=expanded[p.id]===true;
    const li=el('li',{'data-id':p.id,'data-expanded':String(open)});
    if(kids.length)li.append(el('button',{type:'button',class:'toggle','aria-label':'Toggle '+p.name},open?'▾':'▸'));
    li.append(document.createTextNode(' '+p.name+' '),el('button',{type:'button',class:'more','aria-label':'Page options for '+p.name},'⋮'));
    if(kids.length&&open){const ul=el('ul');for(const c of kids)ul.append(el('li',{'data-id':c.id,'data-parent':p.id},c.name));li.append(ul)}
    list.append(li)}
  const menu=document.querySelector('#page-menu');menu.hidden=menuFor===null;menu.replaceChildren();
  if(menuFor!==null)menuItems.forEach((item,i)=>menu.append(el('button',{type:'button',role:'menuitem','data-index':i},item.label)));
}
document.querySelector('#pages').addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;const id=b.closest('li').dataset.id;
  if(b.classList.contains('toggle')){expanded[id]=expanded[id]!==true;render()}
  else if(b.classList.contains('more')){menuFor=id;menuItems=[];render();if(behavior)behavior({type:'menu',pageId:id})}});
document.querySelector('#page-menu').addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;const item=menuItems[Number(b.dataset.index)];menuFor=null;menuItems=[];render();if(item)item.run()});
document.addEventListener('DOMContentLoaded',()=>{if(behavior)behavior({type:'open'})});
""",
    "fixtures": [
        {"state": {"pages": [
            {"id": "sales", "name": "Sales", "parent": None},
            {"id": "q1", "name": "Q1", "parent": "sales"},
            {"id": "q2", "name": "Q2", "parent": "sales"},
            {"id": "contacts", "name": "Contacts", "parent": None},
            {"id": "people", "name": "People", "parent": "contacts"},
            {"id": "summary", "name": "Summary", "parent": None}]},
         "target": "sales", "manual": None},
        {"state": {"pages": [
            {"id": "projects", "name": "Projects", "parent": None},
            {"id": "alpha", "name": "Alpha", "parent": "projects"},
            {"id": "beta", "name": "Beta", "parent": "projects"},
            {"id": "gamma", "name": "Gamma", "parent": "projects"},
            {"id": "team", "name": "Team", "parent": None},
            {"id": "members", "name": "Members", "parent": "team"},
            {"id": "roles", "name": "Roles", "parent": "team"},
            {"id": "archive", "name": "Archive", "parent": None},
            {"id": "y2024", "name": "2024", "parent": "archive"}]},
         "target": "team", "manual": "projects"},
    ],
    "journey_js": r"""
  const n=index+1;const pages=fixture.state.pages;const parents=pages.filter(p=>p.parent===null).map(p=>p.id);
  const kids=id=>pages.filter(p=>p.parent===id).length;
  const shown=()=>page.locator('#pages > li').evaluateAll(ns=>Object.fromEntries(ns.map(li=>[li.dataset.id,li.querySelectorAll('li[data-parent]').length])));
  const first=await shown();
  if(JSON.stringify(Object.keys(first))!==JSON.stringify(parents)||!await page.locator('#page-menu').isHidden())throw new InterfaceError('page list missing or menu open');
  check(`nested_expanded_on_open_${n}`,parents.every(id=>first[id]===kids(id)));
  if(fixture.manual)await (await one(page,`#pages > li[data-id="${fixture.manual}"] > .toggle`)).click();
  await (await one(page,`#pages > li[data-id="${fixture.target}"] > .more`)).click();
  const items=page.locator('#page-menu button');let picked=false;const count=await items.count();
  for(let i=0;i<count;i++){const item=items.nth(i);if(/^set default:\s*collapse$/i.test((await item.innerText()).trim())&&await item.isVisible()){await item.click();picked=true;break}}
  await reload(page);
  const after=await shown();
  check(`collapsed_on_reopen_${n}`,picked&&fixture.target in after&&after[fixture.target]===0);
  check(`other_pages_expanded_on_reopen_${n}`,parents.filter(id=>id!==fixture.target).every(id=>after[id]===kids(id)));
""",
    "target": ["collapsed_on_reopen_1", "collapsed_on_reopen_2"],
    "non_target": ["nested_expanded_on_open_1", "nested_expanded_on_open_2",
                   "other_pages_expanded_on_reopen_1", "other_pages_expanded_on_reopen_2"],
    "controls": {
        "reference": ("app.onPages(ev=>{if(ev.type==='open'){for(const p of app.pages())app.setExpanded(p.id,app.pageSettings(p.id).collapsed!==true);return}"
                      "const id=ev.pageId;const collapsed=app.pageSettings(id).collapsed===true;"
                      "app.showMenu([{label:collapsed?'Set default: Expand':'Set default: Collapse',run(){app.savePageSetting(id,'collapsed',!collapsed)}}])});", "pass"),
        "alternative": ("app.onPages(function(ev){if(ev.type==='open'){app.pages().forEach(function(p){app.setExpanded(p.id,app.pageSettings(p.id).defaultState!=='collapse')})}"
                        "else{var id=ev.pageId;app.showMenu([{label:'Rename',run:function(){}},{label:'Set default: Collapse',run:function(){app.savePageSetting(id,'defaultState','collapse');app.setExpanded(id,false)}},"
                        "{label:'Set default: Expand',run:function(){app.savePageSetting(id,'defaultState','expand');app.setExpanded(id,true)}}])}});", "pass"),
        "target-mutant": ("app.onPages(ev=>{if(ev.type==='open')for(const p of app.pages())app.setExpanded(p.id,true);else app.showMenu([])});", "target_only_failure"),
        "collapse-now-mutant": ("app.onPages(ev=>{if(ev.type==='open')for(const p of app.pages())app.setExpanded(p.id,true);"
                                "else app.showMenu([{label:'Set default: Collapse',run(){app.setExpanded(ev.pageId,false)}}])});", "target_only_failure"),
        "non-target-mutant": ("app.onPages(ev=>{if(ev.type==='open'){for(const p of app.pages())if(app.pageSettings(p.id).collapsed)app.setExpanded(p.id,false);return}"
                              "app.showMenu([{label:'Set default: Collapse',run(){app.savePageSetting(ev.pageId,'collapsed',true)}}])});", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement the page list. app.onPages(handler) receives {type: 'open'} when the document is opened and "
             "{type: 'menu', pageId} when the three-dot icon to the right of a page is clicked. app.pages() gives each "
             "page with its parent page (null at the top level); expand or collapse a parent page's nested pages with "
             "app.setExpanded(id, open), list the entries of the three-dot menu with app.showMenu([{label, run}]), and "
             "keep per-page settings across openings with app.savePageSetting(id, name, value) and "
             "app.pageSettings(id). By default, nested pages will be expanded when a document is opened. You can "
             "change the default state by clicking the three-dot icon to the right of the parent page and selecting "
             "'Set default: Collapse'.",
        "B": "The handler given to app.onPages gets {type: 'open'} when the document opens and {type: 'menu', pageId} "
             "when someone clicks the three-dot icon beside a page. Each page from app.pages() names its parent page "
             "(null for top-level pages); app.setExpanded(id, open) expands or collapses a parent's nested pages, "
             "app.showMenu([{label, run}]) sets the entries of the three-dot menu, and app.savePageSetting(id, name, "
             "value) with app.pageSettings(id) keeps per-page settings from one opening to the next. Opening a "
             "document shows nested pages expanded unless the default state was changed: the three-dot icon of a "
             "parent page offers 'Set default: Collapse', which changes that page's default state to collapsed.",
        "C": "Implement the page list. app.onPages(handler) receives {type: 'open'} when the document is opened and "
             "{type: 'menu', pageId} when the three-dot icon to the right of a page is clicked. app.pages() gives each "
             "page with its parent page (null at the top level); expand or collapse a parent page's nested pages with "
             "app.setExpanded(id, open), list the entries of the three-dot menu with app.showMenu([{label, run}]), and "
             "keep per-page settings across openings with app.savePageSetting(id, name, value) and "
             "app.pageSettings(id). By default, nested pages will be expanded when a document is opened.",
    },
}

TUTORIAL_RESTART = {
    "case": "grist-tutorial-restart",
    "candidate_id": "rc-aac66a0af69a",
    "project_id": "grist",
    "source": {"commit": "4c173049c5", "file": "help/en/docs/document-tutorials.md",
               "snapshot": SNAPSHOT, "snapshot_file": "help/en/docs/document-tutorials.md"},
    "title": "Lunch orders tutorial",
    "register": "app.onRestart",
    "control": "Restart button at the bottom of the tutorial popup",
    "body": '<h1>Lunch orders (your fork)</h1><table id="grid" aria-label="Orders"><tbody></tbody></table>'
            '<button id="replace" type="button">Replace original</button><p id="message" role="status"></p>'
            '<aside aria-label="Tutorial" style="border:1px solid #bbb;padding:1rem;margin-top:1rem">'
            '<p id="slide"></p><button id="prev" type="button">Previous</button> <button id="next" type="button">Next</button>'
            '<footer style="margin-top:1rem"><button id="restart" type="button">Restart</button></footer></aside>',
    "state_js": r"""
const init=window.initialState;let s=load({slide:init.slide,fork:structuredClone(init.rows),original:structuredClone(init.rows)});
function row(id){const r=s.fork.find(r=>r.id===id);if(!r)throw new Error('unknown row');return r}
const app=Object.freeze({
  onRestart:register,
  slide(){return s.slide},
  setSlide(i){if(!Number.isInteger(i)||i<0||i>=init.slides.length)throw new Error('no such slide');s.slide=i;store(s);render()},
  forkRows(){return structuredClone(s.fork)},
  originalRows(){return structuredClone(s.original)},
  setCell(id,value){row(id).value=String(value);store(s);render()},
  refresh(){location.reload()}
});
function render(){
  const body=document.querySelector('#grid tbody');body.replaceChildren();
  for(const r of s.fork){const input=el('input',{'data-row':r.id,'data-stored':r.value,'aria-label':r.label});input.value=r.value;
    const td=el('td');td.append(input);const tr=el('tr');tr.append(el('th',{},r.label),td);body.append(tr)}
  const sl=document.querySelector('#slide');sl.dataset.index=String(s.slide);sl.textContent='Slide '+(s.slide+1)+' of '+init.slides.length+': '+init.slides[s.slide];
}
document.querySelector('#grid').addEventListener('change',e=>{if(!e.target.matches('input[data-row]'))return;row(e.target.dataset.row).value=e.target.value;store(s);render()});
document.querySelector('#replace').addEventListener('click',()=>{s.original=structuredClone(s.fork);store(s);document.querySelector('#message').textContent='Original replaced'});
document.querySelector('#prev').addEventListener('click',()=>{if(s.slide>0){s.slide-=1;store(s);render()}});
document.querySelector('#next').addEventListener('click',()=>{if(s.slide<init.slides.length-1){s.slide+=1;store(s);render()}});
document.querySelector('#restart').addEventListener('click',()=>{if(behavior)behavior()});
""",
    "fixtures": [
        {"state": {"slide": 2, "slides": ["Welcome", "Add a dish", "Change an order", "Done"],
                   "rows": [{"id": "mon", "label": "Monday", "value": "Pasta"},
                            {"id": "tue", "label": "Tuesday", "value": "Soup"},
                            {"id": "wed", "label": "Wednesday", "value": "Salad"}]},
         "saved": None, "unsaved": ["tue", "Curry"]},
        {"state": {"slide": 1, "slides": ["Start", "Edit prices", "Finish"],
                   "rows": [{"id": "tea", "label": "Tea", "value": "2.00"},
                            {"id": "cake", "label": "Cake", "value": "3.50"},
                            {"id": "pie", "label": "Pie", "value": "4.00"}]},
         "saved": ["cake", "3.80"], "unsaved": ["pie", "4.75"]},
    ],
    "journey_js": r"""
  const n=index+1;
  const read=()=>page.evaluate(()=>({slide:document.querySelector('#slide').dataset.index,cells:Object.fromEntries([...document.querySelectorAll('#grid input')].map(i=>[i.dataset.row,i.dataset.stored]))}));
  const initial=Object.fromEntries(fixture.state.rows.map(r=>[r.id,r.value]));
  const before=await read();
  if(before.slide!==String(fixture.state.slide)||JSON.stringify(before.cells)!==JSON.stringify(initial))throw new InterfaceError('tutorial state changed before editing');
  async function edit([id,value]){const input=await one(page,`#grid input[data-row="${id}"]`);await input.fill(value);await input.press('Tab')}
  if(fixture.saved){await edit(fixture.saved);await (await one(page,'#replace')).click()}
  await edit(fixture.unsaved);
  if((await read()).cells[fixture.unsaved[0]]!==fixture.unsaved[1])throw new InterfaceError('edit not applied to the fork');
  await page.evaluate(()=>{window.__beforeRestart=true});
  await (await one(page,'#restart')).click();
  await page.waitForTimeout(500);await page.waitForLoadState('load');
  const refreshed=await page.evaluate(()=>window.__beforeRestart!==true);
  const after=await read();
  check(`unsaved_edit_lost_${n}`,after.cells[fixture.unsaved[0]]===initial[fixture.unsaved[0]]);
  check(`page_refreshed_${n}`,refreshed);
  check(`tutorial_restarted_${n}`,after.slide==='0');
  if(fixture.saved)check(`saved_edit_kept_${n}`,after.cells[fixture.saved[0]]===fixture.saved[1]);
  else check(`other_rows_unchanged_${n}`,Object.entries(initial).every(([k,v])=>k===fixture.unsaved[0]||after.cells[k]===v));
""",
    "target": ["unsaved_edit_lost_1", "unsaved_edit_lost_2"],
    "non_target": ["page_refreshed_1", "tutorial_restarted_1", "other_rows_unchanged_1",
                   "page_refreshed_2", "tutorial_restarted_2", "saved_edit_kept_2"],
    "controls": {
        "reference": ("app.onRestart(()=>{for(const r of app.originalRows())app.setCell(r.id,r.value);app.setSlide(0);app.refresh()});", "pass"),
        "alternative": ("app.onRestart(function(){var orig={};app.originalRows().forEach(function(r){orig[r.id]=r.value});app.forkRows().forEach(function(r){if(r.value!==orig[r.id])app.setCell(r.id,orig[r.id])});app.setSlide(0);location.reload()});", "pass"),
        "target-mutant": ("app.onRestart(()=>{app.setSlide(0);app.refresh()});", "target_only_failure"),
        "non-target-mutant": ("app.onRestart(()=>{for(const r of app.originalRows())app.setCell(r.id,r.value);app.setSlide(0)});", "non_target_only_failure"),
        "pristine-mutant": ("app.onRestart(()=>{for(const r of window.initialState.rows)app.setCell(r.id,r.value);app.setSlide(0);app.refresh()});", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement the Restart button of the tutorial popup. You work in your own fork of the tutorial document: "
             "edits in the grid change only the fork (app.forkRows(), app.setCell(id, value)), and clicking Replace "
             "original saves the fork's data to the main document (app.originalRows()). Restart starts the tutorial "
             "again from the first slide (app.setSlide(0)); app.refresh() refreshes the page. Clicking 'Restart' at "
             "the bottom of the tutorial popup will refresh the page, causing any unsaved changes to be lost. Be sure "
             "to save changes to the main document prior to clicking this.",
        "B": "The tutorial popup has a Restart button at its bottom. The user works in a personal fork of the tutorial "
             "document: grid edits change only that fork (app.forkRows(), app.setCell(id, value)), while the Replace "
             "original button saves the fork's data into the main document (app.originalRows()). Restarting takes the "
             "tutorial back to its first slide (app.setSlide(0)) and refreshes the page, which app.refresh() does; "
             "any change not yet saved is lost when Restart is clicked, so changes should be saved to the main "
             "document before clicking it.",
        "C": "Implement the Restart button of the tutorial popup. You work in your own fork of the tutorial document: "
             "edits in the grid change only the fork (app.forkRows(), app.setCell(id, value)), and clicking Replace "
             "original saves the fork's data to the main document (app.originalRows()). Restart starts the tutorial "
             "again from the first slide (app.setSlide(0)); app.refresh() refreshes the page. Clicking 'Restart' at "
             "the bottom of the tutorial popup will refresh the page. Be sure "
             "to save changes to the main document prior to clicking this.",
    },
}

SUGGESTIONS_COPY = {
    "case": "grist-suggestions-open-copy",
    "candidate_id": "rc-ade633af9c14",
    "project_id": "grist",
    "source": {"commit": "af6962bf5b", "file": "help/en/docs/sharing.md",
               "snapshot": SNAPSHOT, "snapshot_file": "help/en/docs/sharing.md"},
    "title": "Documents",
    "register": "app.onDocument",
    "control": "Open buttons and the cells of the shown document",
    "body": '<h1>Documents</h1><p id="who"></p><ul id="docs" aria-label="Documents"></ul>'
            '<section id="view" aria-label="Shown document"><h2 id="view-title"></h2><table id="grid"><tbody></tbody></table></section>',
    "state_js": r"""
const user=window.initialState.user;
let s=load({docs:window.initialState.docs.map(d=>({...d,copyOf:null,owner:null})),shown:null,copies:0});
function doc(id){const d=s.docs.find(d=>d.id===id);if(!d)throw new Error('unknown document');return d}
const app=Object.freeze({
  onDocument:register,
  user(){return structuredClone(user)},
  documents(){return structuredClone(s.docs)},
  copy(id){const d=doc(id);s.copies+=1;const c={...structuredClone(d),id:d.id+'~copy'+s.copies,copyOf:d.id,owner:user?user.id:null};s.docs.push(c);store(s);render();return c.id},
  show(id){doc(id);s.shown=id;store(s);render()},
  setCell(docId,rowId,value){const r=doc(docId).rows.find(r=>r.id===rowId);if(!r)throw new Error('unknown row');r.value=String(value);store(s);render()}
});
function render(){
  document.querySelector('#who').textContent=user?'Signed in as '+user.name:'Not signed in';
  const list=document.querySelector('#docs');list.replaceChildren();
  for(const d of s.docs.filter(d=>d.copyOf===null)){const li=el('li',{'data-id':d.id,'data-cells':JSON.stringify(Object.fromEntries(d.rows.map(r=>[r.id,r.value])))},d.name+(d.suggestions?' (suggestions enabled) ':' '));
    li.append(el('button',{type:'button',class:'open'},'Open'));list.append(li)}
  const v=document.querySelector('#view');const d=s.shown===null?null:doc(s.shown);
  v.dataset.shown=d?d.id:'';v.dataset.copyOf=d&&d.copyOf?d.copyOf:'';
  document.querySelector('#view-title').textContent=d?(d.copyOf?'Copy of '+doc(d.copyOf).name:d.name):'No document open';
  const body=document.querySelector('#grid tbody');body.replaceChildren();
  if(d)for(const r of d.rows){const input=el('input',{'data-row':r.id,'data-stored':r.value,'aria-label':r.label});input.value=r.value;const td=el('td');td.append(input);const tr=el('tr');tr.append(el('th',{},r.label),td);body.append(tr)}
}
document.querySelector('#docs').addEventListener('click',e=>{const b=e.target.closest('button.open');if(b&&behavior)behavior({type:'open',docId:b.closest('li').dataset.id})});
document.querySelector('#grid').addEventListener('change',e=>{if(e.target.matches('input[data-row]')&&behavior)behavior({type:'edit',docId:s.shown,rowId:e.target.dataset.row,value:e.target.value})});
""",
    "fixtures": [
        {"state": {"user": {"id": "u1", "name": "Ana"}, "docs": [
            {"id": "inventory", "name": "Inventory", "suggestions": False,
             "rows": [{"id": "bolts", "label": "Bolts", "value": "120"}, {"id": "nuts", "label": "Nuts", "value": "80"}]},
            {"id": "survey", "name": "Survey results", "suggestions": True,
             "rows": [{"id": "q1", "label": "Question 1", "value": "Yes"}, {"id": "q2", "label": "Question 2", "value": "No"}]}]},
         "plain": "inventory", "plain_edit": ["nuts", "95"], "suggested": "survey", "edit": ["q2", "Maybe"]},
        {"state": {"user": None, "docs": [
            {"id": "budget", "name": "Public budget", "suggestions": True,
             "rows": [{"id": "parks", "label": "Parks", "value": "5000"}, {"id": "roads", "label": "Roads", "value": "9000"},
                      {"id": "library", "label": "Library", "value": "3000"}]},
            {"id": "prices", "name": "Price list", "suggestions": False,
             "rows": [{"id": "tea", "label": "Tea", "value": "2.00"}]}]},
         "plain": "prices", "plain_edit": None, "suggested": "budget", "edit": ["library", "3500"]},
    ],
    "journey_js": r"""
  const n=index+1;
  const view=()=>page.locator('#view').evaluate(v=>({shown:v.dataset.shown,copyOf:v.dataset.copyOf,cells:Object.fromEntries([...v.querySelectorAll('input[data-row]')].map(i=>[i.dataset.row,i.dataset.stored]))}));
  const originals=()=>page.locator('#docs li').evaluateAll(ns=>Object.fromEntries(ns.map(li=>[li.dataset.id,li.dataset.cells])));
  const cellsOf=id=>JSON.stringify(Object.fromEntries(fixture.state.docs.find(d=>d.id===id).rows.map(r=>[r.id,r.value])));
  const start=await originals();
  if((await view()).shown!==''||JSON.stringify(start)!==JSON.stringify(Object.fromEntries(fixture.state.docs.map(d=>[d.id,cellsOf(d.id)]))))throw new InterfaceError('documents missing or a document already open');
  async function edit([row,value]){const input=await one(page,`#view input[data-row="${row}"]`);await input.fill(value);await input.press('Tab')}
  await (await one(page,`#docs li[data-id="${fixture.plain}"] button.open`)).click();
  const plain=await view();
  check(`plain_document_opened_${n}`,plain.shown===fixture.plain&&plain.copyOf==='');
  if(fixture.plain_edit){
    if(plain.shown!=='')await edit(fixture.plain_edit);
    check(`plain_edit_live_${n}`,JSON.parse((await originals())[fixture.plain])[fixture.plain_edit[0]]===fixture.plain_edit[1]);
  }
  await (await one(page,`#docs li[data-id="${fixture.suggested}"] button.open`)).click();
  const opened=await view();
  check(`copy_opened_${n}`,opened.copyOf===fixture.suggested&&opened.shown!==fixture.suggested&&opened.shown!=='');
  if(opened.shown!=='')await edit(fixture.edit);
  const edited=await view();
  check(`edit_in_copy_${n}`,edited.copyOf===fixture.suggested&&edited.cells[fixture.edit[0]]===fixture.edit[1]);
  check(`original_unchanged_${n}`,(await originals())[fixture.suggested]===cellsOf(fixture.suggested));
""",
    "target": ["copy_opened_1", "copy_opened_2"],
    "non_target": ["plain_document_opened_1", "plain_edit_live_1", "edit_in_copy_1", "original_unchanged_1",
                   "plain_document_opened_2", "edit_in_copy_2", "original_unchanged_2"],
    "controls": {
        "reference": ("app.onDocument(ev=>{if(ev.type==='open'){const d=app.documents().find(x=>x.id===ev.docId);app.show(d.suggestions?app.copy(d.id):d.id)}else app.setCell(ev.docId,ev.rowId,ev.value)});", "pass"),
        "alternative": ("app.onDocument(function(ev){var docs=app.documents();var d=docs.find(function(x){return x.id===ev.docId});if(ev.type==='open'){if(!d.suggestions){app.show(d.id);return}"
                        "var mine=docs.find(function(x){return x.copyOf===d.id&&x.owner===(app.user()?app.user().id:null)});app.show(mine?mine.id:app.copy(d.id))}else if(ev.type==='edit'){app.setCell(d.id,ev.rowId,ev.value)}});", "pass"),
        "target-mutant": ("app.onDocument(ev=>{if(ev.type==='open'){app.show(ev.docId);return}const d=app.documents().find(x=>x.id===ev.docId);"
                          "if(d.suggestions&&d.copyOf===null){const c=app.copy(d.id);app.show(c);app.setCell(c,ev.rowId,ev.value)}else app.setCell(ev.docId,ev.rowId,ev.value)});", "target_only_failure"),
        "signed-in-only-mutant": ("app.onDocument(ev=>{if(ev.type==='open'){const d=app.documents().find(x=>x.id===ev.docId);app.show(d.suggestions&&app.user()?app.copy(d.id):d.id)}else app.setCell(ev.docId,ev.rowId,ev.value)});", "mixed_failure"),
        "non-target-mutant": ("app.onDocument(ev=>{if(ev.type==='open')app.show(app.copy(ev.docId));else app.setCell(ev.docId,ev.rowId,ev.value)});", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement opening and editing documents. app.onDocument(handler) receives {type: 'open', docId} when a "
             "document's Open button is clicked and {type: 'edit', docId, rowId, value} when a cell of the shown "
             "document is edited. app.documents() lists the documents and whether suggestions are enabled for each, "
             "app.user() is the signed-in user or null when signed out, app.copy(id) makes a copy of a document and "
             "returns its id, app.show(id) shows a document, and app.setCell(docId, rowId, value) changes a cell. "
             "Without suggestions, changes to data in a document are made in real time. With suggestions enabled, "
             "users (signed-in or not) automatically open a copy of a document. With suggestions, edits are made to "
             "a copy without modifying the original, and are then submitted as suggestions to be reviewed by the "
             "document Owner prior to integration (submitting is not part of this page).",
        "B": "The handler registered with app.onDocument is called with {type: 'open', docId} when an Open button is "
             "clicked and with {type: 'edit', docId, rowId, value} when a cell of the shown document changes. "
             "app.documents() returns the documents, each saying whether it has suggestions enabled; app.user() is the "
             "signed-in user, or null for someone signed out; app.copy(id) copies a document and returns the copy's "
             "id; app.show(id) shows a document; app.setCell(docId, rowId, value) changes a cell. A document without "
             "suggestions takes data changes in real time. When a document has suggestions enabled, opening it "
             "automatically opens a copy instead, for signed-in and signed-out users alike, and edits go to that copy "
             "while the original stays unmodified; the edits are later submitted as suggestions for the document "
             "Owner to review before integration (submitting is not part of this page).",
        "C": "Implement opening and editing documents. app.onDocument(handler) receives {type: 'open', docId} when a "
             "document's Open button is clicked and {type: 'edit', docId, rowId, value} when a cell of the shown "
             "document is edited. app.documents() lists the documents and whether suggestions are enabled for each, "
             "app.user() is the signed-in user or null when signed out, app.copy(id) makes a copy of a document and "
             "returns its id, app.show(id) shows a document, and app.setCell(docId, rowId, value) changes a cell. "
             "Without suggestions, changes to data in a document are made in real time. With suggestions, edits are made to "
             "a copy without modifying the original, and are then submitted as suggestions to be reviewed by the "
             "document Owner prior to integration (submitting is not part of this page).",
    },
}

FORK_REDIRECT = {
    "case": "grist-tutorial-fork-return",
    "candidate_id": "rc-b49db6870ff5",
    "project_id": "grist",
    "source": {"commit": "b5e6d897fc", "file": "help/en/docs/document-tutorials.md",
               "snapshot": SNAPSHOT, "snapshot_file": "help/en/docs/document-tutorials.md"},
    "title": "Tutorial document",
    "register": "app.onGo",
    "control": "Go button of the address bar",
    "body": '<h1>Tutorial document</h1><p id="user"></p><label>Address <input id="address" size="70"></label>'
            '<button id="go" type="button">Go</button> <button id="close" type="button">Close document</button>'
            '<section id="view" aria-label="Shown document"><p id="view-url"></p><table id="grid"><tbody></tbody></table></section>',
    "state_js": r"""
const user=window.initialState.user;
let s=load({docs:window.initialState.docs,forks:window.initialState.forks,shown:null,created:0});
function find(id){const d=s.docs.find(d=>d.id===id)||s.forks.find(f=>f.id===id);if(!d)throw new Error('unknown document or fork');return d}
const app=Object.freeze({
  onGo:register,
  user(){return structuredClone(user)},
  documents(){return structuredClone(s.docs)},
  forks(){return structuredClone(s.forks)},
  createFork(docId){const d=s.docs.find(d=>d.id===docId);if(!d)throw new Error('unknown document');s.created+=1;
    const forkId='n'+s.created+'Q7xK'+docId.length;const f={id:docId+'~'+forkId+'~'+user.id,docId,forkId,userId:user.id,rows:structuredClone(d.rows)};
    s.forks.push(f);store(s);return f.id},
  show(id){find(id);s.shown=id;store(s);render()}
});
function render(){
  document.querySelector('#user').textContent='Signed in as '+user.name+' (user '+user.id+')';
  const v=document.querySelector('#view');const d=s.shown===null?null:find(s.shown);
  v.dataset.shown=d?d.id:'';v.dataset.doc=d?(d.docId||d.id):'';v.dataset.forkUser=d&&d.userId?d.userId:'';
  document.querySelector('#view-url').textContent=d?'Showing https://docs.getgrist.com/doc/'+d.id+(d.docId?' (fork)':' (original)'):'No document open';
  const body=document.querySelector('#grid tbody');body.replaceChildren();
  if(d)for(const r of d.rows){const input=el('input',{'data-row':r.id,'data-stored':r.value,'aria-label':r.label});input.value=r.value;const td=el('td');td.append(input);const tr=el('tr');tr.append(el('th',{},r.label),td);body.append(tr)}
}
document.querySelector('#go').addEventListener('click',()=>{if(behavior)behavior(document.querySelector('#address').value)});
document.querySelector('#close').addEventListener('click',()=>{s.shown=null;store(s);render()});
document.querySelector('#grid').addEventListener('change',e=>{if(!e.target.matches('input[data-row]')||s.shown===null)return;const r=find(s.shown).rows.find(r=>r.id===e.target.dataset.row);r.value=e.target.value;store(s);render()});
""",
    "fixtures": [
        {"state": {"user": {"id": "12345", "name": "Sam"},
                   "docs": [{"id": "woXtXUBmiN5T", "name": "Intro to formulas",
                             "rows": [{"id": "s1", "label": "Step 1", "value": "=$Price * 2"},
                                      {"id": "s2", "label": "Step 2", "value": ""}]}],
                   "forks": []},
         "doc": "woXtXUBmiN5T", "edit": ["s2", "=SUM($Price)"]},
        {"state": {"user": {"id": "12345", "name": "Sam"},
                   "docs": [{"id": "kQ3pLrT8vZ2m", "name": "Lookups tutorial",
                             "rows": [{"id": "a", "label": "Answer A", "value": ""},
                                      {"id": "b", "label": "Answer B", "value": ""}]}],
                   "forks": [{"id": "kQ3pLrT8vZ2m~7hGtYe2LmQ~777", "docId": "kQ3pLrT8vZ2m", "forkId": "7hGtYe2LmQ",
                              "userId": "777", "rows": [{"id": "a", "label": "Answer A", "value": "other user"},
                                                        {"id": "b", "label": "Answer B", "value": ""}]},
                             {"id": "kQ3pLrT8vZ2m~1eYN9joCXk~12345", "docId": "kQ3pLrT8vZ2m", "forkId": "1eYN9joCXk",
                              "userId": "12345", "rows": [{"id": "a", "label": "Answer A", "value": "$Name"},
                                                          {"id": "b", "label": "Answer B", "value": "lookupOne"}]}]},
         "doc": "kQ3pLrT8vZ2m", "own": "kQ3pLrT8vZ2m~1eYN9joCXk~12345", "edit": ["b", "lookupOne"]},
    ],
    "journey_js": r"""
  const n=index+1;const base='https://docs.getgrist.com/doc/'+fixture.doc;const uid=fixture.state.user.id;
  const original=Object.fromEntries(fixture.state.docs[0].rows.map(r=>[r.id,r.value]));
  const view=()=>page.locator('#view').evaluate(v=>({shown:v.dataset.shown,doc:v.dataset.doc,user:v.dataset.forkUser,cells:Object.fromEntries([...v.querySelectorAll('input[data-row]')].map(i=>[i.dataset.row,i.dataset.stored]))}));
  if((await view()).shown!=='')throw new InterfaceError('a document is open before navigation');
  async function go(url){await (await one(page,'#address')).fill(url);await (await one(page,'#go')).click();return view()}
  async function close(){await (await one(page,'#close')).click();if((await view()).shown!=='')throw new InterfaceError('close did not close the document')}
  const isOwnFork=v=>v.doc===fixture.doc&&v.user===uid&&v.shown!==fixture.doc;
  if(n===1){
    const first=await go(base);const ok=isOwnFork(first);
    check('first_visit_opens_own_fork_1',ok);
    if(ok){const input=await one(page,`#view input[data-row="${fixture.edit[0]}"]`);await input.fill(fixture.edit[1]);await input.press('Tab')}
    await close();
    const back=await go(base);
    check('returns_to_fork_1',ok&&back.shown===first.shown&&back.cells[fixture.edit[0]]===fixture.edit[1]);
  }else{
    const f=await go('https://docs.getgrist.com/doc/'+fixture.own);
    check('fork_url_opens_fork_2',f.shown===fixture.own);
    await close();
    const back=await go(base);
    check('returns_to_fork_2',back.shown===fixture.own&&back.cells[fixture.edit[0]]===fixture.edit[1]);
  }
  await close();
  const def=await go(base+'/m/default');
  check(`default_mode_original_${n}`,def.shown===fixture.doc&&JSON.stringify(def.cells)===JSON.stringify(original));
""",
    "target": ["returns_to_fork_1", "returns_to_fork_2"],
    "non_target": ["first_visit_opens_own_fork_1", "default_mode_original_1", "fork_url_opens_fork_2",
                   "default_mode_original_2"],
    "controls": {
        "reference": (r"app.onGo(url=>{const m=/\/doc\/([^\/~?#]+)(?:~([^\/~?#]+)~([^\/?#]+))?(\/m\/default)?\/?$/.exec(url.trim());if(!m)return;const [,doc,fork,user,def]=m;"
                      r"if(fork){app.show(doc+'~'+fork+'~'+user);return}if(def){app.show(doc);return}"
                      r"const mine=app.forks().find(f=>f.docId===doc&&f.userId===app.user().id);app.show(mine?mine.id:app.createFork(doc))});", "pass"),
        "alternative": (r"app.onGo(function(url){var path=new URL(url).pathname.replace(/\/+$/,'');var parts=path.split('/');var id=parts[2];if(!id)return;"
                        r"if(path.endsWith('/m/default')){app.show(id.split('~')[0]);return}if(id.indexOf('~')>=0){app.show(id);return}"
                        r"var forks=app.forks().filter(function(f){return f.docId===id&&f.userId===app.user().id});app.show(forks.length?forks[forks.length-1].id:app.createFork(id))});", "pass"),
        "target-mutant": (r"app.onGo(url=>{const m=/\/doc\/([^\/~?#]+)(?:~([^\/~?#]+)~([^\/?#]+))?(\/m\/default)?\/?$/.exec(url.trim());if(!m)return;const [,doc,fork,user,def]=m;"
                          r"if(fork){app.show(doc+'~'+fork+'~'+user);return}if(def){app.show(doc);return}app.show(app.createFork(doc))});", "target_only_failure"),
        "original-on-return-mutant": (r"app.onGo(url=>{const m=/\/doc\/([^\/~?#]+)(?:~([^\/~?#]+)~([^\/?#]+))?(\/m\/default)?\/?$/.exec(url.trim());if(!m)return;const [,doc,fork,user,def]=m;"
                                      r"if(fork){app.show(doc+'~'+fork+'~'+user);return}if(def){app.show(doc);return}"
                                      r"const mine=app.forks().some(f=>f.docId===doc&&f.userId===app.user().id);app.show(mine?doc:app.createFork(doc))});", "target_only_failure"),
        "any-fork-mutant": (r"app.onGo(url=>{const m=/\/doc\/([^\/~?#]+)(?:~([^\/~?#]+)~([^\/?#]+))?(\/m\/default)?\/?$/.exec(url.trim());if(!m)return;const [,doc,fork,user,def]=m;"
                            r"if(fork){app.show(doc+'~'+fork+'~'+user);return}if(def){app.show(doc);return}"
                            r"const any=app.forks().find(f=>f.docId===doc);app.show(any?any.id:app.createFork(doc))});", "target_only_failure"),
        "non-target-mutant": (r"app.onGo(url=>{const m=/\/doc\/([^\/~?#]+)(?:~([^\/~?#]+)~([^\/?#]+))?(\/m\/default)?\/?$/.exec(url.trim());if(!m)return;const [,doc,fork,user]=m;"
                              r"if(fork){app.show(doc+'~'+fork+'~'+user);return}"
                              r"const mine=app.forks().find(f=>f.docId===doc&&f.userId===app.user().id);app.show(mine?mine.id:app.createFork(doc))});", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement the address bar of this tutorial document. When the user clicks Go, open the entered address: "
             "app.show(id) shows the original document (id = <docID>) or a fork (id = <docID>~<forkID>~<userID>); "
             "app.forks() lists the existing forks with their docId and userId, app.user() is the signed-in user, and "
             "app.createFork(docID) creates a fork of the document for the signed-in user and returns its id. Direct "
             "URL: This is the main link to your document. The format is https://<teamsite>.getgrist.com/doc/<docID>. "
             "Default Mode: This link opens the original version of the document, letting the owner edit the tutorial "
             "directly, useful for updating tutorial content. To access default mode, append the Direct URL with "
             "/m/default. The format is https://<teamsite>.getgrist.com/doc/<docID>/m/default. Fork URL: This is a "
             "user's unique copy of the tutorial, automatically created when they open the Direct URL for the first "
             "time. Changes made here won't affect the original. The format is "
             "https://<teamsite>.getgrist.com/doc/<docID>~<forkID>~<userID>. If you close out of your fork of the "
             "document, you can always return to it by visiting the Direct URL; you will be redirected to your fork "
             "automatically.",
        "B": "Clicking Go opens the address typed in the address bar. app.show(id) shows either the original document "
             "(id = <docID>) or a fork (id = <docID>~<forkID>~<userID>); app.forks() returns the existing forks with "
             "their docId and userId, app.user() returns the signed-in user, and app.createFork(docID) makes a new fork "
             "of the document for that user and returns its id. There are three kinds of address. The Direct URL, "
             "https://<teamsite>.getgrist.com/doc/<docID>, is the document's main link; a user who has closed their "
             "fork can always get back to it through the Direct URL, which redirects them to that fork automatically. "
             "Default Mode, the Direct URL followed by /m/default "
             "(https://<teamsite>.getgrist.com/doc/<docID>/m/default), opens the original version so that the owner "
             "can edit the tutorial itself, for example to update its content. The Fork URL, "
             "https://<teamsite>.getgrist.com/doc/<docID>~<forkID>~<userID>, is the user's own copy of the tutorial, "
             "created automatically the first time they open the Direct URL; changes there do not affect the "
             "original.",
        "C": "Implement the address bar of this tutorial document. When the user clicks Go, open the entered address: "
             "app.show(id) shows the original document (id = <docID>) or a fork (id = <docID>~<forkID>~<userID>); "
             "app.forks() lists the existing forks with their docId and userId, app.user() is the signed-in user, and "
             "app.createFork(docID) creates a fork of the document for the signed-in user and returns its id. Direct "
             "URL: This is the main link to your document. The format is https://<teamsite>.getgrist.com/doc/<docID>. "
             "Default Mode: This link opens the original version of the document, letting the owner edit the tutorial "
             "directly, useful for updating tutorial content. To access default mode, append the Direct URL with "
             "/m/default. The format is https://<teamsite>.getgrist.com/doc/<docID>/m/default. Fork URL: This is a "
             "user's unique copy of the tutorial, automatically created when they open the Direct URL for the first "
             "time. Changes made here won't affect the original. The format is "
             "https://<teamsite>.getgrist.com/doc/<docID>~<forkID>~<userID>.",
    },
}

BILLING_MANAGERS = {
    "case": "grist-billing-managers-limit",
    "candidate_id": "rc-f33b2bf870e9",
    "project_id": "grist",
    "source": {"commit": "f896f91781", "file": "help/en/docs/team-sharing.md",
               "snapshot": SNAPSHOT, "snapshot_file": "help/en/docs/team-sharing.md"},
    "title": "Billing Account",
    "register": "app.onAdd",
    "control": "Add billing manager button",
    "body": '<h1>Billing Account</h1><h2>Billing managers</h2><ul id="managers" aria-label="Billing managers"></ul>'
            '<label>Email <input id="email" type="email" size="40"></label><button id="add" type="button">Add billing manager</button>'
            '<p id="message" role="status"></p>',
    "state_js": r"""
let managers=load(window.initialState.managers);
const app=Object.freeze({
  onAdd:register,
  managers(){return structuredClone(managers)},
  addManager(email){if(typeof email!=='string'||!email.trim())throw new Error('email required');managers.push(email.trim());store(managers);render()},
  showMessage(text){document.querySelector('#message').textContent=String(text)}
});
function render(){const list=document.querySelector('#managers');list.replaceChildren();for(const m of managers)list.append(el('li',{'data-email':m},m))}
document.querySelector('#add').addEventListener('click',()=>{if(behavior)behavior(document.querySelector('#email').value)});
""",
    "fixtures": [
        {"state": {"managers": [f"finance{i}@acme.test" for i in range(1, 9)]},
         "allowed": ["cfo@acme.test", "audit@acme.test"], "refused": ["intern@acme.test"]},
        {"state": {"managers": ["ana@team.test", "ben@team.test", "chen@team.test"]},
         "allowed": ["dara@team.test", "eli@team.test", "fay@team.test", "gus@team.test", "hana@team.test",
                     "ivo@team.test", "jun@team.test"],
         "refused": ["kai@team.test", "lea@team.test"]},
    ],
    "journey_js": r"""
  const n=index+1;const list=()=>page.locator('#managers li').evaluateAll(ns=>ns.map(x=>x.dataset.email));
  if(JSON.stringify(await list())!==JSON.stringify(fixture.state.managers))throw new InterfaceError('billing managers missing before adding');
  async function add(email){await (await one(page,'#email')).fill(email);await (await one(page,'#add')).click();await reload(page)}
  for(const email of fixture.allowed)await add(email);
  const expected=[...fixture.state.managers,...fixture.allowed];
  check(`managers_added_${n}`,JSON.stringify(await list())===JSON.stringify(expected));
  for(const email of fixture.refused)await add(email);
  const after=await list();
  check(`no_more_than_ten_${n}`,after.length<=10&&!fixture.refused.some(e=>after.includes(e)));
  check(`existing_managers_kept_${n}`,expected.every(e=>after.includes(e)));
""",
    "target": ["no_more_than_ten_1", "no_more_than_ten_2"],
    "non_target": ["managers_added_1", "managers_added_2", "existing_managers_kept_1", "existing_managers_kept_2"],
    "controls": {
        "reference": ("app.onAdd(email=>{if(app.managers().length>=10){app.showMessage('You can add up to 10 billing managers.');return}app.addManager(email)});", "pass"),
        "alternative": ("app.onAdd(function(e){var m=app.managers();e=e.trim().toLowerCase();if(m.length<10&&m.indexOf(e)<0)app.addManager(e);else app.showMessage('Cannot add billing manager')});", "pass"),
        "target-mutant": ("app.onAdd(email=>app.addManager(email));", "target_only_failure"),
        "off-by-one-mutant": ("app.onAdd(email=>{if(app.managers().length>10)return;app.addManager(email)});", "target_only_failure"),
        "limit-nine-mutant": ("app.onAdd(email=>{if(app.managers().length>=9)return;app.addManager(email)});", "non_target_only_failure"),
        "non-target-mutant": ("app.onAdd(()=>{});", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement adding billing managers on the Billing Account page. When the user enters an email and clicks "
             "Add billing manager, add that person with app.addManager(email); app.managers() lists the current "
             "billing managers. None of the team roles (Viewer, Editor, Owner) provide access to billing information "
             "or management. You can add up to 10 billing managers on the 'Billing Account' page, which can be "
             "accessed via the user menu dropdown.",
        "B": "On the Billing Account page, typing an email and clicking Add billing manager adds that person through "
             "app.addManager(email), and app.managers() returns the current billing managers. Billing information and "
             "management are not available through any of the team roles (Viewer, Editor, Owner). The 'Billing "
             "Account' page, reached from the user menu dropdown, allows at most 10 billing managers to be added.",
        "C": "Implement adding billing managers on the Billing Account page. When the user enters an email and clicks "
             "Add billing manager, add that person with app.addManager(email); app.managers() lists the current "
             "billing managers. None of the team roles (Viewer, Editor, Owner) provide access to billing information "
             "or management. You can add billing managers on the 'Billing Account' page, which can be "
             "accessed via the user menu dropdown.",
    },
}

CASES = [CONTEXT_MENU, PAGE_COLLAPSE, TUTORIAL_RESTART, SUGGESTIONS_COPY, FORK_REDIRECT, BILLING_MANAGERS]
