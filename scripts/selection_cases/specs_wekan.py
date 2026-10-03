"""WeKan selection cases (six selected rules; arm A from the frame-end documentation snapshot)."""

SNAPSHOT = "38415f04caf9a3536fe8faaca0cda9b8aa38cf57"

WEEK_TOGGLE = {
    "case": "wekan-week-number-immediate",
    "candidate_id": "rc-59d96b056593",
    "project_id": "wekan",
    "source": {"commit": "e217f1215a", "file": "docs/Features/Date-Format.md", "snapshot": SNAPSHOT,
               "snapshot_file": "docs/Features/Right-Sidebar/Board-Settings/Date.md"},
    "title": "Board Settings / Date",
    "register": "app.onChange",
    "control": "Date popup controls",
    "body": '<h1>Board Settings / Date</h1><section aria-label="Date"><p id="global"></p>'
            '<label><input id="override" type="checkbox"> Board Date Format</label>'
            '<label>Format <select id="format"><option value="YYYY-MM-DD">year-month-day</option>'
            '<option value="DD-MM-YYYY">day-month-year</option><option value="MM-DD-YYYY">month-day-year</option>'
            '</select></label><button id="save" type="button">Save</button><hr>'
            '<label><input id="show-week" type="checkbox"> Show week of year (ISO 8601)</label></section>'
            '<h2>Due dates</h2><ul id="dates" aria-label="Due dates"></ul>',
    "state_js": r"""
let settings=load(window.initialState.settings);
const global=window.initialState.global;
const NAMES={'YYYY-MM-DD':'year-month-day','DD-MM-YYYY':'day-month-year','MM-DD-YYYY':'month-day-year'};
function isoWeek(s){const d=new Date(s+'T00:00:00Z');d.setUTCDate(d.getUTCDate()-((d.getUTCDay()+6)%7)+3);const first=new Date(Date.UTC(d.getUTCFullYear(),0,4));
  return 1+Math.round(((d-first)/86400000-3+((first.getUTCDay()+6)%7))/7)}
function fmt(s,f){const [y,m,d]=s.split('-');return f.replace('YYYY',y).replace('MM',m).replace('DD',d)}
function effective(){return settings.board.enabled?settings.board.format:global.enabled?global.format:'YYYY-MM-DD'}
const app=Object.freeze({
  onChange:register,
  global(){return structuredClone(global)},
  settings(){return structuredClone(settings)},
  saveBoardDateFormat(v){if(typeof v!=='object'||v===null||typeof v.enabled!=='boolean'||!(v.format in NAMES))throw new Error('enabled and a known format required');
    settings={...settings,board:{enabled:v.enabled,format:v.format}};store(settings);render()},
  setShowWeekOfYear(on){if(typeof on!=='boolean')throw new Error('boolean required');settings={...settings,showWeek:on};store(settings);render()}
});
function render(){
  document.querySelector('#global').textContent='Global Date Format: '+(global.enabled?'Enabled':'Disabled')+' ('+NAMES[global.format]+')';
  const list=document.querySelector('#dates');list.replaceChildren();const f=effective();
  for(const c of window.initialState.cards){const shown=fmt(c.due,f);const w=settings.showWeek?String(isoWeek(c.due)):'';
    list.append(el('li',{'data-id':c.id,'data-date':shown,'data-week':w},c.title+' — due '+shown+(w?' (week '+w+')':'')))}
}
const form=()=>({override:document.querySelector('#override').checked,format:document.querySelector('#format').value,showWeek:document.querySelector('#show-week').checked});
document.querySelector('#override').checked=settings.board.enabled;document.querySelector('#format').value=settings.board.format;
document.querySelector('#show-week').checked=settings.showWeek;
for(const id of ['override','format','show-week'])document.querySelector('#'+id).addEventListener('change',()=>{if(behavior)behavior(id,form())});
document.querySelector('#save').addEventListener('click',()=>{if(behavior)behavior('save',form())});
""",
    "fixtures": [
        {"state": {"global": {"enabled": False, "format": "DD-MM-YYYY"},
                   "settings": {"board": {"enabled": False, "format": "YYYY-MM-DD"}, "showWeek": False},
                   "cards": [{"id": "k1", "title": "Release", "due": "2026-01-01"},
                             {"id": "k2", "title": "Audit", "due": "2026-03-30"},
                             {"id": "k3", "title": "Retro", "due": "2026-12-31"}]},
         "weeks": [1, 14, 53], "initial_format": "YYYY-MM-DD", "override": True, "format": "DD-MM-YYYY",
         "saved_format": "DD-MM-YYYY"},
        {"state": {"global": {"enabled": True, "format": "DD-MM-YYYY"},
                   "settings": {"board": {"enabled": True, "format": "MM-DD-YYYY"}, "showWeek": True},
                   "cards": [{"id": "m1", "title": "Kickoff", "due": "2027-01-01"},
                             {"id": "m2", "title": "Review", "due": "2026-06-15"}]},
         "weeks": [53, 25], "initial_format": "MM-DD-YYYY", "override": False, "format": "MM-DD-YYYY",
         "saved_format": "DD-MM-YYYY"},
    ],
    "journey_js": r"""
  const n=index+1;const cards=fixture.state.cards;
  const read=()=>page.locator('#dates li').evaluateAll(ns=>ns.map(x=>[x.dataset.id,x.dataset.date,x.dataset.week]));
  const f=(s,p)=>{const [y,m,d]=s.split('-');return p.replace('YYYY',y).replace('MM',m).replace('DD',d)};
  const expect=(p,w)=>JSON.stringify(cards.map((c,i)=>[c.id,f(c.due,p),w?String(fixture.weeks[i]):'']));
  const dates=rows=>JSON.stringify(rows.map(r=>r[1]));const initialDates=JSON.stringify(cards.map(c=>f(c.due,fixture.initial_format)));
  const week0=fixture.state.settings.showWeek;
  if(JSON.stringify(await read())!==expect(fixture.initial_format,week0))throw new InterfaceError('dates missing or changed before editing');
  await (await one(page,'#show-week')).setChecked(!week0);
  const before=await read();await reload(page);const kept=await read();
  const weeks=rows=>JSON.stringify(rows.map(r=>[r[0],r[2]]));const wanted=JSON.stringify(cards.map((c,i)=>[c.id,week0?'':String(fixture.weeks[i])]));
  check(`week_toggle_applies_without_save_${n}`,weeks(before)===wanted&&weeks(kept)===wanted);
  check(`toggle_keeps_date_format_${n}`,dates(before)===initialDates&&dates(kept)===initialDates);
  await (await one(page,'#override')).setChecked(fixture.override);
  await (await one(page,'#format')).selectOption(fixture.format);
  await (await one(page,'#save')).click();await reload(page);
  check(`board_format_saved_${n}`,dates(await read())===JSON.stringify(cards.map(c=>f(c.due,fixture.saved_format))));
""",
    "target": ["week_toggle_applies_without_save_1", "week_toggle_applies_without_save_2"],
    "non_target": ["toggle_keeps_date_format_1", "toggle_keeps_date_format_2",
                   "board_format_saved_1", "board_format_saved_2"],
    "controls": {
        "reference": ("app.onChange((control,v)=>{if(control==='show-week')app.setShowWeekOfYear(v.showWeek);else if(control==='save')app.saveBoardDateFormat({enabled:v.override,format:v.format})});", "pass"),
        "alternative": ("document.querySelector('#show-week').addEventListener('change',function(e){app.setShowWeekOfYear(e.target.checked)});app.onChange(function(c,v){if(c==='save')app.saveBoardDateFormat({enabled:v.override,format:v.format})});", "pass"),
        "save-also-week": ("app.onChange((c,v)=>{if(c==='show-week')app.setShowWeekOfYear(v.showWeek);if(c==='save'){app.saveBoardDateFormat({enabled:v.override,format:v.format});app.setShowWeekOfYear(v.showWeek)}});", "pass"),
        "target-mutant": ("app.onChange((c,v)=>{if(c!=='save')return;app.saveBoardDateFormat({enabled:v.override,format:v.format});app.setShowWeekOfYear(v.showWeek)});", "target_only_failure"),
        "non-target-mutant": ("app.onChange((c,v)=>{if(c==='show-week')app.setShowWeekOfYear(v.showWeek)});", "non_target_only_failure"),
        "toggle-saves-format-mutant": ("app.onChange((c,v)=>{if(c==='show-week'){app.setShowWeekOfYear(v.showWeek);app.saveBoardDateFormat({enabled:true,format:'MM-DD-YYYY'})}else if(c==='save')app.saveBoardDateFormat({enabled:v.override,format:v.format})});", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement the Board Settings / Date popup. Every change of a popup control and every click on Save calls "
             "the handler with the control's id and the popup's current values. The top of the popup shows whether "
             "the global Date Format is enabled and its saved value. Check the board override, choose a format, and "
             "Save (app.saveBoardDateFormat({enabled, format})). Unchecking it makes the board inherit the global "
             "setting. Below Save and the horizontal rule, Show week of year (ISO 8601) toggles your own week-number "
             "display (app.setShowWeekOfYear(on)) immediately; it does not set a format for everyone.",
        "B": "In the Board Settings / Date popup, the handler is called with the control's id and the popup's current "
             "values whenever a popup control changes and whenever Save is clicked. The popup starts by showing "
             "whether the global Date Format is enabled, with its saved value. To give the board its own format, "
             "check the board override, pick a format and click Save (app.saveBoardDateFormat({enabled, format})); "
             "with the override unchecked, the board inherits the global setting. Under Save and the horizontal "
             "rule, Show week of year (ISO 8601) switches your own week-number display on or off at once "
             "(app.setShowWeekOfYear(on)), and it does not set a format for anyone else.",
        "C": "Implement the Board Settings / Date popup. Every change of a popup control and every click on Save calls "
             "the handler with the control's id and the popup's current values. The top of the popup shows whether "
             "the global Date Format is enabled and its saved value. Check the board override, choose a format, and "
             "Save (app.saveBoardDateFormat({enabled, format})). Unchecking it makes the board inherit the global "
             "setting. Below Save and the horizontal rule, Show week of year (ISO 8601) toggles your own week-number "
             "display (app.setShowWeekOfYear(on)); it does not set a format for everyone.",
    },
}

SWIMLANE_BELOW = {
    "case": "wekan-swimlane-below-default",
    "candidate_id": "rc-6b29ef8b44d8",
    "project_id": "wekan",
    "source": {"commit": "5ed4268a61", "file": "docs/Features/Swimlanes/Swimlanes.md", "snapshot": SNAPSHOT,
               "snapshot_file": "docs/Features/Swimlanes/Swimlanes.md"},
    "title": "Swimlanes",
    "register": "app.onSave",
    "control": "Save button of the Add Swimlane popup",
    "body": '<h1>Swimlanes</h1><ul id="swimlanes" aria-label="Swimlanes"></ul>'
            '<section id="popup" aria-label="Add Swimlane" hidden><h2>Add Swimlane</h2><p id="anchor"></p>'
            '<label><input id="placement-above" type="radio" name="placement" value="above"> Above selected swimlane</label>'
            '<label><input id="placement-below" type="radio" name="placement" value="below"> Below selected swimlane</label>'
            '<label>Title <textarea id="titles" rows="3"></textarea></label>'
            '<button id="save" type="button">Save</button><p id="message" role="status"></p></section>',
    "state_js": r"""
let lanes=load(window.initialState.swimlanes);
let anchor=null;
const app=Object.freeze({
  onSave:register,
  swimlanes(){return structuredClone(lanes)},
  addSwimlanes(laneId,placement,titles){const i=lanes.findIndex(l=>l.id===laneId);if(i<0)throw new Error('unknown swimlane');
    if(placement!=='above'&&placement!=='below')throw new Error('placement must be above or below');
    if(!Array.isArray(titles)||!titles.length||!titles.every(t=>typeof t==='string'&&t.trim()))throw new Error('nonempty titles required');
    const created=titles.map(t=>({id:'s'+Math.random().toString(36).slice(2,10),title:t.trim()}));
    lanes.splice(placement==='above'?i:i+1,0,...created);store(lanes);render()},
  showMessage(text){document.querySelector('#message').textContent=String(text)}
});
function render(){const list=document.querySelector('#swimlanes');list.replaceChildren();
  for(const l of lanes){const li=el('li',{'data-id':l.id,'data-title':l.title},l.title+' ');
    li.append(el('button',{type:'button',class:'add-lane','data-for':l.id,'aria-label':'Add Swimlane'},'+'));list.append(li)}}
document.querySelector('#swimlanes').addEventListener('click',e=>{const b=e.target.closest('.add-lane');if(!b)return;anchor=b.dataset.for;
  document.querySelector('#anchor').textContent='Selected swimlane: '+lanes.find(l=>l.id===anchor).title;document.querySelector('#popup').hidden=false});
document.querySelector('#save').addEventListener('click',()=>{const checked=document.querySelector('input[name=placement]:checked');
  if(behavior)behavior({laneId:anchor,placement:checked?checked.value:null,text:document.querySelector('#titles').value})});
""",
    "fixtures": [
        {"state": {"swimlanes": [{"id": "l1", "title": "Backlog"}, {"id": "l2", "title": "Doing"},
                                 {"id": "l3", "title": "Done"}]},
         "default_anchor": "l2", "default_titles": ["Review"],
         "explicit_anchor": "l1", "explicit_placement": "above", "explicit_titles": ["Ideas", "Inbox"]},
        {"state": {"swimlanes": [{"id": "t1", "title": "Team A"}, {"id": "t2", "title": "Team B"}]},
         "default_anchor": "t1", "default_titles": ["QA"],
         "explicit_anchor": "t2", "explicit_placement": "below", "explicit_titles": ["Support", "Ops", "Sales"]},
    ],
    "journey_js": r"""
  const n=index+1;const lanes=()=>page.locator('#swimlanes li').evaluateAll(ns=>ns.map(x=>x.dataset.title));
  const initial=fixture.state.swimlanes.map(l=>l.title);const title=id=>fixture.state.swimlanes.find(l=>l.id===id).title;
  const insert=(list,at,placement,titles)=>{const i=list.indexOf(at);const out=[...list];out.splice(placement==='above'?i:i+1,0,...titles);return JSON.stringify(out)};
  if(JSON.stringify(await lanes())!==JSON.stringify(initial))throw new InterfaceError('swimlanes missing or changed');
  await (await one(page,`.add-lane[data-for="${fixture.default_anchor}"]`)).click();
  await (await one(page,'#titles')).fill(fixture.default_titles.join('\n'));
  await (await one(page,'#save')).click();await reload(page);
  const a=await lanes();
  check(`untouched_popup_inserts_below_${n}`,JSON.stringify(a)===insert(initial,title(fixture.default_anchor),'below',fixture.default_titles));
  await (await one(page,`.add-lane[data-for="${fixture.explicit_anchor}"]`)).click();
  await (await one(page,`#placement-${fixture.explicit_placement}`)).check();
  await (await one(page,'#titles')).fill(fixture.explicit_titles.join('\n'));
  await (await one(page,'#save')).click();await reload(page);
  const b=await lanes();
  check(`chosen_placement_keeps_order_${n}`,JSON.stringify(b)===insert(a,title(fixture.explicit_anchor),fixture.explicit_placement,fixture.explicit_titles));
  check(`existing_lanes_kept_${n}`,JSON.stringify(b.filter(t=>initial.includes(t)))===JSON.stringify(initial));
""",
    "target": ["untouched_popup_inserts_below_1", "untouched_popup_inserts_below_2"],
    "non_target": ["chosen_placement_keeps_order_1", "chosen_placement_keeps_order_2",
                   "existing_lanes_kept_1", "existing_lanes_kept_2"],
    "controls": {
        "reference": ("app.onSave(f=>{const titles=f.text.split('\\n').map(t=>t.trim()).filter(Boolean);if(!titles.length)return;app.addSwimlanes(f.laneId,f.placement||'below',titles)});", "pass"),
        "preselect-below": ("document.querySelector('#placement-below').checked=true;app.onSave(function(f){var t=f.text.split(/\\r?\\n/).filter(function(x){return x.trim()!==''});if(f.placement&&t.length)app.addSwimlanes(f.laneId,f.placement,t)});", "pass"),
        "target-mutant": ("app.onSave(f=>{if(!f.placement){app.showMessage('Choose above or below.');return}app.addSwimlanes(f.laneId,f.placement,f.text.split('\\n').filter(t=>t.trim()))});", "target_only_failure"),
        "above-default-mutant": ("app.onSave(f=>app.addSwimlanes(f.laneId,f.placement||'above',f.text.split('\\n').filter(t=>t.trim())));", "target_only_failure"),
        "non-target-mutant": ("app.onSave(f=>app.addSwimlanes(f.laneId,'below',f.text.split('\\n').filter(t=>t.trim())));", "non_target_only_failure"),
        "reversed-titles-mutant": ("app.onSave(f=>app.addSwimlanes(f.laneId,f.placement||'below',f.text.split('\\n').filter(t=>t.trim()).reverse()));", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement adding swimlanes. Use + beside a swimlane header to open Add Swimlane; when the user clicks "
             "Save, the handler receives the selected swimlane's id, the checked placement ('above', 'below' or null) "
             "and the entered text. Create one swimlane per nonempty line with app.addSwimlanes(laneId, placement, "
             "titles). The existing popup offers Above selected swimlane and Below selected swimlane, with Below "
             "selected by default. Multiple titles retain their order between the selected lane and its neighbor.",
        "B": "The + beside a swimlane header opens Add Swimlane, and clicking Save passes the handler the selected "
             "swimlane's id, the checked placement ('above', 'below' or null) and the typed text. Every nonempty line "
             "becomes one swimlane, created through app.addSwimlanes(laneId, placement, titles). The popup lets the "
             "user pick Above selected swimlane or Below selected swimlane, and Below is the preselected choice. "
             "When several titles are entered, they keep their order between the selected lane and the neighboring one.",
        "C": "Implement adding swimlanes. Use + beside a swimlane header to open Add Swimlane; when the user clicks "
             "Save, the handler receives the selected swimlane's id, the checked placement ('above', 'below' or null) "
             "and the entered text. Create one swimlane per nonempty line with app.addSwimlanes(laneId, placement, "
             "titles). The existing popup offers Above selected swimlane and Below selected swimlane. Multiple titles "
             "retain their order between the selected lane and its neighbor.",
    },
}

HOME_DROP = {
    "case": "wekan-home-multi-drop",
    "candidate_id": "rc-88440629ecb6",
    "project_id": "wekan",
    "source": {"commit": "aebc7d9def", "file": "docs/Features/Board/Home.md", "snapshot": SNAPSHOT,
               "snapshot_file": "docs/Features/Board/Home.md"},
    "title": "All Boards",
    "register": "app.onDrop",
    "control": "Drop on Home button",
    "body": '<h1>All Boards</h1><p id="home-row"></p><button id="drop-home" type="button">Drop on Home</button>'
            '<p id="message" role="status"></p><ul id="boards" aria-label="Boards"></ul>',
    "state_js": r"""
let home=load(window.initialState.home);
let selected=[];
const boards=window.initialState.boards;
const app=Object.freeze({
  onDrop:register,
  boards(){return structuredClone(boards)},
  home(){return home},
  selection(){return [...selected]},
  setHome(id){if(id!==null&&!boards.some(b=>b.id===id))throw new Error('unknown board');home=id;store(home);render()},
  clearSelection(){selected=[];render()},
  showMessage(text){document.querySelector('#message').textContent=String(text)}
});
function render(){const h=boards.find(b=>b.id===home);const row=document.querySelector('#home-row');
  row.dataset.home=h?h.id:'';row.textContent='Home ('+(h?1:0)+')'+(h?': '+h.title:'');
  const list=document.querySelector('#boards');list.replaceChildren();
  for(const b of boards){const on=selected.includes(b.id);const li=el('li',{'data-id':b.id,'data-selected':on});
    const box=el('input',{type:'checkbox',class:'select','aria-label':'Select '+b.title});box.checked=on;
    li.append(box,document.createTextNode(' '+b.title));list.append(li)}}
document.querySelector('#boards').addEventListener('change',e=>{if(!e.target.matches('input.select'))return;const id=e.target.closest('li').dataset.id;
  selected=e.target.checked?[...selected.filter(x=>x!==id),id]:selected.filter(x=>x!==id);render()});
document.querySelector('#drop-home').addEventListener('click',()=>{if(behavior)behavior([...selected])});
""",
    "fixtures": [
        {"state": {"home": None, "boards": [{"id": "d1", "title": "Sprint"}, {"id": "d2", "title": "Roadmap"},
                                            {"id": "d3", "title": "Ops"}, {"id": "d4", "title": "Personal"}]},
         "multi": ["d1", "d3"], "single": "d1"},
        {"state": {"home": "e2", "boards": [{"id": "e1", "title": "Marketing"}, {"id": "e2", "title": "Support"},
                                            {"id": "e3", "title": "Hiring"}, {"id": "e4", "title": "Budget"}]},
         "multi": ["e1", "e3", "e4"], "single": "e3"},
    ],
    "journey_js": r"""
  const n=index+1;const initialHome=fixture.state.home??'';
  const homeNow=()=>page.locator('#home-row').evaluate(x=>x.dataset.home);
  const selectedNow=async()=>(await page.locator('#boards li').evaluateAll(ns=>ns.filter(x=>x.dataset.selected==='true').map(x=>x.dataset.id))).sort();
  const select=async ids=>{for(const b of fixture.state.boards)await (await one(page,`#boards li[data-id="${b.id}"] input.select`)).setChecked(ids.includes(b.id))};
  if(await homeNow()!==initialHome||(await selectedNow()).length!==0)throw new InterfaceError('home or selection changed before the drop');
  await select(fixture.multi);
  if(JSON.stringify(await selectedNow())!==JSON.stringify([...fixture.multi].sort()))throw new InterfaceError('boards could not be selected');
  await (await one(page,'#drop-home')).click();
  const home1=await homeNow();const sel1=await selectedNow();const msg=((await page.locator('#message').textContent())||'').toLowerCase();
  await reload(page);const home1r=await homeNow();
  check(`multi_drop_changes_nothing_${n}`,home1===initialHome&&home1r===initialHome);
  check(`multi_drop_reports_${n}`,msg.includes('please select only one board'));
  check(`multi_drop_keeps_selection_${n}`,JSON.stringify(sel1)===JSON.stringify([...fixture.multi].sort()));
  await select([fixture.single]);await (await one(page,'#drop-home')).click();await reload(page);
  const home2=await homeNow();
  await select([fixture.single]);await (await one(page,'#drop-home')).click();await reload(page);
  check(`single_drop_sets_home_${n}`,home2===fixture.single&&await homeNow()===fixture.single);
""",
    "target": ["multi_drop_changes_nothing_1", "multi_drop_changes_nothing_2", "multi_drop_reports_1",
               "multi_drop_reports_2", "multi_drop_keeps_selection_1", "multi_drop_keeps_selection_2"],
    "non_target": ["single_drop_sets_home_1", "single_drop_sets_home_2"],
    "controls": {
        "reference": ("app.onDrop(ids=>{if(ids.length>1){app.showMessage('Please select only one board');return}if(ids.length===1)app.setHome(ids[0])});", "pass"),
        "alternative": ("app.onDrop(function(ids){if(ids.length!==1){if(ids.length)app.showMessage('Please select only one board.');return}app.setHome(ids[0]);app.clearSelection()});", "pass"),
        "target-mutant": ("app.onDrop(ids=>{if(!ids.length)return;app.setHome(ids[0]);app.clearSelection()});", "target_only_failure"),
        "first-keeps-selection-mutant": ("app.onDrop(ids=>{if(ids.length)app.setHome(ids[0])});", "target_only_failure"),
        "silent-reject-mutant": ("app.onDrop(ids=>{if(ids.length===1)app.setHome(ids[0])});", "target_only_failure"),
        "non-target-mutant": ("app.onDrop(ids=>{if(ids.length>1)app.showMessage('Please select only one board')});", "non_target_only_failure"),
        "toggle-mutant": ("app.onDrop(ids=>{if(ids.length>1){app.showMessage('Please select only one board');return}if(ids.length===1)app.setHome(app.home()===ids[0]?null:ids[0])});", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement dropping boards on the Home row of All Boards. Ticking a board's checkbox adds it to the "
             "multi-selection; Drop on Home drops the selected boards on the Home row and calls the handler with their "
             "ids. Set Home with app.setHome(id); app.home(), app.selection(), app.clearSelection() and "
             "app.showMessage(text) are also available. Drop a board on the Home row and it becomes the board that "
             "opens after login. A drop replaces. Home holds one board, so dropping a board on it makes that board "
             "Home whatever was there before. It deliberately does not toggle. Dropping a multi-selection does not "
             "silently choose its first board. It reports \"Please select only one board\", changes nothing and keeps "
             "the selection so it can be narrowed. A one-board drag continues to set Home normally.",
        "B": "On All Boards, ticking a board's checkbox puts it in the multi-selection, and Drop on Home drops the "
             "selected boards onto the Home row, passing their ids to the handler. app.setHome(id) sets Home, and "
             "app.home(), app.selection(), app.clearSelection() and app.showMessage(text) can be used too. A board "
             "dropped on the Home row becomes the one that opens after login. Because Home holds a single board, a "
             "drop replaces whichever board was Home before, and it never toggles. A dropped multi-selection does not "
             "quietly pick its first board: it shows \"Please select only one board\", leaves everything unchanged "
             "and keeps the selection so the user can narrow it. Dropping a single board still sets Home as usual.",
        "C": "Implement dropping boards on the Home row of All Boards. Ticking a board's checkbox adds it to the "
             "multi-selection; Drop on Home drops the selected boards on the Home row and calls the handler with their "
             "ids. Set Home with app.setHome(id); app.home(), app.selection(), app.clearSelection() and "
             "app.showMessage(text) are also available. Drop a board on the Home row and it becomes the board that "
             "opens after login. A drop replaces. Home holds one board, so dropping a board on it makes that board "
             "Home whatever was there before. It deliberately does not toggle. A one-board drag continues to set Home "
             "normally.",
    },
}

FIELD_ORDER = {
    "case": "wekan-field-order-independent",
    "candidate_id": "rc-899c4d2472ad",
    "project_id": "wekan",
    "source": {"commit": "15b2b6c533", "file": "docs/Features/Board/Card-Field-Display-Order.md",
               "snapshot": SNAPSHOT, "snapshot_file": "docs/Features/Right-Sidebar/Board-Settings/Card.md",
               "duplicate_of": ["rc-90d29a54a512"]},
    "title": "Board Settings / Card",
    "register": "app.onMove",
    "control": "arrow buttons",
    "body": '<h1>Board Settings / Card</h1><h2>Card field order</h2>'
            '<section aria-label="Show on Minicard"><h3>Show on Minicard</h3><ul id="minicard-list"></ul></section>'
            '<section aria-label="Show on Card"><h3>Show on Card</h3><ul id="card-list"></ul></section>'
            '<h2>Preview</h2><p>Minicard: <span id="minicard-preview"></span></p>'
            '<p>Opened card: <span id="card-preview"></span></p>',
    "state_js": r"""
let orders=load(window.initialState.orders);
const NAMES={dates:'Dates',cover:'Cover image',labels:'Labels',customFields:'Custom Fields',members:'Members',description:'Description'};
const app=Object.freeze({
  onMove:register,
  orders(){return structuredClone(orders)},
  saveOrders(next){const same=(a,b)=>Array.isArray(a)&&a.length===b.length&&[...a].sort().join()===[...b].sort().join();
    if(typeof next!=='object'||next===null||!same(next.minicard,orders.minicard)||!same(next.card,orders.card))throw new Error('both orders must list the same fields');
    orders={minicard:[...next.minicard],card:[...next.card]};store(orders);render()}
});
function render(){
  for(const side of ['minicard','card']){const list=document.querySelector('#'+side+'-list');list.replaceChildren();
    for(const key of orders[side]){const li=el('li',{'data-key':key});
      li.append(el('button',{type:'button',class:'up','aria-label':'Move '+NAMES[key]+' up'},'▲'),el('button',{type:'button',class:'down','aria-label':'Move '+NAMES[key]+' down'},'▼'),document.createTextNode(' '+NAMES[key]));list.append(li)}
    const preview=document.querySelector('#'+side+'-preview');preview.replaceChildren();
    for(const key of orders[side])preview.append(el('span',{class:'field','data-key':key},NAMES[key]+' · '))}
}
for(const side of ['minicard','card'])document.querySelector('#'+side+'-list').addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;
  if(behavior)behavior({side,key:b.closest('li').dataset.key,direction:b.classList.contains('up')?'up':'down'})});
""",
    "fixtures": [
        {"state": {"orders": {"minicard": ["dates", "cover", "labels", "customFields", "members", "description"],
                              "card": ["labels", "dates", "members", "customFields", "description"]}},
         "minicard_moves": [["members", "up"], ["members", "up"]], "card_moves": [["labels", "down"]]},
        {"state": {"orders": {"minicard": ["cover", "labels", "dates", "members", "customFields", "description"],
                              "card": ["description", "customFields", "members", "dates", "labels"]}},
         "minicard_moves": [["dates", "down"]], "card_moves": [["labels", "up"], ["labels", "up"]]},
    ],
    "journey_js": r"""
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
""",
    "target": ["card_unchanged_by_minicard_move_1", "card_unchanged_by_minicard_move_2",
               "minicard_unchanged_by_card_move_1", "minicard_unchanged_by_card_move_2"],
    "non_target": ["minicard_move_applied_1", "minicard_move_applied_2", "card_move_applied_1", "card_move_applied_2"],
    "controls": {
        "reference": ("app.onMove(m=>{const o=app.orders();const list=o[m.side];const i=list.indexOf(m.key);const j=m.direction==='up'?i-1:i+1;if(i<0||j<0||j>=list.length)return;[list[i],list[j]]=[list[j],list[i]];app.saveOrders(o)});", "pass"),
        "alternative": ("app.onMove(function(m){var o=app.orders(),l=o[m.side],i=l.indexOf(m.key),j=i+(m.direction==='up'?-1:1);if(j<0||j>=l.length)return;l.splice(i,1);l.splice(j,0,m.key);app.saveOrders({minicard:o.minicard,card:o.card})});", "pass"),
        "target-mutant": ("app.onMove(m=>{const o=app.orders();for(const side of ['minicard','card']){const l=o[side];const i=l.indexOf(m.key);const j=m.direction==='up'?i-1:i+1;if(i>=0&&j>=0&&j<l.length)[l[i],l[j]]=[l[j],l[i]]}app.saveOrders(o)});", "target_only_failure"),
        "mirror-mutant": ("app.onMove(m=>{const o=app.orders();const l=o[m.side];const i=l.indexOf(m.key);const j=m.direction==='up'?i-1:i+1;if(i<0||j<0||j>=l.length)return;[l[i],l[j]]=[l[j],l[i]];const other=m.side==='card'?'minicard':'card';const common=l.filter(k=>o[other].includes(k));let c=0;o[other]=o[other].map(k=>l.includes(k)?common[c++]:k);app.saveOrders(o)});", "target_only_failure"),
        "non-target-mutant": ("app.onMove(()=>{});", "non_target_only_failure"),
        "reversed-direction-mutant": ("app.onMove(m=>{const o=app.orders();const l=o[m.side];const i=l.indexOf(m.key);const j=m.direction==='up'?i+1:i-1;if(i<0||j<0||j>=l.length)return;[l[i],l[j]]=[l[j],l[i]];app.saveOrders(o)});", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement the arrows of Board Settings / Card, where you choose in what order the opened card and the "
             "minicard show their fields. Clicking ▲ or ▼ beside a field calls the handler with the list's side "
             "('minicard' or 'card'), the field key and the direction ('up' or 'down'); read the orders with "
             "app.orders() and store new ones with app.saveOrders({minicard, card}). The Show on Minicard list is in "
             "the board's minicard order and the Show on Card list in its card order. ▲ ▼ move the field earlier or "
             "later on that side only. They are independent: a field can be third on the minicard and last on the "
             "card. What either list shows top to bottom is what that surface draws top to bottom. The change takes "
             "effect immediately on every card of this board; there is no separate save step.",
        "B": "Board Settings / Card is where you choose the order in which the opened card and the minicard show "
             "their fields; implement its arrows. A click on ▲ or ▼ next to a field calls the handler with the "
             "list's side ('minicard' or 'card'), the field key and the direction ('up' or 'down'); app.orders() "
             "gives the current orders and app.saveOrders({minicard, card}) stores new ones. Show on Minicard lists "
             "the fields in the board's minicard order, Show on Card in its card order, and the top-to-bottom order "
             "of each list is the order its surface draws. An arrow moves the field one place earlier or later in its "
             "own list only, since the two orders are independent of each other: a field may be third on the minicard "
             "and last on the card. Changes apply at once to every card of the board, with no separate save step.",
        "C": "Implement the arrows of Board Settings / Card, where you choose in what order the opened card and the "
             "minicard show their fields. Clicking ▲ or ▼ beside a field calls the handler with the list's side "
             "('minicard' or 'card'), the field key and the direction ('up' or 'down'); read the orders with "
             "app.orders() and store new ones with app.saveOrders({minicard, card}). The Show on Minicard list is in "
             "the board's minicard order and the Show on Card list in its card order. ▲ ▼ move the field earlier or "
             "later. What either list shows top to bottom is what that surface draws top to bottom. The change takes "
             "effect immediately on every card of this board; there is no separate save step.",
    },
}

MEMBER_RESTRICTION = {
    "case": "wekan-member-same-org-team",
    "candidate_id": "rc-8b05adc7767e",
    "project_id": "wekan",
    "source": {"commit": "f0ea1601b3", "file": "docs/Features/Members/Members.md", "snapshot": SNAPSHOT,
               "snapshot_file": "docs/Features/Members/Members.md"},
    "title": "Board members",
    "register": "app.onAdd",
    "control": "Add button",
    "body": '<h1>Board members</h1><p id="actor"></p><p id="settings"></p><ul id="members" aria-label="Members"></ul>'
            '<label>Add member <select id="user"></select></label><button id="add" type="button">Add</button>'
            '<p id="message" role="status"></p>',
    "state_js": r"""
let members=load(window.initialState.members);
const users=window.initialState.users;const actor=window.initialState.actor;const settings=window.initialState.settings;
const app=Object.freeze({
  onAdd:register,
  actor(){return structuredClone(actor)},
  settings(){return structuredClone(settings)},
  users(){return structuredClone(users)},
  members(){return structuredClone(members)},
  addMember(userId){if(!users.some(u=>u.id===userId))throw new Error('unknown user');members.push({userId,isActive:true});store(members);render()},
  showMessage(text){document.querySelector('#message').textContent=String(text)}
});
const name=id=>users.find(u=>u.id===id).username;
function render(){
  document.querySelector('#actor').textContent='Signed in as '+name(actor.id)+(actor.isAdmin?' (site admin)':'');
  document.querySelector('#settings').textContent='Admin Panel: boardMembersFromSameOrgOnly '+(settings.boardMembersFromSameOrgOnly?'on':'off')+', boardMembersFromSameTeamOnly '+(settings.boardMembersFromSameTeamOnly?'on':'off');
  const list=document.querySelector('#members');list.replaceChildren();
  for(const m of members)list.append(el('li',{'data-user':m.userId,'data-active':m.isActive},name(m.userId)+(m.isActive?'':' (inactive)')));
  const select=document.querySelector('#user');select.replaceChildren();
  for(const u of users)if(!members.some(m=>m.userId===u.id))select.append(el('option',{value:u.id},u.username))}
document.querySelector('#add').addEventListener('click',()=>{if(behavior)behavior(document.querySelector('#user').value)});
""",
    "fixtures": [
        {"state": {"actor": {"id": "u0", "isAdmin": False},
                   "settings": {"boardMembersFromSameOrgOnly": True, "boardMembersFromSameTeamOnly": False},
                   "users": [{"id": "u0", "username": "maria", "orgs": ["acme"], "teams": ["design"]},
                             {"id": "u5", "username": "lee", "orgs": ["globex"], "teams": []},
                             {"id": "u6", "username": "kim", "orgs": ["initech"], "teams": []},
                             {"id": "u1", "username": "ana", "orgs": ["acme"], "teams": []},
                             {"id": "u2", "username": "ben", "orgs": [], "teams": ["design"]},
                             {"id": "u3", "username": "cai", "orgs": ["globex"], "teams": []},
                             {"id": "u4", "username": "dev", "orgs": ["initech"], "teams": []},
                             {"id": "u7", "username": "eve", "orgs": ["umbrella"], "teams": ["sales"]}],
                   "members": [{"userId": "u0", "isActive": True}, {"userId": "u5", "isActive": True},
                               {"userId": "u6", "isActive": False}]},
         "inviter_share": ["u1"], "member_share": ["u3"], "blocked": ["u2", "u4", "u7"]},
        {"state": {"actor": {"id": "v0", "isAdmin": False},
                   "settings": {"boardMembersFromSameOrgOnly": False, "boardMembersFromSameTeamOnly": True},
                   "users": [{"id": "v0", "username": "jon", "orgs": ["north"], "teams": ["ops"]},
                             {"id": "v5", "username": "ivy", "orgs": [], "teams": ["qa"]},
                             {"id": "v6", "username": "rob", "orgs": ["south"], "teams": ["sales"]},
                             {"id": "v1", "username": "zoe", "orgs": [], "teams": ["ops"]},
                             {"id": "v2", "username": "tom", "orgs": ["east"], "teams": ["qa"]},
                             {"id": "v3", "username": "liz", "orgs": ["north"], "teams": []},
                             {"id": "v4", "username": "sam", "orgs": [], "teams": ["sales"]}],
                   "members": [{"userId": "v0", "isActive": True}, {"userId": "v5", "isActive": True},
                               {"userId": "v6", "isActive": False}]},
         "inviter_share": ["v1"], "member_share": ["v2"], "blocked": ["v3", "v4"]},
    ],
    "journey_js": r"""
  const n=index+1;const initial=fixture.state.members.map(m=>m.userId);
  const read=()=>page.locator('#members li').evaluateAll(ns=>ns.map(x=>x.dataset.user));
  const attempts=[...fixture.blocked,...fixture.member_share,...fixture.inviter_share];
  if(JSON.stringify(await read())!==JSON.stringify(initial))throw new InterfaceError('members missing before adding');
  await one(page,'#user');
  for(const id of attempts){await reload(page);const select=await one(page,'#user');
    if(!(await select.locator('option').evaluateAll(ns=>ns.map(x=>x.value))).includes(id))continue;
    await select.selectOption(id);await (await one(page,'#add')).click()}
  await reload(page);const after=await read();const count=id=>after.filter(x=>x===id).length;
  check(`unshared_users_blocked_${n}`,fixture.blocked.every(id=>count(id)===0));
  check(`active_member_share_added_${n}`,fixture.member_share.every(id=>count(id)>=1));
  check(`inviter_share_added_${n}`,fixture.inviter_share.every(id=>count(id)>=1));
  check(`members_list_intact_${n}`,JSON.stringify(after.slice(0,initial.length))===JSON.stringify(initial)&&new Set(after).size===after.length);
""",
    "target": ["unshared_users_blocked_1", "unshared_users_blocked_2",
               "active_member_share_added_1", "active_member_share_added_2"],
    "non_target": ["inviter_share_added_1", "inviter_share_added_2", "members_list_intact_1", "members_list_intact_2"],
    "controls": {
        "filtered-users": ("app.onAdd(id=>{const s=app.settings();const users=app.users();const u=users.find(x=>x.id===id);if(!u)return;const kinds=[s.boardMembersFromSameOrgOnly&&'orgs',s.boardMembersFromSameTeamOnly&&'teams'].filter(Boolean);const actor=app.actor();if(!actor.isAdmin&&kinds.length){const peers=[actor.id,...app.members().filter(m=>m.isActive).map(m=>m.userId)].map(p=>users.find(x=>x.id===p)).filter(Boolean);if(!peers.some(p=>kinds.some(k=>p[k].some(g=>u[k].includes(g))))){app.showMessage('This user does not share an Organization or Team with the board.');return}}app.addMember(id)});const ss=app.settings(),uu=app.users(),aa=app.actor();const peers=[aa.id,...app.members().filter(m=>m.isActive).map(m=>m.userId)].map(id=>uu.find(u=>u.id===id));for(const o of document.querySelectorAll('#user option')){const u=uu.find(u=>u.id===o.value);if(u&&!aa.isAdmin&&(ss.boardMembersFromSameOrgOnly||ss.boardMembersFromSameTeamOnly)&&!peers.some(p=>(ss.boardMembersFromSameOrgOnly&&p.orgs.some(v=>u.orgs.includes(v)))||(ss.boardMembersFromSameTeamOnly&&p.teams.some(v=>u.teams.includes(v)))))o.remove()}", "pass"),
        "reference": ("app.onAdd(id=>{const s=app.settings();const users=app.users();const u=users.find(x=>x.id===id);if(!u)return;const kinds=[s.boardMembersFromSameOrgOnly&&'orgs',s.boardMembersFromSameTeamOnly&&'teams'].filter(Boolean);const actor=app.actor();if(!actor.isAdmin&&kinds.length){const peers=[actor.id,...app.members().filter(m=>m.isActive).map(m=>m.userId)].map(p=>users.find(x=>x.id===p)).filter(Boolean);if(!peers.some(p=>kinds.some(k=>p[k].some(g=>u[k].includes(g))))){app.showMessage('This user does not share an Organization or Team with the board.');return}}app.addMember(id)});", "pass"),
        "alternative": ("app.onAdd(function(id){var s=app.settings(),all=app.users(),me=app.actor();function get(x){return all.filter(function(u){return u.id===x})[0]}var u=get(id);if(!u)return;var ok=me.isAdmin||(!s.boardMembersFromSameOrgOnly&&!s.boardMembersFromSameTeamOnly);app.members().forEach(function(m){if(!m.isActive)return;var p=get(m.userId);if(s.boardMembersFromSameOrgOnly&&p.orgs.some(function(o){return u.orgs.indexOf(o)>=0}))ok=true;if(s.boardMembersFromSameTeamOnly&&p.teams.some(function(t){return u.teams.indexOf(t)>=0}))ok=true});if(ok)app.addMember(id);else app.showMessage('Not allowed')});", "pass"),
        "target-mutant": ("app.onAdd(id=>{if(id)app.addMember(id)});", "target_only_failure"),
        "any-kind-mutant": ("app.onAdd(id=>{const users=app.users();const u=users.find(x=>x.id===id);const peers=[app.actor().id,...app.members().filter(m=>m.isActive).map(m=>m.userId)].map(p=>users.find(x=>x.id===p));if(peers.some(p=>p.orgs.some(g=>u.orgs.includes(g))||p.teams.some(g=>u.teams.includes(g))))app.addMember(id)});", "target_only_failure"),
        "inviter-only-mutant": ("app.onAdd(id=>{const s=app.settings();const users=app.users();const u=users.find(x=>x.id===id);const me=users.find(x=>x.id===app.actor().id);const ok=(s.boardMembersFromSameOrgOnly&&me.orgs.some(g=>u.orgs.includes(g)))||(s.boardMembersFromSameTeamOnly&&me.teams.some(g=>u.teams.includes(g)));if(ok)app.addMember(id)});", "target_only_failure"),
        "inactive-counted-mutant": ("app.onAdd(id=>{const s=app.settings();const users=app.users();const u=users.find(x=>x.id===id);const peers=[app.actor().id,...app.members().map(m=>m.userId)].map(p=>users.find(x=>x.id===p));const ok=peers.some(p=>(s.boardMembersFromSameOrgOnly&&p.orgs.some(g=>u.orgs.includes(g)))||(s.boardMembersFromSameTeamOnly&&p.teams.some(g=>u.teams.includes(g))));if(ok)app.addMember(id)});", "target_only_failure"),
        "non-target-mutant": ("app.onAdd(id=>{const s=app.settings();const users=app.users();const u=users.find(x=>x.id===id);const me=app.actor().id;const peers=app.members().filter(m=>m.isActive&&m.userId!==me).map(m=>users.find(x=>x.id===m.userId));const ok=peers.some(p=>(s.boardMembersFromSameOrgOnly&&p.orgs.some(g=>u.orgs.includes(g)))||(s.boardMembersFromSameTeamOnly&&p.teams.some(g=>u.teams.includes(g))));if(ok)app.addMember(id)});", "non_target_only_failure"),
        "duplicate-mutant": ("app.onAdd(id=>{const s=app.settings();const users=app.users();const u=users.find(x=>x.id===id);const peers=[app.actor().id,...app.members().filter(m=>m.isActive).map(m=>m.userId)].map(p=>users.find(x=>x.id===p));const ok=peers.some(p=>(s.boardMembersFromSameOrgOnly&&p.orgs.some(g=>u.orgs.includes(g)))||(s.boardMembersFromSameTeamOnly&&p.teams.some(g=>u.teams.includes(g))));if(ok){app.addMember(id);app.addMember(id)}});", "non_target_only_failure"),
        "never-add-mutant": ("app.onAdd(()=>app.showMessage('Not allowed'));", "mixed_failure"),
    },
    "arms": {
        "A": "Implement adding a member from the board members sidebar. When the user picks a user and clicks Add, "
             "add them with app.addMember(userId). The signed-in inviter is app.actor(), the board's members and "
             "whether each is active are app.members(), every user's Organizations and Teams are in app.users(), and "
             "the admin settings are app.settings(). On multi-tenant instances you can require that a board's members "
             "share an Organization or a Team. There is one admin checkbox per kind (boardMembersFromSameOrgOnly in "
             "Admin Panel / People / Organizations and boardMembersFromSameTeamOnly in Admin Panel / People / Teams), "
             "and when either is on, a user can only be added to a board if they share an enabled kind with the "
             "inviter or with an active board member (site admins bypass this).",
        "B": "In the board members sidebar, picking a user and clicking Add adds them through app.addMember(userId). "
             "app.actor() is the signed-in inviter, app.members() lists the board's members with whether each is "
             "active, app.users() gives each user's Organizations and Teams, and app.settings() holds the admin "
             "settings. Multi-tenant instances can demand that board members share an Organization or a Team, with "
             "a separate admin checkbox for each kind: boardMembersFromSameOrgOnly under Admin Panel / People / "
             "Organizations and boardMembersFromSameTeamOnly under Admin Panel / People / Teams. While either one is "
             "checked, a user may join a board only if they have an enabled kind in common with the inviter or with "
             "an active board member; site admins are exempt.",
        "C": "Implement adding a member from the board members sidebar. When the user picks a user and clicks Add, "
             "add them with app.addMember(userId). The signed-in inviter is app.actor(), the board's members and "
             "whether each is active are app.members(), every user's Organizations and Teams are in app.users(), and "
             "the admin settings are app.settings(). On multi-tenant instances you can require that a board's members "
             "share an Organization or a Team. There is one admin checkbox per kind (boardMembersFromSameOrgOnly in "
             "Admin Panel / People / Organizations and boardMembersFromSameTeamOnly in Admin Panel / People / Teams).",
    },
}

SYNC_TEXT = {
    "case": "wekan-sync-local-edits",
    "candidate_id": "rc-f3df2f6e5885",
    "project_id": "wekan",
    "source": {"commit": "b254b7d3af", "file": "docs/Features/ImportExport/Sync.md", "snapshot": SNAPSHOT,
               "snapshot_file": "docs/Features/ImportExport/Sync.md"},
    "title": "Synced list",
    "register": "app.onSync",
    "control": "Sync now button",
    "body": '<h1>Synced list</h1><p id="source"></p><button id="sync" type="button">Sync now</button>'
            '<p id="message" role="status"></p><ul id="cards" aria-label="Cards"></ul>',
    "state_js": r"""
let cards=load(window.initialState.cards);
const TEXT=['title','description','sourceTitle','sourceDescription'];
const app=Object.freeze({
  onSync:register,
  cards(){return structuredClone(cards)},
  createCard(item){if(typeof item!=='object'||item===null||typeof item.externalId!=='string'||typeof item.title!=='string'||typeof item.description!=='string')throw new Error('externalId, title and description required');
    if(cards.some(c=>c.externalId===item.externalId))throw new Error('card for this item exists');
    cards.push({id:'c'+(cards.length+1),externalId:item.externalId,title:item.title,description:item.description,sourceTitle:item.title,sourceDescription:item.description,archived:false});store(cards);render()},
  updateCard(id,changes){const c=cards.find(x=>x.id===id);if(!c)throw new Error('unknown card');
    if(typeof changes!=='object'||changes===null||!Object.entries(changes).every(([k,v])=>TEXT.includes(k)&&typeof v==='string'))throw new Error('only text fields can change');
    Object.assign(c,changes);store(cards);render()},
  archiveCard(id){const c=cards.find(x=>x.id===id);if(!c)throw new Error('unknown card');c.archived=true;store(cards);render()},
  showMessage(text){document.querySelector('#message').textContent=String(text)}
});
function render(){document.querySelector('#source').textContent='Synced from '+window.initialState.tracker;
  const list=document.querySelector('#cards');list.replaceChildren();
  for(const c of cards)list.append(el('li',{'data-id':c.id,'data-external-id':c.externalId,'data-title':c.title,'data-description':c.description,'data-archived':c.archived},
    (c.archived?'[archived] ':'')+c.externalId+' '+c.title+(c.description?' — '+c.description:'')))}
document.querySelector('#sync').addEventListener('click',()=>{if(behavior)behavior(structuredClone(window.initialState.upstream))});
""",
    "fixtures": [
        {"state": {"tracker": "Jira project WEB", "cards": [
            {"id": "c1", "externalId": "WEB-1", "title": "Login page", "description": "Build the login form",
             "sourceTitle": "Login page", "sourceDescription": "Build the login form", "archived": False},
            {"id": "c2", "externalId": "WEB-2", "title": "Fix crash (urgent, seen twice)", "description": "Null pointer",
             "sourceTitle": "Fix crash", "sourceDescription": "Null pointer", "archived": False},
            {"id": "c3", "externalId": "WEB-3", "title": "Old task", "description": "",
             "sourceTitle": "Old task", "sourceDescription": "", "archived": False}],
            "upstream": [
            {"externalId": "WEB-1", "title": "Login page with SSO", "description": "Build the login form"},
            {"externalId": "WEB-2", "title": "Fix crash", "description": "Null pointer in the parser"},
            {"externalId": "WEB-4", "title": "Write docs", "description": "API reference"}]},
         "updated": [["WEB-1", "title", "Login page with SSO"], ["WEB-2", "description", "Null pointer in the parser"]],
         "kept": [["WEB-2", "title", "Fix crash (urgent, seen twice)"]],
         "created": ["WEB-4", "Write docs", "API reference"], "missing": "WEB-3"},
        {"state": {"tracker": "GitHub repository acme/app", "cards": [
            {"id": "c1", "externalId": "G-10", "title": "Dark mode", "description": "Add a theme toggle; check contrast first",
             "sourceTitle": "Dark mode", "sourceDescription": "Add a theme toggle", "archived": False},
            {"id": "c2", "externalId": "G-11", "title": "Export CSV", "description": "",
             "sourceTitle": "Export CSV", "sourceDescription": "", "archived": False},
            {"id": "c3", "externalId": "G-12", "title": "Typo in footer", "description": "",
             "sourceTitle": "Typo in footer", "sourceDescription": "", "archived": False},
            {"id": "c4", "externalId": "G-14", "title": "Release 2.0 (our checklist)", "description": "Tag and publish",
             "sourceTitle": "Release 2.0", "sourceDescription": "Tag and publish", "archived": False}],
            "upstream": [
            {"externalId": "G-10", "title": "Dark mode", "description": "Add a theme toggle"},
            {"externalId": "G-11", "title": "Export CSV", "description": "Include a header row"},
            {"externalId": "G-14", "title": "Release 2.0", "description": "Tag, sign and publish"},
            {"externalId": "G-13", "title": "Import JSON", "description": "From Trello exports"}]},
         "updated": [["G-11", "description", "Include a header row"], ["G-14", "description", "Tag, sign and publish"]],
         "kept": [["G-10", "description", "Add a theme toggle; check contrast first"],
                  ["G-14", "title", "Release 2.0 (our checklist)"]],
         "created": ["G-13", "Import JSON", "From Trello exports"], "missing": "G-12"},
    ],
    "journey_js": r"""
  const n=index+1;
  const read=()=>page.locator('#cards li').evaluateAll(ns=>ns.map(x=>({ext:x.dataset.externalId,title:x.dataset.title,description:x.dataset.description,archived:x.dataset.archived})));
  const initial=fixture.state.cards.map(c=>({ext:c.externalId,title:c.title,description:c.description,archived:'false'}));
  if(JSON.stringify(await read())!==JSON.stringify(initial))throw new InterfaceError('cards missing or changed before sync');
  await (await one(page,'#sync')).click();await reload(page);
  const after=await read();const by=ext=>after.filter(c=>c.ext===ext);
  const has=([ext,field,value])=>by(ext).length===1&&by(ext)[0][field]===value;
  check(`unchanged_local_text_updated_${n}`,fixture.updated.every(has));
  check(`local_edit_kept_${n}`,fixture.kept.every(has));
  const [ext,title,description]=fixture.created;
  check(`new_item_created_${n}`,by(ext).length===1&&by(ext)[0].title===title&&by(ext)[0].description===description&&by(ext)[0].archived==='false');
  check(`missing_item_archived_${n}`,by(fixture.missing).length===1&&by(fixture.missing)[0].archived==='true'
    &&after.filter(c=>c.ext!==fixture.missing).every(c=>c.archived==='false'));
""",
    "target": ["unchanged_local_text_updated_1", "unchanged_local_text_updated_2", "local_edit_kept_1",
               "local_edit_kept_2"],
    "non_target": ["new_item_created_1", "new_item_created_2", "missing_item_archived_1", "missing_item_archived_2"],
    "controls": {
        "reference": ("app.onSync(items=>{const cards=app.cards();for(const it of items){const c=cards.find(x=>x.externalId===it.externalId);if(!c){app.createCard({externalId:it.externalId,title:it.title,description:it.description});continue}const ch={};for(const [f,s] of [['title','sourceTitle'],['description','sourceDescription']])if(it[f]!==c[s]&&c[f]===c[s]){ch[f]=it[f];ch[s]=it[f]}if(Object.keys(ch).length)app.updateCard(c.id,ch)}for(const c of cards)if(!c.archived&&!items.some(it=>it.externalId===c.externalId))app.archiveCard(c.id)});", "pass"),
        "alternative": ("app.onSync(function(items){var cards=app.cards();items.forEach(function(it){var c=cards.filter(function(x){return x.externalId===it.externalId})[0];if(!c)return app.createCard({externalId:it.externalId,title:it.title,description:it.description});var ch={};if(c.title===c.sourceTitle){ch.title=it.title;ch.sourceTitle=it.title}if(c.description===c.sourceDescription){ch.description=it.description;ch.sourceDescription=it.description}app.updateCard(c.id,ch)});cards.forEach(function(c){if(!items.some(function(it){return it.externalId===c.externalId}))app.archiveCard(c.id)})});", "pass"),
        "target-mutant": ("app.onSync(items=>{const cards=app.cards();for(const it of items){const c=cards.find(x=>x.externalId===it.externalId);if(c)app.updateCard(c.id,{title:it.title,description:it.description,sourceTitle:it.title,sourceDescription:it.description});else app.createCard({externalId:it.externalId,title:it.title,description:it.description})}for(const c of cards)if(!items.some(it=>it.externalId===c.externalId))app.archiveCard(c.id)});", "target_only_failure"),
        "never-update-mutant": ("app.onSync(items=>{const cards=app.cards();for(const it of items)if(!cards.some(c=>c.externalId===it.externalId))app.createCard({externalId:it.externalId,title:it.title,description:it.description});for(const c of cards)if(!items.some(it=>it.externalId===c.externalId))app.archiveCard(c.id)});", "target_only_failure"),
        "non-target-mutant": ("app.onSync(items=>{const cards=app.cards();for(const it of items){const c=cards.find(x=>x.externalId===it.externalId);if(!c)continue;const ch={};for(const [f,s] of [['title','sourceTitle'],['description','sourceDescription']])if(it[f]!==c[s]&&c[f]===c[s]){ch[f]=it[f];ch[s]=it[f]}if(Object.keys(ch).length)app.updateCard(c.id,ch)}});", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement the reconciliation of a list synced from an external tracker. When the user clicks Sync now, "
             "the handler receives the tracker's current items (externalId, title, description). Reconcile them "
             "against the list's cards from app.cards(), which carry each card's externalId, title, description, "
             "archived flag and the last synchronized source values sourceTitle and sourceDescription, using "
             "app.createCard({externalId, title, description}), app.updateCard(id, changes) and app.archiveCard(id): "
             "a new external item creates a WeKan card; upstream title/description changes update the card when "
             "local text still matches the last synchronized source value; local-only text edits are retained; an "
             "external item that disappeared is archived, never deleted.",
        "B": "Clicking Sync now hands the handler the external tracker's current items (externalId, title, "
             "description), which must be reconciled with the synced list's cards. app.cards() returns each card's "
             "externalId, title, description, archived flag and the last synchronized source values sourceTitle and "
             "sourceDescription; changes are made with app.createCard({externalId, title, description}), "
             "app.updateCard(id, changes) and app.archiveCard(id). An item that is new in the tracker becomes a new "
             "WeKan card. A title or description changed upstream is copied to the card only while the card's text "
             "is still the last synchronized source value, so text edited only locally is kept. An item that is no "
             "longer in the tracker has its card archived, never deleted.",
        "C": "Implement the reconciliation of a list synced from an external tracker. When the user clicks Sync now, "
             "the handler receives the tracker's current items (externalId, title, description). Reconcile them "
             "against the list's cards from app.cards(), which carry each card's externalId, title, description, "
             "archived flag and the last synchronized source values sourceTitle and sourceDescription, using "
             "app.createCard({externalId, title, description}), app.updateCard(id, changes) and app.archiveCard(id): "
             "a new external item creates a WeKan card; an external item that disappeared is archived, never deleted.",
    },
}

CASES = [WEEK_TOGGLE, SWIMLANE_BELOW, HOME_DROP, FIELD_ORDER, MEMBER_RESTRICTION, SYNC_TEXT]
