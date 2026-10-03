"""Paperless-ngx selection cases (all five admitted Paperless rules)."""

AI_SKIP = {
    "case": "paperless-ai-suggestions-blank-text",
    "candidate_id": "rc-84013890a131",
    "project_id": "paperless-ngx",
    "source": {"commit": "937feb1bef", "file": "docs/usage.md"},
    "title": "Workflow run",
    "register": "app.onRun",
    "control": "Run action button",
    "body": '<h1>Workflow run</h1><p id="workflow"></p><button id="run" type="button">Run action</button>'
            '<ul id="documents" aria-label="Documents"></ul>',
    "state_js": r"""
let queued=load([]);
const app=Object.freeze({
  onRun:register,
  documents(){return structuredClone(window.initialState.documents)},
  queueSuggestions(id){if(!window.initialState.documents.some(d=>d.id===id))throw new Error('unknown document');queued.push(id);store(queued);render()}
});
function render(){
  document.querySelector('#workflow').textContent='Action: '+window.initialState.workflow;
  const list=document.querySelector('#documents');list.replaceChildren();
  for(const d of window.initialState.documents){const n=queued.filter(id=>id===d.id).length;
    list.append(el('li',{'data-id':d.id,'data-queued':n},d.title+(n?' — suggestions queued':' — not queued')))}
}
document.querySelector('#run').addEventListener('click',()=>{if(behavior)behavior(app.documents())});
""",
    "fixtures": [
        {"state": {"workflow": "Apply AI Suggestions", "documents": [
            {"id": "d1", "title": "Invoice March", "content": "Invoice 2026-03, total 120 EUR, due 30 April."},
            {"id": "d2", "title": "Blank scan", "content": "   \n\t  \n"},
            {"id": "d3", "title": "Letter", "content": "Dear customer, thank you for your order."}]},
         "blank": ["d2"], "text": ["d1", "d3"]},
        {"state": {"workflow": "Apply AI Suggestions", "documents": [
            {"id": "e1", "title": "Receipt", "content": ""},
            {"id": "e2", "title": "Contract", "content": "Contract between Alpha Ltd and Beta GmbH."},
            {"id": "e3", "title": "Photo of whiteboard", "content": "\n\n   "}]},
         "blank": ["e1", "e3"], "text": ["e2"]},
    ],
    "journey_js": r"""
  const n=index+1;const ids=fixture.state.documents.map(d=>d.id);
  const before=await page.locator('#documents li').evaluateAll(ns=>ns.map(x=>[x.dataset.id,x.dataset.queued]));
  if(JSON.stringify(before)!==JSON.stringify(ids.map(id=>[id,'0'])))throw new InterfaceError('documents missing or queued before the run');
  await (await one(page,'#run')).click();await reload(page);
  const after=Object.fromEntries(await page.locator('#documents li').evaluateAll(ns=>ns.map(x=>[x.dataset.id,Number(x.dataset.queued)])));
  check(`blank_documents_skipped_${n}`,fixture.blank.every(id=>after[id]===0));
  check(`text_documents_queued_once_${n}`,fixture.text.every(id=>after[id]===1));
  check(`documents_preserved_${n}`,JSON.stringify(Object.keys(after))===JSON.stringify(ids));
""",
    "target": ["blank_documents_skipped_1", "blank_documents_skipped_2"],
    "non_target": ["text_documents_queued_once_1", "text_documents_queued_once_2",
                   "documents_preserved_1", "documents_preserved_2"],
    "controls": {
        "reference": ("app.onRun(docs=>{for(const d of docs)if(d.content.trim())app.queueSuggestions(d.id)});", "pass"),
        "alternative": ("app.onRun(function(docs){docs.filter(function(d){return /\\S/.test(d.content)}).forEach(function(d){app.queueSuggestions(d.id)})});", "pass"),
        "target-mutant": ("app.onRun(docs=>docs.forEach(d=>app.queueSuggestions(d.id)));", "target_only_failure"),
        "empty-only-mutant": ("app.onRun(docs=>docs.filter(d=>d.content!=='').forEach(d=>app.queueSuggestions(d.id)));", "target_only_failure"),
        "non-target-mutant": ("app.onRun(()=>{});", "non_target_only_failure"),
        "duplicate-mutant": ("app.onRun(docs=>{for(const d of docs)if(d.content.trim()){app.queueSuggestions(d.id);app.queueSuggestions(d.id)}});", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement the run of the \"Apply AI Suggestions\" workflow action. When the user clicks Run action, "
             "ask the AI service for suggestions for each listed document by calling app.queueSuggestions(id); "
             "the action is queued and runs in the background. Suggestions are made from the document's processed "
             "text (its content). Documents whose processed text is empty or contains only whitespace are skipped.",
        "B": "Clicking Run action executes the \"Apply AI Suggestions\" workflow action: for every listed document, "
             "request AI suggestions in the background with app.queueSuggestions(id). The suggestions are based on "
             "the document's processed text (its content), so a document whose processed text has no characters "
             "other than whitespace, or none at all, is not sent.",
        "C": "Implement the run of the \"Apply AI Suggestions\" workflow action. When the user clicks Run action, "
             "ask the AI service for suggestions for each listed document by calling app.queueSuggestions(id); "
             "the action is queued and runs in the background. Suggestions are made from the document's processed "
             "text (its content).",
    },
}

SUPERUSER = {
    "case": "paperless-superuser-grant",
    "candidate_id": "rc-806442660eb5",
    "project_id": "paperless-ngx",
    "source": {"commit": "41bcc12cc2", "file": "docs/usage.md"},
    "title": "Users & Groups",
    "register": "app.onSave",
    "control": "Save button",
    "body": '<h1>Users &amp; Groups</h1><p id="actor"></p><section aria-label="Edit user"><h2>Edit user '
            '<span id="username"></span></h2><label>First name <input id="first-name"></label>'
            '<label><input id="superuser" type="checkbox"> Superuser status</label>'
            '<button id="save" type="button">Save</button><p id="message" role="status"></p></section>'
            '<p id="stored"></p>',
    "state_js": r"""
let user=load(window.initialState.user);
const app=Object.freeze({
  onSave:register,
  actor(){return structuredClone(window.initialState.actor)},
  user(){return structuredClone(user)},
  saveUser(change){if(typeof change!=='object'||change===null||typeof change.firstName!=='string'||typeof change.superuser!=='boolean')throw new Error('firstName and superuser required');
    user={...user,firstName:change.firstName,superuser:change.superuser};store(user);render()},
  showMessage(text){document.querySelector('#message').textContent=String(text)}
});
function render(){
  const a=window.initialState.actor;
  document.querySelector('#actor').textContent='Signed in as '+a.username+(a.superuser?' (superuser)':' (staff, can change users)');
  document.querySelector('#username').textContent=user.username;
  const stored=document.querySelector('#stored');stored.dataset.username=user.username;stored.dataset.firstName=user.firstName;stored.dataset.superuser=String(user.superuser);
  stored.textContent='Stored: '+user.firstName+', superuser: '+(user.superuser?'yes':'no');
}
document.querySelector('#first-name').value=user.firstName;document.querySelector('#superuser').checked=user.superuser;
document.querySelector('#save').addEventListener('click',()=>{if(behavior)behavior({firstName:document.querySelector('#first-name').value,superuser:document.querySelector('#superuser').checked})});
""",
    "fixtures": [
        {"state": {"actor": {"username": "maria", "superuser": False},
                   "user": {"username": "bob", "firstName": "Bob", "superuser": False}},
         "kind": "non_superuser", "first_name": "Robert"},
        {"state": {"actor": {"username": "admin", "superuser": True},
                   "user": {"username": "carla", "firstName": "Carla", "superuser": False}},
         "kind": "superuser", "first_name": "Carla Maria"},
    ],
    "journey_js": r"""
  const n=index+1;const stored=()=>page.locator('#stored').evaluate(x=>({...x.dataset}));
  const initial=await stored();
  if(initial.superuser!=='false'||initial.username!==fixture.state.user.username)throw new InterfaceError('user missing or already superuser');
  await (await one(page,'#first-name')).fill(fixture.first_name);
  if(fixture.kind==='non_superuser'){
    await (await one(page,'#save')).click();await reload(page);
    check('first_name_saved_1',(await stored()).firstName===fixture.first_name);
    await (await one(page,'#first-name')).fill(fixture.first_name);
  }
  const box=page.locator('#superuser');
  if(await box.count()===1&&await box.isVisible()&&await box.isEnabled())await box.check();
  await (await one(page,'#save')).click();await reload(page);
  const after=await stored();
  if(fixture.kind==='non_superuser'){
    check('non_superuser_cannot_grant_1',after.superuser==='false');
    check('username_preserved_1',after.username===fixture.state.user.username);
  }else{
    check('superuser_can_grant_2',after.superuser==='true');
    check('first_name_saved_2',after.firstName===fixture.first_name);
    check('username_preserved_2',after.username===fixture.state.user.username);
  }
""",
    "target": ["non_superuser_cannot_grant_1"],
    "non_target": ["first_name_saved_1", "username_preserved_1", "superuser_can_grant_2", "first_name_saved_2", "username_preserved_2"],
    "controls": {
        "reference": ("app.onSave(form=>{if(form.superuser&&!app.user().superuser&&!app.actor().superuser){app.showMessage('Only a superuser can grant superuser status.');app.saveUser({firstName:form.firstName,superuser:false});return}app.saveUser(form)});", "pass"),
        "alternative": ("app.onSave(function(f){if(!app.actor().superuser)f.superuser=app.user().superuser;app.saveUser(f)});", "pass"),
        "disable-control": ("document.querySelector('#superuser').disabled=!app.actor().superuser;app.onSave(f=>app.saveUser(f));", "pass"),
        "target-mutant": ("app.onSave(form=>app.saveUser(form));", "target_only_failure"),
        "blanket-role-denial": ("app.onSave(f=>{if(!app.actor().superuser)return;app.saveUser(f)});", "non_target_only_failure"),
        "non-target-mutant": ("app.onSave(()=>app.saveUser({firstName:app.user().firstName,superuser:false}));", "non_target_only_failure"),
    },
    "arms": {
        "A": "Edit another user account in Users & Groups. When the signed-in user clicks Save, store the edited first "
             "name and superuser status with app.saveUser. Superusers can access all parts of the application and all "
             "objects. Superuser status can only be granted by another superuser.",
        "B": "In Users & Groups, clicking Save stores the edited user's first name and superuser status through "
             "app.saveUser. A superuser has access to every part of the application and every object, and only "
             "someone who is already a superuser may give superuser status to another user.",
        "C": "Edit another user account in Users & Groups. When the signed-in user clicks Save, store the edited first "
             "name and superuser status with app.saveUser. Superusers can access all parts of the application and all "
             "objects.",
    },
}

CUSTOM_FIELD = {
    "case": "paperless-custom-field-no-value",
    "candidate_id": "rc-086a9d210266",
    "project_id": "paperless-ngx",
    "source": {"commit": "855669ddf9", "file": "docs/usage.md"},
    "title": "Workflow assignment",
    "register": "app.onApply",
    "control": "Apply assignment button",
    "body": '<h1>Workflow action</h1><p id="action"></p><button id="apply" type="button">Apply assignment</button>'
            '<ul id="documents" aria-label="Documents"></ul>',
    "state_js": r"""
let docs=load(window.initialState.documents);
const app=Object.freeze({
  onApply:register,
  action(){return structuredClone(window.initialState.action)},
  documents(){return structuredClone(docs)},
  setCustomFields(id,fields){const doc=docs.find(d=>d.id===id);if(!doc)throw new Error('unknown document');
    if(typeof fields!=='object'||fields===null||Array.isArray(fields)||!Object.values(fields).every(v=>v===null||typeof v==='string'))throw new Error('fields must map names to text or null');
    doc.fields={...fields};store(docs);render()}
});
function render(){
  const a=window.initialState.action;
  document.querySelector('#action').textContent='Assignment: custom field '+a.field+(a.value===null?' (no value)':' with value '+a.value);
  const list=document.querySelector('#documents');list.replaceChildren();
  for(const d of docs){const li=el('li',{'data-id':d.id},d.title+': ');
    for(const [name,value] of Object.entries(d.fields))li.append(el('span',{class:'field','data-name':name,'data-value':value??''},name+' = '+(value??'(empty)')+'; '));
    list.append(li)}
}
document.querySelector('#apply').addEventListener('click',()=>{if(behavior)behavior(app.action(),app.documents())});
""",
    "fixtures": [
        {"state": {"action": {"field": "Invoice number", "value": None}, "documents": [
            {"id": "d1", "title": "Invoice A", "fields": {"Invoice number": "INV-1", "Due date": "2026-10-01"}},
            {"id": "d2", "title": "Invoice B", "fields": {"Due date": "2026-11-01"}}]}},
        {"state": {"action": {"field": "Invoice number", "value": "INV-9"}, "documents": [
            {"id": "e1", "title": "Invoice C", "fields": {"Invoice number": "INV-2", "Due date": "2026-12-01"}},
            {"id": "e2", "title": "Invoice D", "fields": {"Due date": "2027-01-01"}}]}},
    ],
    "journey_js": r"""
  const n=index+1;
  const read=()=>page.locator('#documents li').evaluateAll(ns=>ns.map(li=>({id:li.dataset.id,fields:Object.fromEntries([...li.querySelectorAll('.field')].map(f=>[f.dataset.name,f.dataset.value]))})));
  const expect0=fixture.state.documents.map(d=>({id:d.id,fields:d.fields}));
  if(JSON.stringify(await read())!==JSON.stringify(expect0))throw new InterfaceError('documents changed before the action');
  await (await one(page,'#apply')).click();await reload(page);
  const [first,second]=await read();const field=fixture.state.action.field;
  const dueKept=[first,second].every((d,i)=>d&&d.fields['Due date']===fixture.state.documents[i].fields['Due date']);
  if(n===1){
    check('existing_value_kept_1',first?.fields[field]==='INV-1');
    check('field_added_empty_1',second?.fields[field]==='');
    check('other_fields_kept_1',dueKept);
  }else{
    check('value_overwrites_2',first?.fields[field]==='INV-9');
    check('value_added_2',second?.fields[field]==='INV-9');
    check('other_fields_kept_2',dueKept);
  }
""",
    "target": ["existing_value_kept_1"],
    "non_target": ["field_added_empty_1", "other_fields_kept_1", "value_overwrites_2", "value_added_2",
                   "other_fields_kept_2"],
    "controls": {
        "reference": ("app.onApply((action,docs)=>{for(const d of docs){const f={...d.fields};if(action.value!==null)f[action.field]=action.value;else if(!(action.field in f))f[action.field]=null;app.setCustomFields(d.id,f)}});", "pass"),
        "alternative": ("app.onApply(function(a,docs){docs.forEach(function(d){var f=Object.assign({},d.fields);if(a.value!=null||!Object.prototype.hasOwnProperty.call(f,a.field))f[a.field]=a.value;app.setCustomFields(d.id,f)})});", "pass"),
        "target-mutant": ("app.onApply((a,docs)=>docs.forEach(d=>app.setCustomFields(d.id,{...d.fields,[a.field]:a.value})));", "target_only_failure"),
        "non-target-mutant": ("app.onApply((a,docs)=>docs.forEach(d=>{const f={...d.fields};if(!(a.field in f))f[a.field]=a.value;app.setCustomFields(d.id,f)}));", "non_target_only_failure"),
        "drop-fields-mutant": ("app.onApply((a,docs)=>docs.forEach(d=>app.setCustomFields(d.id,{[a.field]:a.value===null&&a.field in d.fields?d.fields[a.field]:a.value})));", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement the workflow \"Assignment\" action for custom fields. When the user clicks Apply assignment, "
             "assign the action's custom field to every listed document with app.setCustomFields, keeping the "
             "document's other fields. Custom fields can be assigned optionally with a value. If no value is set, "
             "the field is only added to the document and any value it may already have is left untouched. If a "
             "value is set, it will overwrite an existing value of that field on the document.",
        "B": "Clicking Apply assignment runs the workflow \"Assignment\" action: each listed document receives the "
             "action's custom field through app.setCustomFields, and its other fields stay as they are. A value for "
             "the field is optional. Without a value, the field is merely attached and an existing value on the "
             "document is not changed; with a value, that value replaces whatever the document had for the field.",
        "C": "Implement the workflow \"Assignment\" action for custom fields. When the user clicks Apply assignment, "
             "assign the action's custom field to every listed document with app.setCustomFields, keeping the "
             "document's other fields. Custom fields can be assigned optionally with a value. If a value is set, it "
             "will overwrite an existing value of that field on the document.",
    },
}

OWN_PROFILE = {
    "case": "paperless-own-profile",
    "candidate_id": "rc-035e8af08cd7",
    "project_id": "paperless-ngx",
    "source": {"commit": "1ba6c31385", "file": "docs/usage.md"},
    "title": "My Profile",
    "register": "app.onSave",
    "control": "Save button",
    "body": '<h1>My Profile</h1><p id="signed-in"></p><label>First name <input id="first-name"></label>'
            '<label>Email <input id="email" type="email"></label><button id="save" type="button">Save</button>'
            '<p id="message" role="status"></p><p id="stored"></p>',
    "state_js": r"""
let profile=load(window.initialState.profile);
const app=Object.freeze({
  onSave:register,
  profile(){return structuredClone(profile)},
  permissions(){return structuredClone(window.initialState.permissions)},
  saveProfile(change){if(typeof change!=='object'||change===null||typeof change.firstName!=='string'||typeof change.email!=='string')throw new Error('firstName and email required');
    profile={...profile,firstName:change.firstName,email:change.email};store(profile);render()},
  showMessage(text){document.querySelector('#message').textContent=String(text)}
});
function render(){
  document.querySelector('#signed-in').textContent='Signed in as '+profile.username;
  const s=document.querySelector('#stored');s.dataset.username=profile.username;s.dataset.firstName=profile.firstName;s.dataset.email=profile.email;
  s.textContent='Saved profile: '+profile.firstName+' <'+profile.email+'>';
}
document.querySelector('#first-name').value=profile.firstName;document.querySelector('#email').value=profile.email;
document.querySelector('#save').addEventListener('click',()=>{if(behavior)behavior({firstName:document.querySelector('#first-name').value,email:document.querySelector('#email').value})});
""",
    "fixtures": [
        {"state": {"profile": {"username": "lena", "firstName": "Lena", "email": "lena@example.org"},
                   "permissions": ["view_document", "change_document", "view_tag", "view_uisettings"]},
         "first_name": "Lena M.", "email": "lena.m@example.org"},
        {"state": {"profile": {"username": "omar", "firstName": "Omar", "email": "omar@example.org"},
                   "permissions": ["view_document", "view_user", "change_user", "add_user", "view_uisettings"]},
         "first_name": "Omar K.", "email": "omar.k@example.org"},
    ],
    "journey_js": r"""
  const n=index+1;const stored=()=>page.locator('#stored').evaluate(x=>({...x.dataset}));
  const p=fixture.state.profile;const initial=await stored();
  if(initial.firstName!==p.firstName||initial.email!==p.email)throw new InterfaceError('profile missing or changed before editing');
  await (await one(page,'#first-name')).fill(fixture.first_name);await (await one(page,'#email')).fill(fixture.email);
  await (await one(page,'#save')).click();await reload(page);
  const after=await stored();const saved=after.firstName===fixture.first_name&&after.email===fixture.email;
  if(n===1)check('saved_without_user_permissions_1',saved);else check('saved_with_user_permissions_2',saved);
  check(`username_unchanged_${n}`,after.username===p.username);
""",
    "target": ["saved_without_user_permissions_1"],
    "non_target": ["saved_with_user_permissions_2", "username_unchanged_1", "username_unchanged_2"],
    "controls": {
        "reference": ("app.onSave(form=>app.saveProfile(form));", "pass"),
        "alternative": ("app.onSave(function(f){app.saveProfile({firstName:f.firstName.trim(),email:f.email.trim()});app.showMessage('Profile saved')});", "pass"),
        "target-mutant": ("app.onSave(form=>{if(!app.permissions().includes('change_user')){app.showMessage('Permission denied');return}app.saveProfile(form)});", "target_only_failure"),
        "non-target-mutant": ("app.onSave(form=>{if(app.permissions().includes('change_user'))return;app.saveProfile(form)});", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement saving in the My Profile dialog. When the signed-in user clicks Save, store their edited first "
             "name and email with app.saveProfile. Permissions are listed by app.permissions(); the User permission "
             "allows adding, editing, deleting or viewing other user accounts via Settings > Users & Groups. These "
             "permissions are not needed for users to edit their own profile via My Profile.",
        "B": "In the My Profile dialog, clicking Save stores the signed-in user's edited first name and email through "
             "app.saveProfile. app.permissions() lists the user's permissions; the User permission covers adding, "
             "editing, deleting and viewing other people's accounts in Settings > Users & Groups, and a user does "
             "not need it to change their own profile in My Profile.",
        "C": "Implement saving in the My Profile dialog. When the signed-in user clicks Save, store their edited first "
             "name and email with app.saveProfile. Permissions are listed by app.permissions(); the User permission "
             "allows adding, editing, deleting or viewing other user accounts via Settings > Users & Groups.",
    },
}

DOC_TITLE = {
    "case": "paperless-doc-title-placeholder",
    "candidate_id": "rc-9e198862b86e",
    "project_id": "paperless-ngx",
    "source": {"commit": "63c0e2f72b", "file": "docs/usage.md"},
    "title": "Workflow title assignment",
    "register": "app.onSave",
    "control": "Save button",
    "body": '<h1>Workflow assignment</h1><label>Assign title <input id="title-template" size="60"></label>'
            '<button id="save" type="button">Save</button><p id="message" role="status"></p>'
            '<p>Saved title template: <code id="saved"></code></p>',
    "state_js": r"""
let saved=load('');
const app=Object.freeze({
  onSave:register,
  savedTemplate(){return saved},
  saveTitleTemplate(text){if(typeof text!=='string')throw new Error('text required');saved=text;store(saved);render()},
  showMessage(text){document.querySelector('#message').textContent=String(text)}
});
function render(){const s=document.querySelector('#saved');s.dataset.template=saved;s.textContent=saved||'(none)'}
document.querySelector('#save').addEventListener('click',()=>{if(behavior)behavior(document.querySelector('#title-template').value)});
""",
    "fixtures": [
        {"state": {}, "invalid": "{{correspondent}} - {{doc_title}}", "valid": "{{correspondent}} - {{added_year}}"},
        {"state": {}, "invalid": "{{doc_title}}", "valid": "{{original_filename}}"},
    ],
    "journey_js": r"""
  const n=index+1;const saved=()=>page.locator('#saved').evaluate(x=>x.dataset.template);
  if(await saved()!=='')throw new InterfaceError('template saved before editing');
  await (await one(page,'#title-template')).fill(fixture.invalid);await (await one(page,'#save')).click();await reload(page);
  check(`doc_title_not_saved_${n}`,!(await saved()).includes('{{doc_title}}'));
  await (await one(page,'#title-template')).fill(fixture.valid);await (await one(page,'#save')).click();await reload(page);
  check(`valid_template_saved_${n}`,await saved()===fixture.valid);
""",
    "target": ["doc_title_not_saved_1", "doc_title_not_saved_2"],
    "non_target": ["valid_template_saved_1", "valid_template_saved_2"],
    "controls": {
        "reference": ("app.onSave(t=>{if(t.includes('{{doc_title}}')){app.showMessage('{{doc_title}} cannot be used in title assignment.');return}app.saveTitleTemplate(t)});", "pass"),
        "alternative": ("app.onSave(function(t){if(/\\{\\{\\s*doc_title\\s*\\}\\}/.test(t))app.showMessage('Not allowed here');else app.saveTitleTemplate(t)});", "pass"),
        "strip": ("app.onSave(t=>app.saveTitleTemplate(t.replaceAll('{{doc_title}}','').trim()));", "pass"),
        "target-mutant": ("app.onSave(t=>app.saveTitleTemplate(t));", "target_only_failure"),
        "non-target-mutant": ("app.onSave(()=>{});", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement saving the title template of a workflow assignment. When the user clicks Save, store the "
             "entered template with app.saveTitleTemplate. Titles are Jinja templates and can use these placeholders: "
             "{{correspondent}} (assigned correspondent name), {{document_type}} (assigned document type name), "
             "{{owner_username}} (assigned owner username), {{added}}, {{added_year}}, {{added_month}}, {{added_day}} "
             "(added date parts), {{original_filename}} (original file name without extension), {{filename}} "
             "(current file name without extension) and {{doc_title}} (current document title, cannot be used in "
             "title assignment).",
        "B": "Clicking Save stores the workflow assignment's title template through app.saveTitleTemplate. A title is "
             "a Jinja template whose available placeholders are {{correspondent}} (name of the assigned "
             "correspondent), {{document_type}} (name of the assigned document type), {{owner_username}} (user name "
             "of the assigned owner), {{added}}, {{added_year}}, {{added_month}} and {{added_day}} (parts of the "
             "added date), {{original_filename}} and {{filename}} (original and current file names without "
             "extension), and {{doc_title}}, the current title of the document, which is not allowed in a title "
             "assignment.",
        "C": "Implement saving the title template of a workflow assignment. When the user clicks Save, store the "
             "entered template with app.saveTitleTemplate. Titles are Jinja templates and can use these placeholders: "
             "{{correspondent}} (assigned correspondent name), {{document_type}} (assigned document type name), "
             "{{owner_username}} (assigned owner username), {{added}}, {{added_year}}, {{added_month}}, {{added_day}} "
             "(added date parts), {{original_filename}} (original file name without extension), {{filename}} "
             "(current file name without extension) and {{doc_title}} (current document title).",
    },
}

CASES = [AI_SKIP, SUPERUSER, CUSTOM_FIELD, OWN_PROFILE, DOC_TITLE]
