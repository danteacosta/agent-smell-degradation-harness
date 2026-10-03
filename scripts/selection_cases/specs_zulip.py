"""Zulip selection cases (six admitted rules; arm A from the starlight_help snapshot)."""

SNAPSHOT = "9778ffc23c"
DOCS = "starlight_help/src/content/docs/"

GIF_PICKER = {
    "case": "zulip-gif-picker-disabled",
    "candidate_id": "rc-08dffa18a270",
    "project_id": "zulip",
    "source": {"commit": "a31cd65175", "file": "starlight_help/src/content/docs/animated-gifs.mdx",
               "snapshot": SNAPSHOT, "snapshot_file": DOCS + "animated-gifs.mdx"},
    "title": "Organization settings",
    "register": "app.onSave",
    "control": "Save changes button",
    "body": '<h1>Organization settings</h1><section aria-label="Compose settings"><h2>Compose settings</h2>'
            '<label>GIF picker <select id="gif-picker"><option value="g">G (General audience)</option>'
            '<option value="pg">PG (Parental guidance)</option><option value="pg13">PG-13 (Parental guidance - under 13)'
            '</option><option value="r">R (Restricted)</option><option value="disabled">Disabled</option></select></label>'
            '<button id="save" type="button">Save changes</button><p id="message" role="status"></p></section>'
            '<p id="stored"></p><section aria-label="Compose box"><h2>Compose box</h2>'
            '<label>Message <textarea id="compose" rows="3" cols="60"></textarea></label><div id="compose-buttons"></div></section>',
    "state_js": r"""
let state=load({settings:window.initialState.settings,composeButtons:window.initialState.composeButtons});
const LABELS={formatting:'Formatting',emoji:'Add emoji',gif:'Add GIF',poll:'Add poll',video:'Add video call'};
const RATINGS=['g','pg','pg13','r','disabled'];
const app=Object.freeze({
  onSave:register,
  settings(){return structuredClone(state.settings)},
  composeButtons(){return [...state.composeButtons]},
  saveSettings(change){if(typeof change!=='object'||change===null||!RATINGS.includes(change.gifRating))throw new Error('gifRating must be one of '+RATINGS.join(', '));
    state.settings={...state.settings,gifRating:change.gifRating};store(state);render()},
  setComposeButtons(list){if(!Array.isArray(list)||!list.every(b=>b in LABELS)||new Set(list).size!==list.length)throw new Error('known compose buttons required');
    state.composeButtons=[...list];store(state);render()},
  showMessage(text){document.querySelector('#message').textContent=String(text)}
});
function render(){
  const s=document.querySelector('#stored');s.dataset.gifRating=state.settings.gifRating;
  s.textContent='Saved GIF picker setting: '+document.querySelector('#gif-picker option[value="'+state.settings.gifRating+'"]').textContent;
  const box=document.querySelector('#compose-buttons');box.replaceChildren();
  for(const b of state.composeButtons)box.append(el('button',{type:'button','data-button':b},LABELS[b]));
}
document.querySelector('#gif-picker').value=state.settings.gifRating;
document.querySelector('#save').addEventListener('click',()=>{if(behavior)behavior({gifRating:document.querySelector('#gif-picker').value})});
""",
    "fixtures": [
        {"state": {"settings": {"gifRating": "g"}, "composeButtons": ["formatting", "emoji", "gif", "poll", "video"]},
         "rating": "r"},
        {"state": {"settings": {"gifRating": "pg13"}, "composeButtons": ["formatting", "gif", "emoji", "poll"]},
         "rating": "pg"},
    ],
    "journey_js": r"""
  const n=index+1;const stored=()=>page.locator('#stored').evaluate(x=>x.dataset.gifRating);
  const buttons=()=>page.locator('#compose-buttons [data-button]').evaluateAll(ns=>ns.map(x=>x.dataset.button));
  const b0=fixture.state.composeButtons;
  if(await stored()!==fixture.state.settings.gifRating||JSON.stringify(await buttons())!==JSON.stringify(b0))throw new InterfaceError('settings or compose box changed before saving');
  async function save(value){await (await one(page,'#gif-picker')).selectOption(value);await (await one(page,'#save')).click();await reload(page)}
  if(n===1){
    await save(fixture.rating);
    check('rating_saved_1',await stored()===fixture.rating);
    check('picker_kept_when_rated_1',(await buttons()).includes('gif'));
  }
  await save('disabled');
  const after=await buttons();
  check(`picker_removed_when_disabled_${n}`,!after.includes('gif'));
  check(`disabled_saved_${n}`,await stored()==='disabled');
  check(`other_buttons_kept_${n}`,JSON.stringify(after.filter(b=>b!=='gif'))===JSON.stringify(b0.filter(b=>b!=='gif')));
  if(n===2){await save(fixture.rating);check('rating_saved_2',await stored()===fixture.rating)}
""",
    "target": ["picker_removed_when_disabled_1", "picker_removed_when_disabled_2"],
    "non_target": ["rating_saved_1", "picker_kept_when_rated_1", "disabled_saved_1", "other_buttons_kept_1",
                   "disabled_saved_2", "other_buttons_kept_2", "rating_saved_2"],
    "controls": {
        "reference": ("app.onSave(f=>{app.saveSettings(f);const b=app.composeButtons();if(f.gifRating==='disabled')app.setComposeButtons(b.filter(x=>x!=='gif'));else if(!b.includes('gif'))app.setComposeButtons([...b,'gif'])});", "pass"),
        "alternative": ("app.onSave(function(f){app.setComposeButtons(app.composeButtons().filter(function(b){return b!=='gif'||f.gifRating!=='disabled'}));app.saveSettings({gifRating:f.gifRating});app.showMessage('Saved')});", "pass"),
        "target-mutant": ("app.onSave(f=>app.saveSettings(f));", "target_only_failure"),
        "non-target-mutant": ("app.onSave(f=>{if(f.gifRating==='disabled')app.setComposeButtons(app.composeButtons().filter(b=>b!=='gif'))});", "non_target_only_failure"),
        "always-remove-mutant": ("app.onSave(f=>{app.saveSettings(f);app.setComposeButtons(app.composeButtons().filter(b=>b!=='gif'))});", "non_target_only_failure"),
        "clear-toolbar-mutant": ("app.onSave(f=>{app.saveSettings(f);if(f.gifRating==='disabled')app.setComposeButtons([])});", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement saving the organization's Compose settings. When the user clicks Save changes, store the "
             "selected GIF picker setting with app.saveSettings({gifRating}); the buttons at the bottom of the compose "
             "box are listed by app.composeButtons() and changed with app.setComposeButtons(list). Users insert a GIF by "
             "clicking the add GIF button (gif) at the bottom of the compose box. You can configure the maximum rating "
             "of GIFs shown in the GIF picker, which by default is set to GIFs rated G (General audience): under "
             "Compose settings, select a rating for GIF picker. Disabling the GIF picker removes it from the compose "
             "box. To disable the GIF picker, under Compose settings, set GIF picker to Disabled.",
        "B": "Clicking Save changes stores the GIF picker choice made under Compose settings through "
             "app.saveSettings({gifRating}). The buttons along the bottom of the compose box come from "
             "app.composeButtons() and are replaced with app.setComposeButtons(list); the add GIF button (gif) there "
             "is how users insert a GIF. Under Compose settings, GIF picker sets the highest rating of GIFs the picker "
             "shows, G (General audience) unless changed. Choosing Disabled for GIF picker turns the GIF picker off, "
             "and a disabled GIF picker is no longer part of the compose box.",
        "C": "Implement saving the organization's Compose settings. When the user clicks Save changes, store the "
             "selected GIF picker setting with app.saveSettings({gifRating}); the buttons at the bottom of the compose "
             "box are listed by app.composeButtons() and changed with app.setComposeButtons(list). Users insert a GIF by "
             "clicking the add GIF button (gif) at the bottom of the compose box. You can configure the maximum rating "
             "of GIFs shown in the GIF picker, which by default is set to GIFs rated G (General audience): under "
             "Compose settings, select a rating for GIF picker. To disable the GIF picker, under Compose settings, set "
             "GIF picker to Disabled.",
    },
}

RESOLVED_NOTICES = {
    "case": "zulip-resolved-notice-auto-read",
    "candidate_id": "rc-362ff82e3812",
    "project_id": "zulip",
    "source": {"commit": "a11cc9a46e", "file": "help/configure-automated-notices.md",
               "snapshot": SNAPSHOT, "snapshot_file": DOCS + "configure-automated-notices.mdx",
               "snapshot_context": ["starlight_help/src/content/include/_ConfigureResolvedNoticesMarkedAsRead.mdx"]},
    "title": "Topics",
    "register": "app.onResolve",
    "control": "Resolve topic / Unresolve topic buttons",
    "body": '<h1>Topics</h1><section id="settings" aria-label="Settings"><h2>Settings</h2>'
            '<label>Mark messages as read on scroll <select id="read-on-scroll"><option value="always">Always</option>'
            '<option value="conversation">Only in conversation views</option><option value="never">Never</option>'
            '</select></label></section><h2>Channel #support</h2><ul id="topics" aria-label="Topics"></ul>'
            '<h2>Messages</h2><ul id="messages" aria-label="Messages"></ul><p id="message" role="status"></p>',
    "state_js": r"""
let state=load(window.initialState);
const app=Object.freeze({
  onResolve:register,
  user(){return structuredClone(state.user)},
  topics(){return structuredClone(state.topics)},
  messages(){return structuredClone(state.messages)},
  setting(name){return name in state.settings?structuredClone(state.settings[name]):undefined},
  saveSetting(name,value){if(typeof name!=='string'||!name)throw new Error('setting name required');state.settings[name]=structuredClone(value);store(state)},
  setResolved(topicId,resolved){const t=state.topics.find(x=>x.id===topicId);if(!t||typeof resolved!=='boolean')throw new Error('known topic and boolean required');t.resolved=resolved;store(state);render()},
  sendNotice(topicId,content){if(!state.topics.some(x=>x.id===topicId)||typeof content!=='string'||!content.trim())throw new Error('known topic and content required');
    const id=Math.max(0,...state.messages.map(m=>m.id))+1;state.messages.push({id,topic:topicId,sender:'Notification Bot',content,read:false});store(state);render();return id},
  markAsRead(id){const m=state.messages.find(x=>x.id===id);if(!m)throw new Error('unknown message');m.read=true;store(state);render()},
  showMessage(text){document.querySelector('#message').textContent=String(text)}
});
function render(){
  const topics=document.querySelector('#topics');topics.replaceChildren();
  for(const t of state.topics){const li=el('li',{'data-id':t.id,'data-resolved':t.resolved},(t.resolved?'✔ ':'')+t.name+' ');
    li.append(el('button',{type:'button','data-topic':t.id},t.resolved?'Unresolve topic':'Resolve topic'));topics.append(li)}
  const list=document.querySelector('#messages');list.replaceChildren();
  for(const m of state.messages){const t=state.topics.find(x=>x.id===m.topic);
    list.append(el('li',{'data-id':m.id,'data-topic':m.topic,'data-sender':m.sender,'data-read':m.read},(m.read?'':'● ')+t.name+' — '+m.sender+': '+m.content))}
}
const scroll=document.querySelector('#read-on-scroll');scroll.value=state.settings.readOnScroll;
scroll.addEventListener('change',()=>{state.settings.readOnScroll=scroll.value;store(state)});
document.querySelector('#topics').addEventListener('click',e=>{const b=e.target.closest('button[data-topic]');if(b&&behavior)behavior(app.topics().find(t=>t.id===b.dataset.topic))});
""",
    "fixtures": [
        {"state": {"user": {"id": 7, "name": "Lena"}, "settings": {"readOnScroll": "always"},
                   "topics": [{"id": "t1", "name": "login page down", "resolved": False},
                              {"id": "t2", "name": "invoice export", "resolved": False}],
                   "messages": [{"id": 1, "topic": "t1", "sender": "Omar", "content": "Login returns 502.", "read": True},
                                {"id": 2, "topic": "t2", "sender": "Ana", "content": "CSV export is empty.", "read": False}]},
         "steps": [["t1", True], ["t1", False]]},
        {"state": {"user": {"id": 9, "name": "Rui"}, "settings": {"readOnScroll": "conversation"},
                   "topics": [{"id": "t3", "name": "build flaky", "resolved": False},
                              {"id": "t4", "name": "printer offline", "resolved": True},
                              {"id": "t5", "name": "vpn access", "resolved": False}],
                   "messages": [{"id": 11, "topic": "t3", "sender": "Kim", "content": "Test 14 fails at random.", "read": False},
                                {"id": 12, "topic": "t4", "sender": "Notification Bot", "content": "@Kim has marked this topic as resolved.", "read": True},
                                {"id": 13, "topic": "t5", "sender": "Ivo", "content": "Who can grant VPN access?", "read": True}]},
         "steps": [["t3", False], ["t4", True]]},
    ],
    "journey_js": r"""
  const n=index+1;
  const msgs=()=>page.locator('#messages li').evaluateAll(ns=>ns.map(x=>({id:x.dataset.id,topic:x.dataset.topic,sender:x.dataset.sender,read:x.dataset.read})));
  const topics=()=>page.locator('#topics li').evaluateAll(ns=>Object.fromEntries(ns.map(x=>[x.dataset.id,x.dataset.resolved])));
  const init=await msgs();
  if(JSON.stringify(init.map(m=>[m.id,m.read]))!==JSON.stringify(fixture.state.messages.map(m=>[String(m.id),String(m.read)])))throw new InterfaceError('messages missing or changed before acting');
  async function setOption(on){
    const c=page.getByLabel(/mark resolved topic notices as read/i);
    if(await c.count()!==1||!await c.isVisible()||!await c.isEnabled())return false;
    const kind=await c.evaluate(x=>x.tagName+':'+(x.type||''));
    if(kind==='INPUT:checkbox'){await c.setChecked(on);return true}
    if(kind.startsWith('SELECT')){
      const opts=await c.locator('option').evaluateAll(os=>os.map(o=>[o.value,o.textContent.trim()]));
      const re=on?/^(always|yes|on|enabled?|true)$/i:/^(never|no|off|disabled?|false)$/i;
      const o=opts.find(([v,t])=>re.test(t)||re.test(v));if(!o)return false;await c.selectOption(o[0]);return true}
    return false}
  const seen=new Set(init.map(m=>m.id));let readOk=true,unreadOk=true,posted=true,toggled=true;
  for(const [topic,on] of fixture.steps){
    const before=(await topics())[topic];
    const set=await setOption(on);
    await (await one(page,`#topics button[data-topic="${topic}"]`)).click();await page.waitForTimeout(100);await reload(page);
    const now=(await topics())[topic];
    const fresh=(await msgs()).filter(m=>!seen.has(m.id));fresh.forEach(m=>seen.add(m.id));
    const notices=fresh.filter(m=>m.topic===topic&&m.sender==='Notification Bot');
    posted=posted&&fresh.length===1&&notices.length===1;
    toggled=toggled&&now===String(before!=='true');
    if(on)readOk=readOk&&set&&notices.every(m=>m.read==='true');
    else unreadOk=unreadOk&&set&&notices.every(m=>m.read==='false');
  }
  const final=await msgs();
  check(`notice_read_when_enabled_${n}`,readOk);
  check(`notice_unread_when_disabled_${n}`,unreadOk);
  check(`notice_posted_for_each_change_${n}`,posted);
  check(`topic_state_toggled_${n}`,toggled);
  check(`other_messages_unchanged_${n}`,init.every(m=>final.some(f=>f.id===m.id&&f.read===m.read)));
""",
    "target": ["notice_read_when_enabled_1", "notice_unread_when_disabled_1",
               "notice_read_when_enabled_2", "notice_unread_when_disabled_2"],
    "non_target": ["notice_posted_for_each_change_1", "topic_state_toggled_1", "other_messages_unchanged_1",
                   "notice_posted_for_each_change_2", "topic_state_toggled_2", "other_messages_unchanged_2"],
    "controls": {
        "reference": ("const box=el('input',{type:'checkbox',id:'auto-read-resolved'});box.checked=app.setting('autoReadResolvedNotices')===true;const label=el('label');label.append(box,' Automatically mark resolved topic notices as read');document.querySelector('#settings').append(label);box.addEventListener('change',()=>app.saveSetting('autoReadResolvedNotices',box.checked));app.onResolve(t=>{const r=!t.resolved;app.setResolved(t.id,r);const id=app.sendNotice(t.id,'@'+app.user().name+' has marked this topic as '+(r?'resolved':'unresolved')+'.');if(app.setting('autoReadResolvedNotices')===true)app.markAsRead(id)});", "pass"),
        "alternative-select": ("var s=el('select',{id:'resolved-read'});[['always','Always'],['except_followed','Except for topics I follow'],['never','Never']].forEach(function(o){s.append(el('option',{value:o[0]},o[1]))});s.value=app.setting('resolvedNoticesRead')||'never';var l=el('label',{},'Automatically mark resolved topic notices as read ');l.append(s);document.querySelector('#settings').append(l);s.addEventListener('change',function(){app.saveSetting('resolvedNoticesRead',s.value)});app.onResolve(function(t){app.setResolved(t.id,!t.resolved);var id=app.sendNotice(t.id,'Topic '+(t.resolved?'unresolved':'resolved')+'.');if(app.setting('resolvedNoticesRead')==='always')app.markAsRead(id)});", "pass"),
        "target-mutant": ("app.onResolve(t=>{const r=!t.resolved;app.setResolved(t.id,r);app.sendNotice(t.id,'@'+app.user().name+' has marked this topic as '+(r?'resolved':'unresolved')+'.')});", "target_only_failure"),
        "always-read-mutant": ("app.onResolve(t=>{app.setResolved(t.id,!t.resolved);app.markAsRead(app.sendNotice(t.id,'Topic status changed.'))});", "target_only_failure"),
        "ignored-setting-mutant": ("const box=el('input',{type:'checkbox'});const label=el('label');label.append(box,' Automatically mark resolved topic notices as read');document.querySelector('#settings').append(label);app.onResolve(t=>{app.setResolved(t.id,!t.resolved);app.sendNotice(t.id,'Topic status changed.')});", "target_only_failure"),
        "non-target-mutant": ("const box=el('input',{type:'checkbox'});box.checked=app.setting('autoRead')===true;const label=el('label');label.append(box,' Automatically mark resolved topic notices as read');document.querySelector('#settings').append(label);box.addEventListener('change',()=>app.saveSetting('autoRead',box.checked));app.onResolve(t=>app.setResolved(t.id,!t.resolved));", "non_target_only_failure"),
        "mark-everything-mutant": ("const box=el('input',{type:'checkbox'});box.checked=app.setting('autoRead')===true;const label=el('label');label.append(box,' Automatically mark resolved topic notices as read');document.querySelector('#settings').append(label);box.addEventListener('change',()=>app.saveSetting('autoRead',box.checked));app.onResolve(t=>{app.setResolved(t.id,!t.resolved);app.sendNotice(t.id,'Topic status changed.');if(app.setting('autoRead'))app.messages().forEach(m=>{if(!m.read)app.markAsRead(m.id)})});", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement resolving topics. When the user clicks a topic's Resolve topic or Unresolve topic button, mark "
             "the topic as resolved or unresolved with app.setResolved(topicId, resolved). A notice is sent by "
             "Notification Bot when a topic is resolved or unresolved: post it with app.sendNotice(topicId, content), "
             "which returns the new message's id. Messages stay unread until app.markAsRead(id) is called; the "
             "signed-in user is app.user(), and user settings are read with app.setting(name) and stored with "
             "app.saveSetting(name, value). Users can configure whether these notices are automatically marked as "
             "read, with an \"Automatically mark resolved topic notices as read\" setting that you add to the page's "
             "Settings section.",
        "B": "Every topic has a Resolve topic or Unresolve topic button, and clicking it changes the topic's state "
             "through app.setResolved(topicId, resolved). Whenever a topic is resolved or unresolved, Notification Bot "
             "posts a notice, created with app.sendNotice(topicId, content), which gives back the id of the new "
             "message. A message only becomes read through app.markAsRead(id); app.user() is the signed-in user, and "
             "app.setting(name) and app.saveSetting(name, value) read and store user settings. Each user decides "
             "whether these notices get marked as read automatically: add an \"Automatically mark resolved topic "
             "notices as read\" setting to the Settings section of the page for this choice.",
        "C": "Implement resolving topics. When the user clicks a topic's Resolve topic or Unresolve topic button, mark "
             "the topic as resolved or unresolved with app.setResolved(topicId, resolved). A notice is sent by "
             "Notification Bot when a topic is resolved or unresolved: post it with app.sendNotice(topicId, content), "
             "which returns the new message's id. Messages stay unread until app.markAsRead(id) is called; the "
             "signed-in user is app.user(), and user settings are read with app.setting(name) and stored with "
             "app.saveSetting(name, value).",
    },
}

REVERSE_LINKIFIER = {
    "case": "zulip-reverse-linkifier-paste",
    "candidate_id": "rc-4200f1dac6a9",
    "project_id": "zulip",
    "source": {"commit": "3ca12e7224", "file": "starlight_help/src/content/docs/add-a-custom-linkifier.mdx",
               "snapshot": SNAPSHOT, "snapshot_file": DOCS + "add-a-custom-linkifier.mdx"},
    "title": "Compose",
    "register": "app.onSend",
    "control": "Send button",
    "body": '<h1>Compose</h1><section aria-label="Linkifiers"><h2>Linkifiers</h2><table id="linkifiers"><thead><tr>'
            '<th>Pattern</th><th>URL template</th></tr></thead><tbody></tbody></table></section>'
            '<label>Message <textarea id="compose" rows="3" cols="70"></textarea></label>'
            '<button id="send" type="button">Send</button><h2>Messages</h2><ul id="messages" aria-label="Messages"></ul>',
    "state_js": r"""
let messages=load([]);
const linkifiers=window.initialState.linkifiers;
const app=Object.freeze({
  onSend:register,
  linkifiers(){return structuredClone(linkifiers)},
  messages(){return structuredClone(messages)},
  sendMessage(parts){if(!Array.isArray(parts)||!parts.length||!parts.every(p=>p&&typeof p.text==='string'&&(p.href===undefined||/^https?:\/\//.test(p.href))))throw new Error('parts must be {text} or {text, href} pieces');
    messages.push(parts.map(p=>p.href===undefined?{text:p.text}:{text:p.text,href:p.href}));store(messages);document.querySelector('#compose').value='';render()}
});
function render(){
  const body=document.querySelector('#linkifiers tbody');body.replaceChildren();
  for(const l of linkifiers){const tr=el('tr');tr.append(el('td',{},l.pattern),el('td',{},l.urlTemplate));body.append(tr)}
  const list=document.querySelector('#messages');list.replaceChildren();
  for(const parts of messages){const li=el('li');
    for(const p of parts)li.append(p.href===undefined?document.createTextNode(p.text):el('a',{href:p.href,'data-href':p.href},p.text));
    list.append(li)}
}
document.querySelector('#send').addEventListener('click',()=>{if(behavior)behavior(document.querySelector('#compose').value)});
""",
    "fixtures": [
        {"state": {"linkifiers": [
            {"pattern": "#(?<id>[0-9]+)", "urlTemplate": "https://github.com/zulip/zulip/issues/{id}", "linkText": "#{id}"},
            {"pattern": "RT(?<id>[0-9]+)", "urlTemplate": "https://rt.example.org/Ticket/Display.html?id={id}", "linkText": None}]},
         "messages": [
             {"typed": "Fixed in ", "paste": "https://github.com/zulip/zulip/issues/2468", "expect": "Fixed in #2468", "kind": "converted"},
             {"typed": "Ticket: ", "paste": "https://rt.example.org/Ticket/Display.html?id=77",
              "expect": "Ticket: https://rt.example.org/Ticket/Display.html?id=77", "kind": "unmatched"},
             {"typed": "See #1357 and RT42", "paste": None, "expect": "See #1357 and RT42", "kind": "typed",
              "links": [["#1357", "https://github.com/zulip/zulip/issues/1357"],
                        ["RT42", "https://rt.example.org/Ticket/Display.html?id=42"]]}]},
        {"state": {"linkifiers": [
            {"pattern": "#F(?<id>[0-9]+)", "urlTemplate": "https://github.com/zulip/zulip-flutter/issues/{id}", "linkText": "#F{id}"},
            {"pattern": "(?<org>[a-zA-Z0-9_-]+)/(?<repo>[a-zA-Z0-9_-]+)#(?<id>[0-9]+)",
             "urlTemplate": "https://github.com/{org}/{repo}/pull/{id}", "linkText": "{org}/{repo}#{id}"},
            {"pattern": "CASE-(?<id>[0-9]+)", "urlTemplate": "https://support.example.com/cases/{id}", "linkText": None}]},
         "messages": [
             {"typed": "Merged as ", "paste": "https://github.com/django/django/pull/123", "expect": "Merged as django/django#123", "kind": "converted"},
             {"typed": "Tracked in ", "paste": "https://github.com/zulip/zulip-flutter/issues/245", "expect": "Tracked in #F245", "kind": "converted"},
             {"typed": "Customer report: ", "paste": "https://support.example.com/cases/5150",
              "expect": "Customer report: https://support.example.com/cases/5150", "kind": "unmatched"},
             {"typed": "Duplicate of #F12, see CASE-9", "paste": None, "expect": "Duplicate of #F12, see CASE-9", "kind": "typed",
              "links": [["#F12", "https://github.com/zulip/zulip-flutter/issues/12"],
                        ["CASE-9", "https://support.example.com/cases/9"]]}]},
    ],
    "journey_js": r"""
  const n=index+1;
  const read=()=>page.locator('#messages li').evaluateAll(ns=>ns.map(li=>({text:li.textContent,links:[...li.querySelectorAll('a')].map(a=>[a.textContent,a.dataset.href])})));
  if((await read()).length!==0)throw new InterfaceError('messages present before sending');
  async function paste(text){
    await page.locator('#compose').evaluate((box,t)=>{box.focus();box.setSelectionRange(box.value.length,box.value.length);
      const data=new DataTransfer();data.setData('text/plain',t);
      const event=new ClipboardEvent('paste',{clipboardData:data,bubbles:true,cancelable:true});
      if(box.dispatchEvent(event)){box.setRangeText(t,box.selectionStart,box.selectionEnd,'end');box.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertFromPaste',data:t}))}},text);
    await page.waitForTimeout(150)}
  for(const m of fixture.messages){
    await (await one(page,'#compose')).fill(m.typed);
    if(m.paste)await paste(m.paste);
    await (await one(page,'#send')).click();await page.waitForTimeout(100);
  }
  await reload(page);
  const got=await read();const at=i=>got[i]||{text:null,links:[]};
  const idx=kind=>fixture.messages.map((m,i)=>m.kind===kind?i:-1).filter(i=>i>=0);
  check(`pasted_url_converted_${n}`,idx('converted').every(i=>at(i).text===fixture.messages[i].expect));
  check(`unmatched_paste_kept_${n}`,idx('unmatched').every(i=>at(i).text===fixture.messages[i].expect));
  check(`typed_reference_linked_${n}`,idx('typed').every(i=>at(i).text===fixture.messages[i].expect&&JSON.stringify(at(i).links)===JSON.stringify(fixture.messages[i].links)));
  check(`one_message_per_send_${n}`,got.length===fixture.messages.length);
""",
    "target": ["pasted_url_converted_1", "unmatched_paste_kept_1", "pasted_url_converted_2", "unmatched_paste_kept_2"],
    "non_target": ["typed_reference_linked_1", "one_message_per_send_1", "typed_reference_linked_2", "one_message_per_send_2"],
    "controls": {
        "reference": (r"""const LK=app.linkifiers();const esc=s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');const fill=(t,g)=>t.replace(/\{(\w+)\}/g,(_,k)=>g[k]);
const REV=LK.filter(l=>l.linkText).map(l=>{const names=[];const src='^'+l.urlTemplate.split(/(\{\w+\})/).map(p=>{const m=/^\{(\w+)\}$/.exec(p);if(m){names.push(m[1]);return '([^/?#&]+)'}return esc(p)}).join('')+'$';return {re:new RegExp(src),names,l}});
document.querySelector('#compose').addEventListener('paste',e=>{const t=(e.clipboardData.getData('text/plain')||'').trim();for(const r of REV){const m=r.re.exec(t);if(m){e.preventDefault();const g={};r.names.forEach((k,i)=>g[k]=decodeURIComponent(m[i+1]));const box=e.target;box.setRangeText(fill(r.l.linkText,g),box.selectionStart,box.selectionEnd,'end');return}}});
app.onSend(text=>{const parts=[];let i=0;const rules=LK.map(l=>({re:new RegExp(l.pattern,'g'),l}));while(i<text.length){let best=null;for(const r of rules){r.re.lastIndex=i;const m=r.re.exec(text);if(m&&m[0]&&(!best||m.index<best.m.index))best={m,l:r.l}}if(!best){parts.push({text:text.slice(i)});break}if(best.m.index>i)parts.push({text:text.slice(i,best.m.index)});const g={};for(const [k,v] of Object.entries(best.m.groups||{}))g[k]=encodeURIComponent(v);parts.push({text:best.m[0],href:fill(best.l.urlTemplate,g)});i=best.m.index+best.m[0].length}if(parts.length)app.sendMessage(parts)});""", "pass"),
        "convert-on-send": (r"""function linkify(text){var LK=app.linkifiers(),parts=[],i=0;while(i<text.length){var best=null,bl=null;LK.forEach(function(l){var re=new RegExp(l.pattern,'g');re.lastIndex=i;var m=re.exec(text);if(m&&m[0]&&(!best||m.index<best.index)){best=m;bl=l}});if(!best){parts.push({text:text.slice(i)});break}if(best.index>i)parts.push({text:text.slice(i,best.index)});parts.push({text:best[0],href:bl.urlTemplate.replace(/\{(\w+)\}/g,function(_,k){return encodeURIComponent(best.groups[k])})});i=best.index+best[0].length}return parts}
function reverse(text){return text.replace(/https?:\/\/\S+/g,function(url){var out=url;app.linkifiers().some(function(l){if(!l.linkText)return false;var names=[];var src=l.urlTemplate.replace(/[.*+?^$()|[\]\\]/g,'\\$&').replace(/\{(\w+)\}/g,function(_,k){names.push(k);return '([^/?#&]+)'});var m=new RegExp('^'+src+'$').exec(url);if(!m)return false;out=l.linkText.replace(/\{(\w+)\}/g,function(_,k){return m[names.indexOf(k)+1]});return true});return out})}
app.onSend(function(text){if(text.trim())app.sendMessage(linkify(reverse(text)))});""", "pass"),
        "input-event": (r"""const LK=app.linkifiers();function rev(url){for(const l of LK){if(!l.linkText)continue;const names=[];const src=l.urlTemplate.replace(/[.*+?^$()|[\]\\]/g,'\\$&').replace(/\{(\w+)\}/g,(_,k)=>{names.push(k);return '([^/?#&]+)'});const m=new RegExp('^'+src+'$').exec(url);if(m)return l.linkText.replace(/\{(\w+)\}/g,(_,k)=>m[names.indexOf(k)+1])}return null}
document.querySelector('#compose').addEventListener('input',e=>{if(e.inputType!=='insertFromPaste')return;const box=e.target;box.value=box.value.replace(/https?:\/\/\S+/g,u=>rev(u)??u)});
app.onSend(text=>{const parts=[];let rest=text;while(rest){let best=null;for(const l of LK){const m=new RegExp(l.pattern).exec(rest);if(m&&m[0]&&(!best||m.index<best.m.index))best={m,l}}if(!best){parts.push({text:rest});break}if(best.m.index)parts.push({text:rest.slice(0,best.m.index)});parts.push({text:best.m[0],href:best.l.urlTemplate.replace(/\{(\w+)\}/g,(_,k)=>encodeURIComponent(best.m.groups[k]))});rest=rest.slice(best.m.index+best.m[0].length)}app.sendMessage(parts)});""", "pass"),
        "target-mutant": (r"""const LK=app.linkifiers();app.onSend(text=>{const parts=[];let rest=text;while(rest){let best=null;for(const l of LK){const m=new RegExp(l.pattern).exec(rest);if(m&&m[0]&&(!best||m.index<best.m.index))best={m,l}}if(!best){parts.push({text:rest});break}if(best.m.index)parts.push({text:rest.slice(0,best.m.index)});parts.push({text:best.m[0],href:best.l.urlTemplate.replace(/\{(\w+)\}/g,(_,k)=>encodeURIComponent(best.m.groups[k]))});rest=rest.slice(best.m.index+best.m[0].length)}app.sendMessage(parts)});""", "target_only_failure"),
        "non-target-mutant": (r"""const LK=app.linkifiers();function rev(url){for(const l of LK){if(!l.linkText)continue;const names=[];const src=l.urlTemplate.replace(/[.*+?^$()|[\]\\]/g,'\\$&').replace(/\{(\w+)\}/g,(_,k)=>{names.push(k);return '([^/?#&]+)'});const m=new RegExp('^'+src+'$').exec(url);if(m)return l.linkText.replace(/\{(\w+)\}/g,(_,k)=>m[names.indexOf(k)+1])}return null}
document.querySelector('#compose').addEventListener('paste',e=>{const t=e.clipboardData.getData('text/plain').trim();const r=rev(t);if(r!==null){e.preventDefault();e.target.setRangeText(r,e.target.selectionStart,e.target.selectionEnd,'end')}});
app.onSend(text=>app.sendMessage([{text}]));""", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement sending a message from the compose box. When the user clicks Send, send the composed text with "
             "app.sendMessage(parts), where parts is a list of {text} and {text, href} pieces; the organization's "
             "linkifiers come from app.linkifiers(), each with a pattern (a JavaScript regular expression with named "
             "groups), a urlTemplate and a linkText (null when not set). Linkifiers make it easy to refer to issues or "
             "tickets in third party issue trackers, like GitHub, Salesforce, Zendesk, and others. For instance, you "
             "can add a linkifier that automatically turns #2468 into a link to "
             "https://github.com/zulip/zulip/issues/2468. You can configure linkifiers to work in reverse as well: "
             "when you paste a URL that matches the linkifier's urlTemplate into the compose box, Zulip will "
             "automatically convert it to linked text given by the linkifier's linkText (e.g., "
             "https://github.com/zulip/zulip/issues/2468 becomes #2468).",
        "B": "Clicking Send sends what was written in the compose box through app.sendMessage(parts), with parts being "
             "a list of {text} and {text, href} pieces. app.linkifiers() returns the organization's linkifiers, each "
             "having a pattern (JavaScript regular expression with named groups), a urlTemplate and a linkText (null "
             "if unset). Linkifiers are a convenient way to mention issues or tickets kept in outside trackers such as "
             "GitHub, Salesforce or Zendesk: a linkifier can, for example, make #2468 a link to "
             "https://github.com/zulip/zulip/issues/2468 on its own. They also work the other way around: a URL "
             "pasted into the compose box that matches a linkifier's urlTemplate is turned by Zulip into that "
             "linkifier's linked text from linkText, so pasting https://github.com/zulip/zulip/issues/2468 gives #2468.",
        "C": "Implement sending a message from the compose box. When the user clicks Send, send the composed text with "
             "app.sendMessage(parts), where parts is a list of {text} and {text, href} pieces; the organization's "
             "linkifiers come from app.linkifiers(), each with a pattern (a JavaScript regular expression with named "
             "groups), a urlTemplate and a linkText (null when not set). Linkifiers make it easy to refer to issues or "
             "tickets in third party issue trackers, like GitHub, Salesforce, Zendesk, and others. For instance, you "
             "can add a linkifier that automatically turns #2468 into a link to "
             "https://github.com/zulip/zulip/issues/2468.",
    },
}

SUBSCRIBE_TYPEAHEAD = {
    "case": "zulip-subscribe-typeahead",
    "candidate_id": "rc-c044ebec7fe1",
    "project_id": "zulip",
    "source": {"commit": "94c98c5749", "file": "help/include/subscribe-user-to-channel.md",
               "snapshot": SNAPSHOT, "snapshot_file": "starlight_help/src/content/include/_SubscribeUserToChannel.mdx"},
    "title": "Channel settings",
    "register": "app.onInput",
    "control": "Name or email field",
    "body": '<h1>Channel settings</h1><h2 id="channel"></h2><section aria-label="Subscribers"><h3>Subscribers</h3>'
            '<ul id="subscribers"></ul></section><section aria-label="Add subscribers"><h3>Add subscribers</h3>'
            '<label>Name or email <input id="add-subscriber" autocomplete="off"></label>'
            '<ul id="typeahead" role="listbox" aria-label="Suggestions"></ul>'
            '<button id="add" type="button">Add</button></section>',
    "state_js": r"""
let state=load({subscribers:window.initialState.subscribers});
const users=window.initialState.users;let suggestions=[];let selected=null;
const app=Object.freeze({
  onInput:register,
  users(){return structuredClone(users)},
  subscribers(){return [...state.subscribers]},
  showSuggestions(ids){if(!Array.isArray(ids)||!ids.every(id=>users.some(u=>u.id===id)))throw new Error('user ids required');suggestions=[...ids];render()}
});
function render(){
  document.querySelector('#channel').textContent='#'+window.initialState.channel;
  const subs=document.querySelector('#subscribers');subs.replaceChildren();
  for(const id of state.subscribers){const u=users.find(x=>x.id===id);subs.append(el('li',{'data-id':id},u.name+' <'+u.email+'>'))}
  const list=document.querySelector('#typeahead');list.replaceChildren();
  for(const id of suggestions){const u=users.find(x=>x.id===id);list.append(el('li',{'data-id':id,role:'option',tabindex:'0'},u.name+' <'+u.email+'>'))}
}
const input=document.querySelector('#add-subscriber');
input.addEventListener('input',()=>{selected=null;if(behavior)behavior(input.value)});
document.querySelector('#typeahead').addEventListener('click',e=>{const li=e.target.closest('li[data-id]');if(!li)return;selected=li.dataset.id;input.value=users.find(u=>u.id===selected).name;suggestions=[];render()});
document.querySelector('#add').addEventListener('click',()=>{if(selected){state.subscribers.push(selected);store(state)}selected=null;input.value='';suggestions=[];render()});
""",
    "fixtures": [
        {"state": {"channel": "design", "subscribers": ["u1", "u4"], "users": [
            {"id": "u1", "name": "Anna Lee", "email": "anna@example.com"},
            {"id": "u2", "name": "Andrés Silva", "email": "andres@example.com"},
            {"id": "u3", "name": "Bo Andersen", "email": "bo@example.com"},
            {"id": "u4", "name": "Carl Smith", "email": "carl@example.com"},
            {"id": "u5", "name": "Mei Wong", "email": "mei@example.com"}]},
         "before": [["an", ["u2", "u3"], ["u1"]], ["mei@", ["u5"], []], ["carl", [], ["u4"]]],
         "add": ["an", "u2"],
         "after": [["an", ["u3"], ["u1", "u2"]]]},
        {"state": {"channel": "support", "subscribers": ["v1", "v4"], "users": [
            {"id": "v1", "name": "Priya Shah", "email": "priya@corp.test"},
            {"id": "v2", "name": "Priya Nair", "email": "pnair@corp.test"},
            {"id": "v3", "name": "Sam Price", "email": "sprice@corp.test"},
            {"id": "v4", "name": "Lee Wong", "email": "lwong@corp.test"},
            {"id": "v5", "name": "Leela Rao", "email": "leela@corp.test"}]},
         "before": [["pri", ["v2", "v3"], ["v1"]], ["pnair", ["v2"], []], ["le", ["v5"], ["v4"]]],
         "add": ["le", "v5"],
         "after": [["le", [], ["v4", "v5"]], ["pri", ["v2", "v3"], ["v1"]]]},
    ],
    "journey_js": r"""
  const n=index+1;
  const subs=()=>page.locator('#subscribers li').evaluateAll(ns=>ns.map(x=>x.dataset.id));
  const sugg=()=>page.locator('#typeahead li').evaluateAll(ns=>ns.map(x=>x.dataset.id));
  if(JSON.stringify(await subs())!==JSON.stringify(fixture.state.subscribers)||(await sugg()).length!==0)throw new InterfaceError('subscribers changed or suggestions shown before typing');
  let excluded=true,included=true,precise=true;
  async function query([q,expected,subscribedMatches]){
    await (await one(page,'#add-subscriber')).fill(q);await page.waitForTimeout(250);
    const got=await sugg();const current=await subs();
    excluded=excluded&&got.every(id=>!current.includes(id));
    included=included&&expected.every(id=>got.includes(id));
    precise=precise&&new Set(got).size===got.length&&got.every(id=>expected.includes(id)||subscribedMatches.includes(id));
  }
  for(const q of fixture.before)await query(q);
  const [addQuery,addUser]=fixture.add;
  await (await one(page,'#add-subscriber')).fill(addQuery);await page.waitForTimeout(250);
  const option=page.locator(`#typeahead li[data-id="${addUser}"]`);
  if(await option.count()===1&&await option.isVisible())await option.click();
  await (await one(page,'#add')).click();
  const added=(await subs()).includes(addUser);
  for(const q of fixture.after)await query(q);
  await reload(page);const persisted=(await subs()).includes(addUser);
  check(`subscribed_users_excluded_${n}`,excluded);
  check(`unsubscribed_matches_suggested_${n}`,included&&added&&persisted);
  check(`non_matching_users_excluded_${n}`,precise);
""",
    "target": ["subscribed_users_excluded_1", "subscribed_users_excluded_2"],
    "non_target": ["unsubscribed_matches_suggested_1", "non_matching_users_excluded_1",
                   "unsubscribed_matches_suggested_2", "non_matching_users_excluded_2"],
    "controls": {
        "reference": ("app.onInput(q=>{const t=q.trim().toLowerCase();if(!t){app.showSuggestions([]);return}const subs=app.subscribers();app.showSuggestions(app.users().filter(u=>!subs.includes(u.id)&&(u.name.toLowerCase().includes(t)||u.email.toLowerCase().includes(t))).map(u=>u.id))});", "pass"),
        "word-prefix": (r"app.onInput(function(q){var t=q.trim().toLowerCase();var subs=app.subscribers();app.showSuggestions(t?app.users().filter(function(u){var words=u.name.toLowerCase().split(/\s+/).concat([u.email.toLowerCase()]);return subs.indexOf(u.id)<0&&words.some(function(w){return w.indexOf(t)===0})}).map(function(u){return u.id}):[])});", "pass"),
        "target-mutant": ("app.onInput(q=>{const t=q.trim().toLowerCase();app.showSuggestions(t?app.users().filter(u=>u.name.toLowerCase().includes(t)||u.email.toLowerCase().includes(t)).map(u=>u.id):[])});", "target_only_failure"),
        "stale-subscribers-mutant": ("const SUBS=app.subscribers();app.onInput(q=>{const t=q.trim().toLowerCase();app.showSuggestions(t?app.users().filter(u=>!SUBS.includes(u.id)&&(u.name.toLowerCase().includes(t)||u.email.toLowerCase().includes(t))).map(u=>u.id):[])});", "target_only_failure"),
        "non-target-mutant": ("app.onInput(q=>{const subs=app.subscribers();app.showSuggestions(app.users().filter(u=>!subs.includes(u.id)).map(u=>u.id))});", "non_target_only_failure"),
        "name-only-mutant": ("app.onInput(q=>{const t=q.trim().toLowerCase();const subs=app.subscribers();app.showSuggestions(t?app.users().filter(u=>!subs.includes(u.id)&&u.name.toLowerCase().includes(t)).map(u=>u.id):[])});", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement the Add subscribers typeahead in the channel settings. As the user types in the Name or email "
             "field, show the suggested users with app.showSuggestions(ids), using the users from app.users() and the "
             "channel's current subscribers from app.subscribers(); the user then picks a suggestion and clicks Add. "
             "Under Add subscribers, enter the user's name or email address, and the typeahead suggests the matching "
             "users. The typeahead will only include users who aren't already subscribed to the channel.",
        "B": "In the channel settings, the Name or email field under Add subscribers has a typeahead: while the user "
             "types, list the suggested users through app.showSuggestions(ids), based on app.users() and on the "
             "channel's current subscribers from app.subscribers(), after which the user chooses a suggestion and "
             "clicks Add. Users are looked up by their name or email address, and anyone already subscribed to the "
             "channel is left out of the suggestions.",
        "C": "Implement the Add subscribers typeahead in the channel settings. As the user types in the Name or email "
             "field, show the suggested users with app.showSuggestions(ids), using the users from app.users() and the "
             "channel's current subscribers from app.subscribers(); the user then picks a suggestion and clicks Add. "
             "Under Add subscribers, enter the user's name or email address, and the typeahead suggests the matching "
             "users.",
    },
}

GROUPS = {"role:administrators": "Administrators", "role:moderators": "Moderators", "role:members": "Members",
          "design-team": "design-team", "eng-leads": "eng-leads"}

UNSUBSCRIBE_SELF = {
    "case": "zulip-unsubscribe-self",
    "candidate_id": "rc-dfb84383fb89",
    "project_id": "zulip",
    "source": {"commit": "bde295806c", "file": "help/include/unsubscribe-user-from-channel.md",
               "snapshot": SNAPSHOT, "snapshot_file": DOCS + "unsubscribe-from-a-channel.mdx",
               "snapshot_context": [DOCS + "channel-permissions.mdx"]},
    "title": "Channel settings",
    "register": "app.onUnsubscribe",
    "control": "Unsubscribe buttons",
    "body": '<h1>Channel settings</h1><p id="actor"></p><h2 id="channel"></h2>'
            '<section aria-label="Permissions"><h3>Subscription permissions</h3><ul id="permissions"></ul></section>'
            '<section aria-label="Subscribers"><h3>Subscribers</h3><ul id="subscribers"></ul></section>'
            '<p id="message" role="status"></p>',
    "state_js": r"""
let state=load({subscribers:window.initialState.subscribers});
const S=window.initialState;
const app=Object.freeze({
  onUnsubscribe:register,
  actor(){return structuredClone(S.actor)},
  channel(){return structuredClone(S.channel)},
  users(){return structuredClone(S.users)},
  subscribers(){return [...state.subscribers]},
  unsubscribe(userId){if(!state.subscribers.includes(userId))throw new Error('not a subscriber');state.subscribers=state.subscribers.filter(id=>id!==userId);store(state);render()},
  showMessage(text){document.querySelector('#message').textContent=String(text)}
});
function render(){
  const names=S.groupNames;
  document.querySelector('#actor').textContent='Signed in as '+S.actor.name+' (groups: '+S.actor.groups.map(g=>names[g]).join(', ')+')';
  document.querySelector('#channel').textContent=(S.channel.privacy==='private'?'🔒 ':'#')+S.channel.name;
  const labels={administer:'Who can administer the channel',subscribeSelf:'Who can subscribe themselves',subscribeAnyone:'Who can subscribe anyone',unsubscribeAnyone:'Who can unsubscribe anyone'};
  const perms=document.querySelector('#permissions');perms.replaceChildren();
  for(const [k,label] of Object.entries(labels))perms.append(el('li',{},label+': '+S.channel.permissions[k].map(g=>names[g]).join(', ')));
  const subs=document.querySelector('#subscribers');subs.replaceChildren();
  for(const id of state.subscribers){const u=S.users.find(x=>x.id===id);const li=el('li',{'data-id':id},u.name+(id===S.actor.id?' (you) ':' '));
    li.append(el('button',{type:'button','data-user':id},'Unsubscribe'));subs.append(li)}
}
document.querySelector('#subscribers').addEventListener('click',e=>{const b=e.target.closest('button[data-user]');if(b&&behavior)behavior(b.dataset.user)});
""",
    "fixtures": [
        {"state": {"groupNames": GROUPS,
                   "actor": {"id": "u1", "name": "Lena", "groups": ["role:members", "design-team"]},
                   "users": [{"id": "u1", "name": "Lena"}, {"id": "u2", "name": "Omar"}, {"id": "u3", "name": "Ana"}],
                   "channel": {"id": "c1", "name": "design reviews", "privacy": "private", "permissions": {
                       "administer": ["role:administrators"], "subscribeSelf": ["role:administrators"],
                       "subscribeAnyone": ["role:administrators"], "unsubscribeAnyone": ["role:administrators"]}},
                   "subscribers": ["u1", "u2", "u3"]},
         "other": "u2", "other_allowed": False, "bystanders": ["u3"]},
        {"state": {"groupNames": GROUPS,
                   "actor": {"id": "v1", "name": "Omar", "groups": ["role:members", "eng-leads"]},
                   "users": [{"id": "v1", "name": "Omar"}, {"id": "v2", "name": "Kim"}, {"id": "v3", "name": "Rui"},
                             {"id": "v4", "name": "Ivo"}],
                   "channel": {"id": "c2", "name": "engineering", "privacy": "public", "permissions": {
                       "administer": ["role:administrators"], "subscribeSelf": ["role:members"],
                       "subscribeAnyone": ["role:moderators"], "unsubscribeAnyone": ["role:moderators", "eng-leads"]}},
                   "subscribers": ["v2", "v1", "v3", "v4"]},
         "other": "v3", "other_allowed": True, "bystanders": ["v2", "v4"]},
    ],
    "journey_js": r"""
  const n=index+1;const me=fixture.state.actor.id;
  const subs=()=>page.locator('#subscribers li').evaluateAll(ns=>ns.map(x=>x.dataset.id));
  if(JSON.stringify(await subs())!==JSON.stringify(fixture.state.subscribers))throw new InterfaceError('subscribers missing or changed');
  const selector=`#subscribers button[data-user="${fixture.other}"]`;
  if(fixture.other_allowed)await (await one(page,selector)).click();
  else{const other=page.locator(selector);if(await other.count()===1&&await other.isVisible()&&await other.isEnabled())await other.click()}
  await reload(page);const mid=await subs();
  await (await one(page,`#subscribers button[data-user="${me}"]`)).click();await reload(page);
  const after=await subs();
  check(`self_unsubscribed_${n}`,!after.includes(me));
  if(n===1)check('other_kept_without_permission_1',mid.includes(fixture.other)&&after.includes(fixture.other));
  else check('other_unsubscribed_with_permission_2',!mid.includes(fixture.other)&&!after.includes(fixture.other));
  check(`bystanders_kept_${n}`,fixture.bystanders.every(id=>after.includes(id)));
""",
    "target": ["self_unsubscribed_1", "self_unsubscribed_2"],
    "non_target": ["other_kept_without_permission_1", "bystanders_kept_1",
                   "other_unsubscribed_with_permission_2", "bystanders_kept_2"],
    "controls": {
        "reference": ("app.onUnsubscribe(id=>{const a=app.actor();const may=g=>g.some(x=>a.groups.includes(x));if(id===a.id||may(app.channel().permissions.unsubscribeAnyone)){app.unsubscribe(id);return}app.showMessage('You do not have permission to unsubscribe other users from this channel.')});", "pass"),
        "hide-others": ("(function(){var a=app.actor();var ok=app.channel().permissions.unsubscribeAnyone.some(function(g){return a.groups.indexOf(g)>=0});function hide(){if(!ok)document.querySelectorAll('#subscribers button[data-user]').forEach(function(b){if(b.dataset.user!==a.id)b.hidden=true})}hide();new MutationObserver(hide).observe(document.querySelector('#subscribers'),{childList:true});app.onUnsubscribe(function(id){if(id===a.id||ok)app.unsubscribe(id)})})();", "pass"),
        "target-mutant": ("app.onUnsubscribe(id=>{const a=app.actor();if(!app.channel().permissions.unsubscribeAnyone.some(g=>a.groups.includes(g))){app.showMessage('You do not have permission to unsubscribe users.');return}app.unsubscribe(id)});", "target_only_failure"),
        "symmetric-mutant": ("app.onUnsubscribe(id=>{const a=app.actor();const p=app.channel().permissions;const may=g=>g.some(x=>a.groups.includes(x));if(id===a.id?may(p.subscribeSelf)||may(p.unsubscribeAnyone):may(p.unsubscribeAnyone))app.unsubscribe(id);else app.showMessage('Not allowed.')});", "target_only_failure"),
        "non-target-mutant": ("app.onUnsubscribe(id=>app.unsubscribe(id));", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement the Unsubscribe buttons in the channel's subscriber list. When the signed-in user clicks "
             "Unsubscribe next to a subscriber, remove that subscriber with app.unsubscribe(userId); app.actor() is "
             "the signed-in user with the groups they belong to, app.channel() gives the channel's permission settings "
             "(each listing the groups that hold it), and app.showMessage(text) shows a message. You can configure "
             "the following subscription permissions for each channel, regardless of its type: who can administer "
             "the channel, who can subscribe themselves, who can subscribe anyone, and who can unsubscribe anyone. "
             "You can always unsubscribe from any channel in Zulip. Unsubscribing from a channel removes "
             "conversations in that channel from your inbox, recent conversations, and left sidebar.",
        "B": "Each subscriber in the channel's subscriber list has an Unsubscribe button; clicking it removes that "
             "subscriber through app.unsubscribe(userId). The signed-in user and the groups they are in come from "
             "app.actor(), the channel's permission settings (each one a list of the groups holding it) from "
             "app.channel(), and app.showMessage(text) displays a message. Whatever the channel's type, its "
             "subscription permissions are who can administer it, who can subscribe themselves, who can subscribe "
             "anyone and who can unsubscribe anyone. In Zulip you are always able to unsubscribe yourself from any "
             "channel, and doing so takes that channel's conversations out of your inbox, recent conversations and "
             "left sidebar.",
        "C": "Implement the Unsubscribe buttons in the channel's subscriber list. When the signed-in user clicks "
             "Unsubscribe next to a subscriber, remove that subscriber with app.unsubscribe(userId); app.actor() is "
             "the signed-in user with the groups they belong to, app.channel() gives the channel's permission settings "
             "(each listing the groups that hold it), and app.showMessage(text) shows a message. You can configure "
             "the following subscription permissions for each channel, regardless of its type: who can administer "
             "the channel, who can subscribe themselves, who can subscribe anyone, and who can unsubscribe anyone. "
             "Unsubscribing from a channel removes conversations in that channel from your inbox, recent "
             "conversations, and left sidebar.",
    },
}

PRIVATE_CHANNEL = {
    "case": "zulip-private-channel-access",
    "candidate_id": "rc-fd348eb33246",
    "project_id": "zulip",
    "source": {"commit": "befe49c293", "file": "help/channel-permissions.md",
               "snapshot": SNAPSHOT, "snapshot_file": DOCS + "channel-permissions.mdx"},
    "title": "Channels",
    "register": "app.onOpen",
    "control": "View conversations buttons",
    "body": '<h1>Channels</h1><p id="actor"></p><ul id="channels" aria-label="Channels"></ul>'
            '<section id="conversation" aria-label="Conversations"><h2 id="conversation-title">No channel open</h2>'
            '<ul id="topics" aria-label="Topics"></ul></section><p id="message" role="status"></p>',
    "state_js": r"""
const S=window.initialState;let open=null;
const app=Object.freeze({
  onOpen:register,
  actor(){return structuredClone(S.actor)},
  channels(){return S.channels.map(c=>({id:c.id,name:c.name,privacy:c.privacy,subscribers:[...c.subscribers]}))},
  showConversations(channelId){if(!S.channels.some(c=>c.id===channelId))throw new Error('unknown channel');open=channelId;render()},
  closeConversations(){open=null;render()},
  showMessage(text){document.querySelector('#message').textContent=String(text)}
});
function render(){
  document.querySelector('#actor').textContent='Signed in as '+S.actor.name+' ('+S.actor.role+')';
  const list=document.querySelector('#channels');list.replaceChildren();
  for(const c of S.channels){const li=el('li',{'data-id':c.id},(c.privacy==='private'?'🔒 ':'# ')+c.name+(c.subscribers.includes(S.actor.id)?' (subscribed) ':' '));
    li.append(el('button',{type:'button','data-channel':c.id},'View conversations'));list.append(li)}
  const box=document.querySelector('#conversation');box.dataset.channel=open??'';
  const c=S.channels.find(x=>x.id===open);document.querySelector('#conversation-title').textContent=c?'Conversations in '+c.name:'No channel open';
  const topics=document.querySelector('#topics');topics.replaceChildren();
  if(c)for(const t of c.topics)topics.append(el('li',{'data-topic':t},t));
}
document.querySelector('#channels').addEventListener('click',e=>{const b=e.target.closest('button[data-channel]');if(b&&behavior)behavior(b.dataset.channel)});
""",
    "fixtures": [
        {"state": {"actor": {"id": "u1", "name": "Lena", "role": "member"}, "channels": [
            {"id": "c1", "name": "leadership", "privacy": "private", "subscribers": ["u1", "u2"],
             "topics": ["Q3 hiring plan", "offsite agenda"]},
            {"id": "c2", "name": "general", "privacy": "public", "subscribers": ["u2", "u3"],
             "topics": ["welcome", "lunch on Friday"]}]},
         "private": "c1", "public": "c2"},
        {"state": {"actor": {"id": "g1", "name": "Kim", "role": "guest"}, "channels": [
            {"id": "d1", "name": "announcements", "privacy": "public", "subscribers": ["u5", "u6"],
             "topics": ["new office", "holiday schedule"]},
            {"id": "d2", "name": "client acme", "privacy": "private", "subscribers": ["g1", "u5"],
             "topics": ["contract renewal", "launch checklist", "weekly sync"]}]},
         "private": "d2", "public": "d1"},
    ],
    "journey_js": r"""
  const n=index+1;
  const shown=()=>page.locator('#conversation').evaluate(x=>({channel:x.dataset.channel,topics:[...x.querySelectorAll('#topics li')].map(t=>t.dataset.topic)}));
  if((await shown()).channel!=='')throw new InterfaceError('conversations shown before opening a channel');
  async function open(id){await (await one(page,`#channels button[data-channel="${id}"]`)).click();await page.waitForTimeout(100);return shown()}
  const sees=(r,id)=>r.channel===id&&JSON.stringify(r.topics)===JSON.stringify(fixture.state.channels.find(c=>c.id===id).topics);
  if(n===1){
    check('granted_user_sees_private_1',sees(await open(fixture.private),fixture.private));
    check('member_sees_unsubscribed_public_1',sees(await open(fixture.public),fixture.public));
  }else{
    check('guest_kept_out_of_unsubscribed_public_2',(await open(fixture.public)).channel!==fixture.public);
    check('granted_guest_sees_private_2',sees(await open(fixture.private),fixture.private));
  }
""",
    "target": ["granted_user_sees_private_1", "granted_guest_sees_private_2"],
    "non_target": ["member_sees_unsubscribed_public_1", "guest_kept_out_of_unsubscribed_public_2"],
    "controls": {
        "reference": ("app.onOpen(id=>{const a=app.actor();const c=app.channels().find(x=>x.id===id);const subscribed=c.subscribers.includes(a.id);if(subscribed||(c.privacy!=='private'&&a.role!=='guest')){app.showConversations(id);return}app.closeConversations();app.showMessage('You do not have access to this channel.')});", "pass"),
        "alternative": ("app.onOpen(function(id){var a=app.actor();var c=app.channels().filter(function(x){return x.id===id})[0];var ok=c.privacy==='private'?c.subscribers.indexOf(a.id)>=0:(a.role!=='guest'||c.subscribers.indexOf(a.id)>=0);if(ok)app.showConversations(id);else app.showMessage('Not available')});", "pass"),
        "target-mutant": ("app.onOpen(id=>{const c=app.channels().find(x=>x.id===id);if(c.privacy==='public'&&app.actor().role!=='guest')app.showConversations(id);else{app.closeConversations();app.showMessage('You cannot view this channel.')}});", "target_only_failure"),
        "subscribed-only-mutant": ("app.onOpen(id=>{const c=app.channels().find(x=>x.id===id);if(c.subscribers.includes(app.actor().id))app.showConversations(id);else app.showMessage('Subscribe to view this channel.')});", "non_target_only_failure"),
        "non-target-mutant": ("app.onOpen(id=>app.showConversations(id));", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement viewing a channel's conversations. When the user clicks View conversations for a channel, show "
             "its conversations with app.showConversations(channelId), or otherwise tell the user with "
             "app.showMessage(text); app.actor() gives the signed-in user and their role, and app.channels() gives "
             "each channel's privacy and subscribers. Private channels (indicated by a lock) are for conversations "
             "that should be visible to users who are specifically granted access. Public channels (indicated by #) "
             "are open to all members of your organization other than guests. Anyone who is not a guest can see all "
             "messages and topics, whether or not they are subscribed.",
        "B": "Clicking View conversations for a channel opens its conversations through "
             "app.showConversations(channelId); if they are not opened, inform the user with app.showMessage(text). "
             "The signed-in user and their role come from app.actor(), and every channel's privacy and subscribers "
             "from app.channels(). A private channel (shown with a lock) holds conversations meant to be seen by the "
             "users who were specifically given access to it. A public channel (shown with #) is open to every member "
             "of the organization except guests, and any non-guest can read all of its messages and topics, "
             "subscribed or not.",
        "C": "Implement viewing a channel's conversations. When the user clicks View conversations for a channel, show "
             "its conversations with app.showConversations(channelId), or otherwise tell the user with "
             "app.showMessage(text); app.actor() gives the signed-in user and their role, and app.channels() gives "
             "each channel's privacy and subscribers. Public channels (indicated by #) are open to all members of "
             "your organization other than guests. Anyone who is not a guest can see all messages and topics, "
             "whether or not they are subscribed.",
    },
}

CASES = [GIF_PICKER, RESOLVED_NOTICES, REVERSE_LINKIFIER, SUBSCRIBE_TYPEAHEAD, UNSUBSCRIBE_SELF, PRIVATE_CHANNEL]
