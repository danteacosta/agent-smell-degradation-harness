"""Mattermost selection cases (six admitted rules; arm A from the frame-end documentation snapshot)."""

SNAPSHOT = "bd09d959514c34e72a33c24663b5946682b656ec"

PLAYBOOK_MARKDOWN = {
    "case": "mattermost-playbook-task-markdown",
    "candidate_id": "rc-0284c8781546",
    "project_id": "mattermost",
    "source": {"commit": "5fb0a2b285", "file": "source/end-user-guide/workflow-automation/work-with-playbooks.rst",
               "snapshot": SNAPSHOT,
               "snapshot_file": "source/end-user-guide/workflow-automation/work-with-playbooks.rst"},
    "title": "Playbook tasks",
    "register": "app.onAdd",
    "control": "Add a task button",
    "body": '<h1>Playbook: <span id="playbook"></span></h1><h2>Tasks</h2><ol id="tasks" aria-label="Checklist"></ol>'
            '<label>Task <input id="task-text" size="60"></label><button id="add-task" type="button">Add a task</button>'
            '<p id="message" role="status"></p>',
    "state_js": r"""
let tasks=load([]);
const app=Object.freeze({
  onAdd:register,
  tasks(){return structuredClone(tasks)},
  addTask(task){if(typeof task!=='object'||task===null||typeof task.text!=='string'||!task.text.trim()||typeof task.html!=='string')throw new Error('text and html required');
    tasks.push({text:task.text,html:task.html});store(tasks);render()},
  showMessage(text){document.querySelector('#message').textContent=String(text)}
});
function render(){
  document.querySelector('#playbook').textContent=window.initialState.playbook;
  const list=document.querySelector('#tasks');list.replaceChildren();
  for(const t of tasks){const li=el('li',{'data-text':t.text});const span=el('span',{class:'task-text'});span.innerHTML=t.html;li.append(el('input',{type:'checkbox','aria-label':'Done'}),document.createTextNode(' '),span);list.append(li)}
}
document.querySelector('#add-task').addEventListener('click',()=>{if(behavior)behavior(document.querySelector('#task-text').value)});
""",
    "fixtures": [
        {"state": {"playbook": "Incident response"},
         "tasks": ["**Review** the incident timeline", "Notify stakeholders"],
         "formatted": [[0, "Review the incident timeline", [["strong,b", "Review"]]]], "plain": [1]},
        {"state": {"playbook": "Release checklist"},
         "tasks": ["Page the on-call engineer", "Confirm *all* alerts are **resolved**"],
         "formatted": [[1, "Confirm all alerts are resolved", [["em,i", "all"], ["strong,b", "resolved"]]]], "plain": [0]},
    ],
    "journey_js": r"""
  const n=index+1;
  if(await page.locator('#tasks li').count()!==0)throw new InterfaceError('tasks present before adding');
  for(const text of fixture.tasks){await (await one(page,'#task-text')).fill(text);await (await one(page,'#add-task')).click()}
  await reload(page);
  const rows=await page.locator('#tasks li').evaluateAll(ns=>ns.map(li=>{const s=li.querySelector('.task-text');
    return {text:li.dataset.text,shown:s?s.textContent.replace(/\s+/g,' ').trim():'',
      parts:s?[...s.querySelectorAll('*')].map(e=>[e.tagName.toLowerCase(),e.textContent.trim()]):[]}}));
  const formatted=fixture.formatted.every(([i,shown,parts])=>{const r=rows[i];return !!r&&r.shown===shown&&!/[*_]/.test(r.shown)&&
    parts.every(([tags,word])=>r.parts.some(([tag,t])=>tags.split(',').includes(tag)&&t===word))});
  check(`markdown_rendered_${n}`,formatted);
  check(`tasks_added_in_order_${n}`,JSON.stringify(rows.map(r=>r.text))===JSON.stringify(fixture.tasks));
  check(`plain_task_shown_as_typed_${n}`,fixture.plain.every(i=>rows[i]&&rows[i].shown===fixture.tasks[i]));
""",
    "target": ["markdown_rendered_1", "markdown_rendered_2"],
    "non_target": ["tasks_added_in_order_1", "tasks_added_in_order_2",
                   "plain_task_shown_as_typed_1", "plain_task_shown_as_typed_2"],
    "controls": {
        "reference": (r"""const esc=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
function md(t){return esc(t).replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g,'<a href="$2">$1</a>').replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>').replace(/__(.+?)__/g,'<strong>$1</strong>').replace(/\*(.+?)\*/g,'<em>$1</em>').replace(/_(.+?)_/g,'<em>$1</em>').replace(/`([^`]+)`/g,'<code>$1</code>')}
app.onAdd(text=>{if(!text.trim())return;app.addTask({text,html:md(text)})});""", "pass"),
        "alternative": (r"""app.onAdd(function(text){var d=document.createElement('div');d.textContent=text;var h=d.innerHTML;
h=h.replace(/(\*\*|__)(?=\S)([\s\S]*?\S)\1/g,'<b>$2</b>').replace(/(\*|_)(?=\S)([\s\S]*?\S)\1/g,'<i>$2</i>');app.addTask({text:text,html:h})});""", "pass"),
        "target-mutant": (r"""const esc=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');app.onAdd(text=>app.addTask({text,html:esc(text)}));""", "target_only_failure"),
        "raw-html-mutant": ("app.onAdd(text=>app.addTask({text,html:text}));", "target_only_failure"),
        "strip-markers-mutant": (r"""app.onAdd(text=>{const d=document.createElement('div');d.textContent=text.replace(/[*_]/g,'');app.addTask({text,html:d.innerHTML})});""", "target_only_failure"),
        "non-target-mutant": (r"""const md=t=>t.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>').replace(/\*(.+?)\*/g,'<em>$1</em>');app.onAdd(text=>app.addTask({text:text.replace(/[*_]/g,''),html:md(text)}));""", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement adding a task to a playbook checklist. To create a checklist in a playbook, go to the Tasks "
             "section and select Add a task to build out checklists in the playbook. When the user selects Add a "
             "task, add the entered task with app.addTask({text, html}), where text is the task as typed and html is "
             "the markup shown for it in the checklist. Playbook tasks consist of text rendered in Markdown (when "
             "present).",
        "B": "Selecting Add a task in the Tasks section of a playbook builds out the playbook's checklist: the typed "
             "task is added through app.addTask({text, html}), with text being the task exactly as entered and html "
             "the markup that the checklist displays for it. Whenever a playbook task's text contains Markdown, that "
             "Markdown is rendered.",
        "C": "Implement adding a task to a playbook checklist. To create a checklist in a playbook, go to the Tasks "
             "section and select Add a task to build out checklists in the playbook. When the user selects Add a "
             "task, add the entered task with app.addTask({text, html}), where text is the task as typed and html is "
             "the markup shown for it in the checklist.",
    },
}

GUEST_CHANNEL = {
    "case": "mattermost-guest-invite-channel",
    "candidate_id": "rc-3fbc295441e2",
    "project_id": "mattermost",
    "source": {"commit": "dbfcaedd0e", "file": "source/end-user-guide/collaborate/invite-people.rst",
               "snapshot": SNAPSHOT, "snapshot_file": "source/end-user-guide/collaborate/invite-people.rst"},
    "title": "Invite people",
    "register": "app.onInvite",
    "control": "Invite button",
    "body": '<h1>Invite people to <span id="team"></span></h1><section aria-label="Invite as guest"><h2>Invite as guest</h2>'
            '<label>Email <input id="guest-email" type="email"></label><fieldset><legend>Channels</legend>'
            '<div id="channels"></div></fieldset><label>Custom message <input id="guest-message" size="50"></label>'
            '<button id="invite" type="button">Invite</button><p id="message" role="status"></p></section>'
            '<h2>Sent invitations</h2><ul id="invitations" aria-label="Sent invitations"></ul>',
    "state_js": r"""
let invitations=load([]);
const channels=window.initialState.channels;
const app=Object.freeze({
  onInvite:register,
  channels(){return structuredClone(channels)},
  invitations(){return structuredClone(invitations)},
  inviteGuest(inv){if(typeof inv!=='object'||inv===null||typeof inv.email!=='string'||!inv.email.trim()||!Array.isArray(inv.channels)||!inv.channels.every(id=>channels.some(c=>c.id===id))||(inv.message!==undefined&&typeof inv.message!=='string'))throw new Error('email, known channel ids and optional message required');
    invitations.push({email:inv.email.trim(),channels:[...inv.channels],message:inv.message??''});store(invitations);render()},
  showMessage(text){document.querySelector('#message').textContent=String(text)}
});
function render(){
  document.querySelector('#team').textContent=window.initialState.team;
  const list=document.querySelector('#invitations');list.replaceChildren();
  for(const i of invitations)list.append(el('li',{'data-email':i.email,'data-channels':i.channels.join(',')},
    i.email+' — '+(i.channels.map(id=>channels.find(c=>c.id===id).name).join(', ')||'no channels')))
}
const box=document.querySelector('#channels');
for(const c of channels){const label=el('label');label.append(el('input',{type:'checkbox',name:'channel',value:c.id}),document.createTextNode(' '+c.name));box.append(label)}
document.querySelector('#invite').addEventListener('click',()=>{if(behavior)behavior({email:document.querySelector('#guest-email').value,
  channels:[...document.querySelectorAll('input[name=channel]:checked')].map(b=>b.value),message:document.querySelector('#guest-message').value})});
""",
    "fixtures": [
        {"state": {"team": "Acme", "channels": [{"id": "c1", "name": "Project Falcon"}, {"id": "c2", "name": "Vendor Support"},
                                                {"id": "c3", "name": "Design Review"}]},
         "steps": [{"email": "ana@partner.example", "channels": [], "message": ""},
                   {"email": "ben@partner.example", "channels": ["c2", "c3"], "message": ""}]},
        {"state": {"team": "Northwind", "channels": [{"id": "d1", "name": "Onboarding"}, {"id": "d2", "name": "Q4 Launch"}]},
         "steps": [{"email": "carla@agency.example", "channels": ["d1"], "message": "Welcome aboard!"},
                   {"email": "dev@agency.example", "channels": [], "message": "See you there."}]},
    ],
    "journey_js": r"""
  const n=index+1;
  const invites=()=>page.locator('#invitations li').evaluateAll(ns=>ns.map(x=>({email:x.dataset.email,channels:x.dataset.channels?x.dataset.channels.split(',').sort():[]})));
  if((await invites()).length!==0||await page.locator('input[name=channel]').count()!==fixture.state.channels.length)throw new InterfaceError('channel choices missing or invitations present');
  for(const step of fixture.steps){
    await (await one(page,'#guest-email')).fill(step.email);
    if(step.message)await (await one(page,'#guest-message')).fill(step.message);
    for(const id of step.channels)await page.locator(`input[name=channel][value="${id}"]`).check();
    if(step.channels.length)await (await one(page,'#invite')).click();
    else{const b=page.locator('#invite');if(await b.count()===1&&await b.isVisible()&&await b.isEnabled())await b.click()}
    await page.waitForTimeout(100);await reload(page);
  }
  const all=await invites();
  const invalid=fixture.steps.find(s=>!s.channels.length),valid=fixture.steps.find(s=>s.channels.length);
  check(`no_invite_without_channel_${n}`,!all.some(i=>i.email===invalid.email));
  const sent=all.filter(i=>i.email===valid.email);
  check(`invite_limited_to_selected_channels_${n}`,sent.length===1&&JSON.stringify(sent[0].channels)===JSON.stringify([...valid.channels].sort()));
""",
    "target": ["no_invite_without_channel_1", "no_invite_without_channel_2"],
    "non_target": ["invite_limited_to_selected_channels_1", "invite_limited_to_selected_channels_2"],
    "controls": {
        "reference": ("app.onInvite(f=>{if(!f.channels.length){app.showMessage('Select at least one channel for the guest.');return}app.inviteGuest(f)});", "pass"),
        "disable-control": ("const inv=document.querySelector('#invite');const sync=()=>{inv.disabled=!document.querySelector('input[name=channel]:checked')};document.querySelectorAll('input[name=channel]').forEach(b=>b.addEventListener('change',sync));sync();app.onInvite(function(f){if(f.channels.length>0)app.inviteGuest(f)});", "pass"),
        "target-mutant": ("app.onInvite(f=>app.inviteGuest(f));", "target_only_failure"),
        "all-channels-mutant": ("app.onInvite(f=>{if(!f.channels.length)return;app.inviteGuest({...f,channels:app.channels().map(c=>c.id)})});", "non_target_only_failure"),
        "non-target-mutant": ("app.onInvite(()=>{});", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement Invite as guest in the Invite People dialog. Invite a guest temporarily with limited "
             "workspace access: specify their email address, select the channels they can access, and optionally "
             "add a custom message. When the user selects Invite, send the invitation with "
             "app.inviteGuest({email, channels, message}). When inviting guests, you must select at least one "
             "channel they can access. Guests are limited to the channels you specify and cannot discover other "
             "channels.",
        "B": "In the Invite People dialog, Invite as guest gives someone temporary, limited access to the workspace: "
             "you enter the guest's email address, choose the channels they may use and can add a personal message "
             "if you like. Selecting Invite sends the invitation through app.inviteGuest({email, channels, "
             "message}). A guest invitation requires at least one selected channel; the guest only gets the channels "
             "you chose and cannot discover any others.",
        "C": "Implement Invite as guest in the Invite People dialog. Invite a guest temporarily with limited "
             "workspace access: specify their email address, select the channels they can access, and optionally "
             "add a custom message. When the user selects Invite, send the invitation with "
             "app.inviteGuest({email, channels, message}). Guests are limited to the channels you specify and cannot "
             "discover other channels.",
    },
}

TIMEZONE_DEFAULT = {
    "case": "mattermost-timezone-default-automatic",
    "candidate_id": "rc-4fa8e7483b1a",
    "project_id": "mattermost",
    "source": {"commit": "34180cef60", "file": "source/end-user-guide/preferences/manage-your-display-options.rst",
               "snapshot": SNAPSHOT,
               "snapshot_file": "source/end-user-guide/preferences/manage-your-display-options.rst"},
    "title": "Display settings",
    "register": "app.onEdit",
    "control": "Edit button of the Timezone setting",
    "body": '<h1>Settings › Display</h1><section aria-label="Timezone"><h2>Timezone</h2><p id="current"></p>'
            '<button id="edit" type="button">Edit</button><div id="editor" hidden>'
            '<label><input id="automatic" type="checkbox"> Automatic</label>'
            '<label>Timezone <select id="manual-timezone"></select></label>'
            '<button id="save" type="button">Save</button></div></section>',
    "state_js": r"""
let pref=load(window.initialState.timezone);
const zones=window.initialState.zones;
const app=Object.freeze({
  onEdit:register,
  zones(){return [...zones]},
  computerTimezone(){return window.initialState.computerTimezone},
  showEditor(values){if(typeof values!=='object'||values===null||typeof values.automatic!=='boolean'||typeof values.manualTimezone!=='string')throw new Error('automatic and manualTimezone required');
    document.querySelector('#automatic').checked=values.automatic;document.querySelector('#manual-timezone').value=values.manualTimezone;document.querySelector('#editor').hidden=false}
});
function render(){const c=document.querySelector('#current');c.dataset.pref=JSON.stringify(pref);
  c.textContent=pref===null?'—':pref.automatic?'Automatic ('+window.initialState.computerTimezone+')':(pref.manualTimezone||'—')}
const select=document.querySelector('#manual-timezone');for(const z of zones)select.append(el('option',{value:z},z));
document.querySelector('#edit').addEventListener('click',()=>{if(behavior)behavior(pref===null?null:structuredClone(pref))});
document.querySelector('#save').addEventListener('click',()=>{pref={automatic:document.querySelector('#automatic').checked,manualTimezone:select.value};store(pref);document.querySelector('#editor').hidden=true;render()});
""",
    "fixtures": [
        {"state": {"timezone": None, "computerTimezone": "Europe/Lisbon",
                   "zones": ["America/New_York", "Europe/Lisbon", "Asia/Tokyo"]}, "zone": "Asia/Tokyo"},
        {"state": {"timezone": None, "computerTimezone": "Australia/Sydney",
                   "zones": ["America/Sao_Paulo", "Europe/Berlin", "Australia/Sydney"]}, "zone": "America/Sao_Paulo"},
    ],
    "journey_js": r"""
  const n=index+1;const stored=()=>page.locator('#current').evaluate(x=>JSON.parse(x.dataset.pref));
  if(await stored()!==null||await page.locator('#editor').isVisible())throw new InterfaceError('timezone preference saved before editing');
  await (await one(page,'#edit')).click();await (await one(page,'#save')).click();await reload(page);
  const first=await stored();
  check(`untouched_save_keeps_automatic_${n}`,first!==null&&first.automatic===true);
  await (await one(page,'#edit')).click();await (await one(page,'#automatic')).setChecked(false);
  await (await one(page,'#manual-timezone')).selectOption(fixture.zone);await (await one(page,'#save')).click();await reload(page);
  const second=await stored();
  check(`manual_timezone_saved_${n}`,second!==null&&second.automatic===false&&second.manualTimezone===fixture.zone);
  await (await one(page,'#edit')).click();await (await one(page,'#save')).click();await reload(page);
  const third=await stored();
  check(`saved_choice_kept_on_reopen_${n}`,third!==null&&third.automatic===false&&third.manualTimezone===fixture.zone);
""",
    "target": ["untouched_save_keeps_automatic_1", "untouched_save_keeps_automatic_2"],
    "non_target": ["manual_timezone_saved_1", "manual_timezone_saved_2",
                   "saved_choice_kept_on_reopen_1", "saved_choice_kept_on_reopen_2"],
    "controls": {
        "reference": ("app.onEdit(p=>app.showEditor(p??{automatic:true,manualTimezone:''}));", "pass"),
        "alternative": ("app.onEdit(function(p){if(p===null)p={automatic:true,manualTimezone:app.computerTimezone()};app.showEditor({automatic:p.automatic,manualTimezone:p.manualTimezone})});", "pass"),
        "target-mutant": ("app.onEdit(p=>app.showEditor({automatic:p?p.automatic:false,manualTimezone:p?p.manualTimezone:''}));", "target_only_failure"),
        "computer-zone-manual-mutant": ("app.onEdit(p=>app.showEditor(p||{automatic:false,manualTimezone:app.computerTimezone()}));", "target_only_failure"),
        "non-target-mutant": ("app.onEdit(p=>app.showEditor({automatic:true,manualTimezone:p?p.manualTimezone:''}));", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement the Timezone setting in Settings > Display. You can customize the timezone used for "
             "timestamps in Mattermost and in email notifications. Select Timezone > Edit to select your timezone: "
             "when the user selects Edit, open the editor with app.showEditor({automatic, manualTimezone}); the "
             "handler receives the user's saved timezone preference ({automatic, manualTimezone}, or null if they "
             "have never saved one), and Save stores the values shown in the editor. You can also select Automatic "
             "to set your timezone automatically based on your computer's timezone settings. This option is enabled "
             "by default.",
        "B": "Under Settings > Display, the Timezone setting controls the timezone of timestamps in Mattermost and in "
             "email notifications. Timezone > Edit is where you pick it: Edit opens the editor through "
             "app.showEditor({automatic, manualTimezone}), the handler is given the saved timezone preference "
             "({automatic, manualTimezone}, or null when none has ever been saved), and Save keeps whatever the "
             "editor shows. Another choice is Automatic, which takes the timezone from your computer's timezone "
             "settings; Automatic is turned on unless the user changes it.",
        "C": "Implement the Timezone setting in Settings > Display. You can customize the timezone used for "
             "timestamps in Mattermost and in email notifications. Select Timezone > Edit to select your timezone: "
             "when the user selects Edit, open the editor with app.showEditor({automatic, manualTimezone}); the "
             "handler receives the user's saved timezone preference ({automatic, manualTimezone}, or null if they "
             "have never saved one), and Save stores the values shown in the editor. You can also select Automatic "
             "to set your timezone automatically based on your computer's timezone settings.",
    },
}

AUTOTRANSLATE = {
    "case": "mattermost-channel-autotranslate",
    "candidate_id": "rc-554bcd113361",
    "project_id": "mattermost",
    "source": {"commit": "73d7ca79e6", "file": "source/end-user-guide/collaborate/collaborate-within-channels.rst",
               "snapshot": SNAPSHOT, "snapshot_file": "source/end-user-guide/collaborate/autotranslate-messages.rst"},
    "title": "Channel",
    "register": "app.onOpen",
    "control": "Open channel button",
    "body": '<h1>Channels</h1><p id="signed-in"></p><button id="open" type="button">Open channel</button>'
            '<h2 id="channel-name"></h2><ol id="messages" aria-label="Messages"></ol>',
    "state_js": r"""
let shown=[];
const app=Object.freeze({
  onOpen:register,
  user(){return structuredClone(window.initialState.user)},
  channel(){return structuredClone(window.initialState.channel)},
  translate(text,language){if(typeof text!=='string'||typeof language!=='string')throw new Error('text and language required');
    const hit=window.initialState.translations.find(t=>t.text===text&&t.language===language);return hit?hit.translation:text},
  showMessages(list){const msgs=window.initialState.channel.messages;
    if(!Array.isArray(list)||!list.every(m=>m&&msgs.some(x=>x.id===m.id)&&typeof m.text==='string'))throw new Error('known message ids and text required');
    shown=list.map(m=>({id:m.id,text:m.text}));render()}
});
function render(){const s=window.initialState;document.querySelector('#signed-in').textContent='Signed in as '+s.user.username;
  document.querySelector('#channel-name').textContent=shown.length?'~'+s.channel.name:'';
  const list=document.querySelector('#messages');list.replaceChildren();
  for(const m of shown){const author=s.channel.messages.find(x=>x.id===m.id).author;list.append(el('li',{'data-id':m.id,'data-text':m.text},author+': '+m.text))}}
document.querySelector('#open').addEventListener('click',()=>{if(behavior)behavior(app.channel())});
""",
    "fixtures": [
        {"state": {"user": {"username": "ana", "language": "en"},
                   "channel": {"name": "global-ops", "messages": [
                       {"id": "m1", "author": "lucas", "language": "pt", "text": "Bom dia, equipe!"},
                       {"id": "m2", "author": "ana", "language": "en", "text": "Deploy finished at 09:00."},
                       {"id": "m3", "author": "sofia", "language": "es", "text": "¿Quién revisa el cambio?"}]},
                   "translations": [
                       {"text": "Bom dia, equipe!", "language": "en", "translation": "Good morning, team!"},
                       {"text": "¿Quién revisa el cambio?", "language": "en", "translation": "Who is reviewing the change?"},
                       {"text": "Deploy finished at 09:00.", "language": "pt", "translation": "Implantação concluída às 09:00."}]},
         "foreign": {"m1": "Good morning, team!", "m3": "Who is reviewing the change?"}, "own": ["m2"]},
        {"state": {"user": {"username": "jonas", "language": "de"},
                   "channel": {"name": "release-train", "messages": [
                       {"id": "n1", "author": "mia", "language": "en", "text": "Release notes are ready."},
                       {"id": "n2", "author": "jonas", "language": "de", "text": "Danke, ich schaue es mir an."},
                       {"id": "n3", "author": "luc", "language": "fr", "text": "Réunion demain à 15 h."}]},
                   "translations": [
                       {"text": "Release notes are ready.", "language": "de", "translation": "Die Versionshinweise sind fertig."},
                       {"text": "Réunion demain à 15 h.", "language": "de", "translation": "Besprechung morgen um 15 Uhr."},
                       {"text": "Réunion demain à 15 h.", "language": "en", "translation": "Meeting tomorrow at 3 pm."}]},
         "foreign": {"n1": "Die Versionshinweise sind fertig.", "n3": "Besprechung morgen um 15 Uhr."}, "own": ["n2"]},
    ],
    "journey_js": r"""
  const n=index+1;const msgs=fixture.state.channel.messages;
  if(await page.locator('#messages li').count()!==0)throw new InterfaceError('messages shown before opening the channel');
  await (await one(page,'#open')).click();
  const rows=await page.locator('#messages li').evaluateAll(ns=>ns.map(x=>[x.dataset.id,x.innerText,x.checkVisibility()]));
  const shown=Object.fromEntries(rows.map(([id,text,visible])=>[id,visible?text:null]));
  check(`foreign_messages_translated_${n}`,Object.entries(fixture.foreign).every(([id,text])=>shown[id]===msgs.find(m=>m.id===id).author+': '+text));
  check(`own_language_messages_unchanged_${n}`,fixture.own.every(id=>shown[id]===msgs.find(m=>m.id===id).author+': '+msgs.find(m=>m.id===id).text));
  check(`all_messages_in_order_${n}`,rows.every(r=>r[2])&&JSON.stringify(rows.map(r=>r[0]))===JSON.stringify(msgs.map(m=>m.id)));
""",
    "target": ["foreign_messages_translated_1", "foreign_messages_translated_2"],
    "non_target": ["own_language_messages_unchanged_1", "own_language_messages_unchanged_2",
                   "all_messages_in_order_1", "all_messages_in_order_2"],
    "controls": {
        "hidden-messages": ("app.onOpen(ch=>{const lang=app.user().language;app.showMessages(ch.messages.map(m=>({id:m.id,text:m.language===lang?m.text:app.translate(m.text,lang)})));document.querySelector('#messages').style.display='none'});", "mixed_failure"),
        "visible-originals": ("app.onOpen(ch=>{const lang=app.user().language;app.showMessages(ch.messages.map(m=>({id:m.id,text:m.language===lang?m.text:app.translate(m.text,lang)})));for(const li of document.querySelectorAll('#messages li')){const m=ch.messages.find(m=>m.id===li.dataset.id);li.textContent=m.author+': '+m.text}});", "target_only_failure"),
        "reference": ("app.onOpen(ch=>{const lang=app.user().language;app.showMessages(ch.messages.map(m=>({id:m.id,text:m.language===lang?m.text:app.translate(m.text,lang)})))});", "pass"),
        "alternative": ("app.onOpen(function(ch){var lang=app.user().language;var out=[];for(var i=0;i<ch.messages.length;i++){out.push({id:ch.messages[i].id,text:app.translate(ch.messages[i].text,lang)})}app.showMessages(out)});", "pass"),
        "target-mutant": ("app.onOpen(ch=>app.showMessages(ch.messages.map(m=>({id:m.id,text:m.text}))));", "target_only_failure"),
        "english-only-mutant": ("app.onOpen(ch=>app.showMessages(ch.messages.map(m=>({id:m.id,text:m.language==='en'?m.text:app.translate(m.text,'en')}))));", "target_only_failure"),
        "non-target-mutant": ("app.onOpen(ch=>{const lang=app.user().language;app.showMessages(ch.messages.filter(m=>m.language!==lang).map(m=>({id:m.id,text:app.translate(m.text,lang)})))});", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement opening a channel. When the user selects Open channel, show all of the channel's messages, in "
             "their original order, with app.showMessages([{id, text}]). app.user().language is your preferred "
             "display language, each message in app.channel().messages has the language it was written in, and "
             "app.translate(text, language) returns the text translated into that language. This channel has "
             "auto-translation enabled: its messages are automatically translated into your preferred language and "
             "shown in place of the original text.",
        "B": "Selecting Open channel lists every message of the channel, keeping their original order, through "
             "app.showMessages([{id, text}]). Your preferred display language is app.user().language, every message "
             "in app.channel().messages records the language it was written in, and app.translate(text, language) "
             "gives the text in the requested language. Auto-translation is on for this channel, so instead of its "
             "original text each message appears translated, without any action from you, into your preferred "
             "language.",
        "C": "Implement opening a channel. When the user selects Open channel, show all of the channel's messages, in "
             "their original order, with app.showMessages([{id, text}]). app.user().language is your preferred "
             "display language, each message in app.channel().messages has the language it was written in, and "
             "app.translate(text, language) returns the text translated into that language.",
    },
}

MENTION_ADD = {
    "case": "mattermost-mention-add-prompt",
    "candidate_id": "rc-882709afd891",
    "project_id": "mattermost",
    "source": {"commit": "6c4598422f", "file": "source/end-user-guide/collaborate/manage-channel-members.rst",
               "snapshot": SNAPSHOT, "snapshot_file": "source/end-user-guide/collaborate/manage-channel-members.rst"},
    "title": "Channel",
    "register": "app.onSend",
    "control": "Send button",
    "body": '<h1>~<span id="channel"></span></h1><p id="signed-in"></p><h2>Members</h2>'
            '<ul id="members" aria-label="Members"></ul><ol id="posts" aria-label="Messages"></ol>'
            '<ul id="notices" aria-label="Notices"></ul><label>Message <input id="message" size="60"></label>'
            '<button id="send" type="button">Send</button>',
    "state_js": r"""
let channel=load({members:window.initialState.members,posts:[]});
let notices=[];
const users=window.initialState.users;
const app=Object.freeze({
  onSend:register,
  currentUser(){return window.initialState.currentUser},
  members(){return [...channel.members]},
  users(){return structuredClone(users)},
  post(text){if(typeof text!=='string'||!text.trim())throw new Error('text required');channel.posts.push({author:window.initialState.currentUser,text});store(channel);render()},
  addMembers(usernames){if(!Array.isArray(usernames)||!usernames.every(u=>users.some(x=>x.username===u)))throw new Error('known usernames required');
    for(const u of usernames)if(!channel.members.includes(u))channel.members.push(u);store(channel);render()},
  showNotice(text,action){if(typeof text!=='string'||!text)throw new Error('text required');
    if(action!==undefined&&(typeof action!=='object'||action===null||typeof action.label!=='string'||typeof action.run!=='function'))throw new Error('action needs label and run');
    notices.push({text,action});render()}
});
function render(){const s=window.initialState;document.querySelector('#channel').textContent=s.channel;
  document.querySelector('#signed-in').textContent='Signed in as '+s.currentUser;
  const members=document.querySelector('#members');members.replaceChildren();
  for(const u of channel.members)members.append(el('li',{'data-username':u},u));
  const posts=document.querySelector('#posts');posts.replaceChildren();
  for(const p of channel.posts)posts.append(el('li',{'data-text':p.text},p.author+': '+p.text));
  const list=document.querySelector('#notices');list.replaceChildren();
  for(const notice of notices){const li=el('li');li.append(el('span',{},notice.text));
    if(notice.action){const b=el('button',{type:'button'},notice.action.label);
      b.addEventListener('click',()=>{notices=notices.filter(x=>x!==notice);render();notice.action.run()});li.append(document.createTextNode(' '),b)}
    list.append(li)}}
document.querySelector('#send').addEventListener('click',()=>{if(behavior)behavior(document.querySelector('#message').value)});
""",
    "fixtures": [
        {"state": {"channel": "deploys", "currentUser": "alice", "members": ["alice", "bob"],
                   "users": [{"username": "alice"}, {"username": "bob"}, {"username": "carol"}, {"username": "dan"}]},
         "text": "@carol can you review the deploy plan? cc @bob", "nonmembers": ["carol"], "mentioned_members": ["bob"],
         "add": "carol"},
        {"state": {"channel": "launch-room", "currentUser": "erin", "members": ["erin", "frank", "gina"],
                   "users": [{"username": "erin"}, {"username": "frank"}, {"username": "gina"},
                             {"username": "hal"}, {"username": "ivy"}]},
         "text": "@hal and @ivy please join the call, @frank FYI", "nonmembers": ["hal", "ivy"],
         "mentioned_members": ["frank"], "add": "ivy"},
    ],
    "journey_js": r"""
  const n=index+1;
  const members=()=>page.locator('#members li').evaluateAll(ns=>ns.map(x=>x.dataset.username));
  const posts=()=>page.locator('#posts li').evaluateAll(ns=>ns.map(x=>x.dataset.text));
  const names=u=>new RegExp('(^|[^a-z0-9._-])@?'+u+'(?![a-z0-9._-])','i');
  if(JSON.stringify(await members())!==JSON.stringify(fixture.state.members)||(await posts()).length||await page.locator('#notices li').count())throw new InterfaceError('channel changed before sending');
  await (await one(page,'#message')).fill(fixture.text);await (await one(page,'#send')).click();await page.waitForTimeout(100);
  const notices=await page.locator('#notices li').evaluateAll(ns=>ns.map(x=>x.textContent));
  const afterSend=await members();
  check(`nonmember_prompted_not_added_${n}`,fixture.nonmembers.every(u=>notices.some(t=>names(u).test(t))&&!afterSend.includes(u)));
  check(`member_not_prompted_${n}`,fixture.mentioned_members.every(u=>!notices.some(t=>names(u).test(t))));
  const notice=page.locator('#notices li').filter({hasText:names(fixture.add)});
  if(await notice.count()>=1&&await notice.first().locator('button').count()>=1){await notice.first().locator('button').first().click();await page.waitForTimeout(100)}
  await reload(page);
  const after=await members();
  check(`prompt_adds_nonmember_${n}`,after.includes(fixture.add));
  check(`message_posted_once_${n}`,JSON.stringify(await posts())===JSON.stringify([fixture.text]));
  check(`existing_members_kept_${n}`,fixture.state.members.every(u=>after.includes(u)));
""",
    "target": ["nonmember_prompted_not_added_1", "nonmember_prompted_not_added_2", "member_not_prompted_1",
               "member_not_prompted_2", "prompt_adds_nonmember_1", "prompt_adds_nonmember_2"],
    "non_target": ["message_posted_once_1", "message_posted_once_2", "existing_members_kept_1", "existing_members_kept_2"],
    "controls": {
        "reference": (r"""app.onSend(text=>{if(!text.trim())return;app.post(text);const members=app.members(),known=app.users().map(u=>u.username);
const mentioned=[...new Set([...text.matchAll(/@([a-z0-9._-]+)/gi)].map(m=>m[1].toLowerCase()))];
for(const u of mentioned.filter(u=>known.includes(u)&&!members.includes(u)))app.showNotice('@'+u+' did not get notified by this mention because they are not in the channel. Would you like to add them to it?',{label:'Add them',run:()=>app.addMembers([u])})});""", "pass"),
        "one-notice": (r"""app.onSend(function(text){app.post(text);var m=app.members();var missing=(text.match(/@[\w.-]+/g)||[]).map(function(s){return s.slice(1)}).filter(function(u,i,a){return a.indexOf(u)===i&&m.indexOf(u)<0&&app.users().some(function(x){return x.username===u})});
if(missing.length)app.showNotice(missing.map(function(u){return '@'+u}).join(' and ')+' are not members of this channel. Add them?',{label:'Add to channel',run:function(){app.addMembers(missing)}})});""", "pass"),
        "target-mutant": ("app.onSend(text=>app.post(text));", "target_only_failure"),
        "auto-add-mutant": (r"""app.onSend(text=>{app.post(text);const m=app.members();const add=[...text.matchAll(/@([a-z0-9._-]+)/gi)].map(x=>x[1]).filter(u=>!m.includes(u)&&app.users().some(x=>x.username===u));if(add.length)app.addMembers(add)});""", "target_only_failure"),
        "prompt-everyone-mutant": (r"""app.onSend(text=>{app.post(text);for(const [,u] of text.matchAll(/@([a-z0-9._-]+)/gi))app.showNotice('Add @'+u+' to the channel?',{label:'Add',run:()=>app.addMembers([u])})});""", "target_only_failure"),
        "non-target-mutant": (r"""app.onSend(text=>{const m=app.members();for(const [,u] of text.matchAll(/@([a-z0-9._-]+)/gi))if(!m.includes(u)&&app.users().some(x=>x.username===u))app.showNotice('@'+u+' is not in the channel. Add them?',{label:'Add them',run:()=>app.addMembers([u])})});""", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement sending a message in the channel. When the user selects Send, post the typed message with "
             "app.post(text). The channel's members are listed by app.members() and all workspace users by "
             "app.users(); app.addMembers(usernames) adds users to the channel, and app.showNotice(text, {label, "
             "run}) shows the sender a notice with one action button that calls run. You can also @mention users "
             "to add them to a channel. If they're not a channel member, Mattermost prompts you to add them.",
        "B": "Selecting Send posts the typed message through app.post(text). app.members() lists the channel's "
             "members and app.users() every user of the workspace; app.addMembers(usernames) puts users into the "
             "channel, and app.showNotice(text, {label, run}) shows the sender a notice whose single action button "
             "calls run. Mentioning people with @ is another way to add them to a channel: when someone you mention "
             "isn't a member of the channel, Mattermost asks you whether to add them.",
        "C": "Implement sending a message in the channel. When the user selects Send, post the typed message with "
             "app.post(text). The channel's members are listed by app.members() and all workspace users by "
             "app.users(); app.addMembers(usernames) adds users to the channel, and app.showNotice(text, {label, "
             "run}) shows the sender a notice with one action button that calls run. You can also @mention users "
             "to add them to a channel.",
    },
}

TEAM_URL = {
    "case": "mattermost-anonymous-team-url",
    "candidate_id": "rc-aa2c82f86e08",
    "project_id": "mattermost",
    "source": {"commit": "840fc4b8f5", "file": "source/end-user-guide/collaborate/organize-using-teams.rst",
               "snapshot": SNAPSHOT, "snapshot_file": "source/end-user-guide/collaborate/organize-using-teams.rst"},
    "title": "Create a team",
    "register": "app.onNext",
    "control": "Next button",
    "body": '<h1>Create a team</h1><section id="name-step"><label>Team name <input id="team-name"></label>'
            '<button id="next" type="button">Next</button></section><section id="url-step" hidden><h2>Team URL</h2>'
            '<label>https://chat.example.com/<input id="team-url"></label><button id="finish" type="button">Finish</button>'
            '</section><p id="message" role="status"></p><h2>Teams</h2><ul id="teams" aria-label="Teams"></ul>',
    "state_js": r"""
let teams=load(window.initialState.teams);
const app=Object.freeze({
  onNext:register,
  config(){return structuredClone(window.initialState.config)},
  teams(){return structuredClone(teams)},
  createTeam(team){if(typeof team!=='object'||team===null||typeof team.name!=='string'||team.name.trim().length<2||team.name.trim().length>64||typeof team.url!=='string'||!team.url)throw new Error('name of 2-64 characters and url required');
    if(teams.some(t=>t.url===team.url))throw new Error('team URL already taken');
    teams.push({name:team.name.trim(),url:team.url});store(teams);document.querySelector('#url-step').hidden=true;render()},
  showUrlStep(url){if(typeof url!=='string')throw new Error('url text required');document.querySelector('#team-url').value=url;document.querySelector('#url-step').hidden=false},
  showMessage(text){document.querySelector('#message').textContent=String(text)}
});
function render(){const list=document.querySelector('#teams');list.replaceChildren();
  for(const t of teams)list.append(el('li',{'data-name':t.name,'data-url':t.url},t.name+' — https://chat.example.com/'+t.url+'/'))}
document.querySelector('#next').addEventListener('click',()=>{if(behavior)behavior({name:document.querySelector('#team-name').value})});
document.querySelector('#finish').addEventListener('click',()=>{try{app.createTeam({name:document.querySelector('#team-name').value,url:document.querySelector('#team-url').value})}catch(e){app.showMessage(e.message)}});
""",
    "fixtures": [
        {"state": {"config": {"anonymousUrls": True, "enableOpenServer": True, "restrictCreationToDomains": ""},
                   "teams": [{"name": "Engineering", "url": "engineering"}]},
         "name": "Release Crew", "url": "release-crew"},
        {"state": {"config": {"anonymousUrls": False, "enableOpenServer": True, "restrictCreationToDomains": ""},
                   "teams": [{"name": "Sales", "url": "sales"}, {"name": "Marketing", "url": "marketing"}]},
         "name": "Support Desk", "url": "help-desk-emea"},
    ],
    "journey_js": r"""
  const n=index+1;const before=fixture.state.teams;
  const teams=()=>page.locator('#teams li').evaluateAll(ns=>ns.map(x=>({name:x.dataset.name,url:x.dataset.url})));
  if(JSON.stringify(await teams())!==JSON.stringify(before)||await page.locator('#url-step').isVisible())throw new InterfaceError('teams changed or URL step open before creating');
  await (await one(page,'#team-name')).fill(fixture.name);await (await one(page,'#next')).click();await page.waitForTimeout(100);
  const prompted=await page.locator('#url-step').isVisible();
  const early=(await teams()).filter(t=>t.name===fixture.name);
  if(prompted){await (await one(page,'#team-url')).fill(fixture.url);await (await one(page,'#finish')).click();await page.waitForTimeout(100)}
  await reload(page);
  const after=await teams();const created=after.filter(t=>t.name===fixture.name);
  const kept=before.every(b=>after.some(t=>t.name===b.name&&t.url===b.url));
  if(fixture.state.config.anonymousUrls){
    check('url_assigned_without_prompt_1',!prompted&&early.length===1&&/^[a-z][a-z0-9-]{0,62}[a-z0-9]$/.test(early[0].url)&&!before.some(b=>b.url===early[0].url));
    check('team_created_once_1',created.length===1);
    check('existing_teams_kept_1',kept);
  }else{
    check('url_step_shown_2',prompted&&early.length===0);
    check('chosen_url_saved_2',created.length===1&&created[0].url===fixture.url);
    check('existing_teams_kept_2',kept);
  }
""",
    "target": ["url_assigned_without_prompt_1"],
    "non_target": ["team_created_once_1", "existing_teams_kept_1", "url_step_shown_2", "chosen_url_saved_2",
                   "existing_teams_kept_2"],
    "controls": {
        "reference": (r"""const slug=s=>s.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'');
app.onNext(f=>{if(f.name.trim().length<2){app.showMessage('Team names must be 2 - 64 characters in length.');return}
if(app.config().anonymousUrls){const taken=app.teams().map(t=>t.url);let url;do{url='t'+Array.from(crypto.getRandomValues(new Uint8Array(15)),b=>(b%36).toString(36)).join('')}while(taken.includes(url));app.createTeam({name:f.name,url});return}
app.showUrlStep(slug(f.name))});""", "pass"),
        "alternative": (r"""app.onNext(function(f){var c=app.config();if(c&&c.anonymousUrls===true){var n=app.teams().length+1,url;do{url='team-'+Math.random().toString(36).slice(2,10)+n}while(app.teams().some(function(t){return t.url===url}));app.createTeam({name:f.name,url:url})}else{app.showUrlStep(f.name.toLowerCase().trim().split(/\s+/).join('-'))}});""", "pass"),
        "target-mutant": (r"""app.onNext(f=>app.showUrlStep(f.name.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'')));""", "target_only_failure"),
        "non-target-mutant": (r"""app.onNext(f=>app.createTeam({name:f.name,url:'t'+Date.now().toString(36)}));""", "non_target_only_failure"),
        "do-nothing-mutant": ("app.onNext(()=>{});", "mixed_failure"),
    },
    "arms": {
        "A": "Implement the Next button of Create a Team. When the user enters a team name and selects Next, handle "
             "the team URL: app.showUrlStep(suggestedUrl) shows the team URL step, whose Finish button creates the "
             "team with the URL the user chose, and app.createTeam({name, url}) creates a team. There are a few "
             "details and restrictions to consider when selecting a team name and team URL. If your system admin "
             "has enabled anonymous team and channel URLs (app.config().anonymousUrls), team creation becomes a "
             "single-step flow and you will not be prompted to choose a team URL. The URL is assigned "
             "automatically. If your system admin has not enabled anonymous URLs, you choose a team URL during team "
             "creation. The team URL is part of the web address that navigates to your team; it may contain only "
             "lowercase letters, numbers, and dashes, must start with a letter, cannot end in a dash, and must be "
             "2 - 64 characters in length.",
        "B": "The Next button of Create a Team deals with the team URL once the user has typed a team name: "
             "app.createTeam({name, url}) makes a team, and app.showUrlStep(suggestedUrl) opens the team URL step, "
             "where Finish creates the team with the URL the user picked. Team names and team URLs come with some "
             "details and restrictions. When the system admin has turned on anonymous team and channel URLs "
             "(app.config().anonymousUrls), creating a team takes a single step: nobody is asked to choose a team "
             "URL, because one is assigned automatically. Without anonymous URLs, the user picks the team URL while "
             "creating the team. The team URL is part of the web address of the team; it uses only lowercase "
             "letters, numbers and dashes, begins with a letter, does not end with a dash and is 2 - 64 characters "
             "long.",
        "C": "Implement the Next button of Create a Team. When the user enters a team name and selects Next, handle "
             "the team URL: app.showUrlStep(suggestedUrl) shows the team URL step, whose Finish button creates the "
             "team with the URL the user chose, and app.createTeam({name, url}) creates a team. There are a few "
             "details and restrictions to consider when selecting a team name and team URL. If your system admin "
             "has not enabled anonymous URLs, you choose a team URL during team "
             "creation. The team URL is part of the web address that navigates to your team; it may contain only "
             "lowercase letters, numbers, and dashes, must start with a letter, cannot end in a dash, and must be "
             "2 - 64 characters in length.",
    },
}

CASES = [PLAYBOOK_MARKDOWN, GUEST_CHANNEL, TIMEZONE_DEFAULT, AUTOTRANSLATE, MENTION_ADD, TEAM_URL]
