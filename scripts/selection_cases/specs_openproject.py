"""OpenProject selection cases (six selected rules, arm A from the frame-end documentation snapshot)."""

SNAPSHOT = "66f582c19f87534703d2eaf92c5929d13d440cd9"

AUTO_CONTRAST = {
    "case": "openproject-auto-theme-contrast",
    "candidate_id": "rc-02df56f00b58",
    "project_id": "openproject",
    "source": {"commit": "5e64e38f60", "file": "docs/user-guide/account-settings/README.md",
               "snapshot": SNAPSHOT, "snapshot_file": "docs/user-guide/account-settings/interface/README.md"},
    "title": "Interface",
    "register": "app.onUpdate",
    "control": "Update look and feel button",
    "body": '<h1>Interface</h1><section aria-label="Look and feel"><h2>Look and feel</h2>'
            '<label>Color mode <select id="color-mode"><option value="light">Light</option>'
            '<option value="dark">Dark</option><option value="auto">Automatic</option></select></label>'
            '<label><input id="increase-contrast" type="checkbox"> Increase contrast</label>'
            '<button id="update" type="button">Update look and feel</button><p id="message" role="status"></p>'
            '</section><p id="applied"></p>',
    "state_js": r"""
let prefs=load({mode:'light',increaseContrast:false,theme:'light'});
const THEMES=['light','light_high_contrast','dark','dark_high_contrast'];
const app=Object.freeze({
  onUpdate:register,
  system(){return structuredClone(window.initialState.system)},
  preferences(){return {mode:prefs.mode,increaseContrast:prefs.increaseContrast}},
  applyTheme(theme){if(!THEMES.includes(theme))throw new Error('unknown theme');prefs.theme=theme;store(prefs);render()},
  showMessage(text){document.querySelector('#message').textContent=String(text)}
});
function render(){const a=document.querySelector('#applied');a.dataset.theme=prefs.theme;a.textContent='Applied theme: '+prefs.theme.replaceAll('_',' ')}
document.querySelector('#color-mode').value=prefs.mode;document.querySelector('#increase-contrast').checked=prefs.increaseContrast;
document.querySelector('#update').addEventListener('click',()=>{prefs.mode=document.querySelector('#color-mode').value;
  prefs.increaseContrast=document.querySelector('#increase-contrast').checked;store(prefs);
  if(behavior)behavior({mode:prefs.mode,increaseContrast:prefs.increaseContrast})});
""",
    "fixtures": [
        {"state": {"system": {"colorScheme": "dark", "contrast": "more"}},
         "manual": {"mode": "light", "contrast": False, "theme": "light"}},
        {"state": {"system": {"colorScheme": "light", "contrast": "no-preference"}},
         "manual": {"mode": "dark", "contrast": True, "theme": "dark_high_contrast"}},
    ],
    "journey_js": r"""
  const n=index+1;const applied=()=>page.locator('#applied').evaluate(x=>x.dataset.theme);
  if(await applied()!=='light')throw new InterfaceError('theme applied before any update');
  const setContrast=async on=>{const box=page.locator('#increase-contrast');
    if(await box.count()===1&&await box.isVisible()&&await box.isEnabled()){if(on)await box.check();else await box.uncheck()}};
  await (await one(page,'#color-mode')).selectOption(fixture.manual.mode);await setContrast(fixture.manual.contrast);
  await (await one(page,'#update')).click();await reload(page);
  check(`manual_mode_applied_${n}`,await applied()===fixture.manual.theme);
  await (await one(page,'#color-mode')).selectOption('auto');await setContrast(false);
  await (await one(page,'#update')).click();await reload(page);
  const theme=String(await applied());const os=fixture.state.system;
  check(`auto_follows_os_scheme_${n}`,theme.split('_')[0]===os.colorScheme);
  check(`auto_follows_os_contrast_${n}`,theme.endsWith('_high_contrast')===(os.contrast==='more'));
""",
    "target": ["auto_follows_os_contrast_1", "auto_follows_os_contrast_2"],
    "non_target": ["manual_mode_applied_1", "manual_mode_applied_2", "auto_follows_os_scheme_1",
                   "auto_follows_os_scheme_2"],
    "controls": {
        "reference": ("app.onUpdate(f=>{const os=app.system();const auto=f.mode==='auto';const scheme=auto?os.colorScheme:f.mode;const high=f.increaseContrast||(auto&&os.contrast==='more');app.applyTheme(scheme+(high?'_high_contrast':''))});", "pass"),
        "alternative": ("app.onUpdate(function(f){var s=app.system();var base=f.mode;if(f.mode==='auto')base=s.colorScheme==='dark'?'dark':'light';var hc=f.increaseContrast;if(f.mode==='auto'&&s.contrast==='more')hc=true;app.applyTheme(hc?base+'_high_contrast':base);app.showMessage('Saved')});", "pass"),
        "target-mutant": ("app.onUpdate(f=>{const scheme=f.mode==='auto'?app.system().colorScheme:f.mode;app.applyTheme(scheme+(f.increaseContrast?'_high_contrast':''))});", "target_only_failure"),
        "always-high-in-auto": ("app.onUpdate(f=>{const scheme=f.mode==='auto'?app.system().colorScheme:f.mode;app.applyTheme(scheme+(f.increaseContrast||f.mode==='auto'?'_high_contrast':''))});", "target_only_failure"),
        "non-target-mutant": ("app.onUpdate(f=>{const os=app.system();app.applyTheme(os.colorScheme+(os.contrast==='more'?'_high_contrast':''))});", "non_target_only_failure"),
        "light-only-auto": ("app.onUpdate(f=>{const os=app.system();const auto=f.mode==='auto';const scheme=auto?'light':f.mode;const high=f.increaseContrast||(auto&&os.contrast==='more');app.applyTheme(scheme+(high?'_high_contrast':''))});", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement the Update look and feel button of the Interface settings. When the user clicks it, apply the "
             "color mode chosen in the Color mode dropdown with app.applyTheme(theme), where theme is light, "
             "light_high_contrast, dark or dark_high_contrast. You can increase the contrast by activating the "
             "Increase contrast setting, which will significantly increase the contrast. You can also select the "
             "Automatic option, which will match the color mode of your operating system (app.system() describes the "
             "operating system's display preferences). If this option is selected, OpenProject will automatically "
             "match your operating system's light or dark theme, including the system's contrast settings. If your "
             "operating system is set to high contrast mode, OpenProject will also automatically switch to the "
             "corresponding high contrast mode (light or dark).",
        "B": "Clicking Update look and feel in the Interface settings applies the mode picked in the Color mode "
             "dropdown through app.applyTheme(theme), with theme being one of light, light_high_contrast, dark and "
             "dark_high_contrast. Turning on Increase contrast raises the contrast significantly. The Automatic option "
             "follows the color mode of the operating system (app.system() describes the operating system's display "
             "preferences): OpenProject then takes over the system's light or dark theme as well as its contrast "
             "setting, so when the operating system uses high contrast, OpenProject switches to the matching high "
             "contrast mode (light or dark).",
        "C": "Implement the Update look and feel button of the Interface settings. When the user clicks it, apply the "
             "color mode chosen in the Color mode dropdown with app.applyTheme(theme), where theme is light, "
             "light_high_contrast, dark or dark_high_contrast. You can increase the contrast by activating the "
             "Increase contrast setting, which will significantly increase the contrast. You can also select the "
             "Automatic option, which will match the color mode of your operating system (app.system() describes the "
             "operating system's display preferences). If this option is selected, OpenProject will automatically "
             "match your operating system's light or dark theme.",
    },
}

FILTER_TEXT = {
    "case": "openproject-filter-text-autoupdate",
    "candidate_id": "rc-1114153d4704",
    "project_id": "openproject",
    "source": {"commit": "db54165614",
               "file": "docs/user-guide/work-packages/work-package-table-configuration/README.md",
               "snapshot": SNAPSHOT,
               "snapshot_file": "docs/user-guide/work-packages/work-package-table-configuration/README.md"},
    "title": "Work packages",
    "register": "app.onFilterText",
    "control": "Filter by text field",
    "body": '<h1>Work packages</h1><label>Filter by text <input id="filter-text" type="text"></label>'
            '<table><thead><tr><th>ID</th><th>Subject</th></tr></thead><tbody id="rows"></tbody></table>',
    "state_js": r"""
const wps=window.initialState.workPackages;let shown=null;
const app=Object.freeze({
  onFilterText:register,
  workPackages(){return structuredClone(wps)},
  showWorkPackages(ids){if(!Array.isArray(ids)||!ids.every(id=>wps.some(w=>w.id===id)))throw new Error('work package ids required');shown=[...ids];render()}
});
function render(){const body=document.querySelector('#rows');body.replaceChildren();
  for(const id of shown??wps.map(w=>w.id)){const w=wps.find(x=>x.id===id);const tr=el('tr',{'data-id':id});tr.append(el('td',{},'#'+id),el('td',{},w.subject));body.append(tr)}}
document.querySelector('#filter-text').addEventListener('change',e=>{if(behavior)behavior(e.target.value)});
""",
    "fixtures": [
        {"state": {"workPackages": [
            {"id": 101, "subject": "Invoice template redesign", "description": "Update the layout", "comments": ["Looks good"]},
            {"id": 102, "subject": "Server migration", "description": "Move the archive to the new host", "comments": []},
            {"id": 103, "subject": "Team offsite", "description": "Plan the agenda", "comments": ["Book the venue near the river"]},
            {"id": 104, "subject": "Release notes", "description": "Write notes for 17.8", "comments": ["Mention the venue change"]}]},
         "typed": ["Server", [102]], "entered": ["venue", [103, 104]]},
        {"state": {"workPackages": [
            {"id": 201, "subject": "Login page broken", "description": "Users see a blank screen after the upgrade", "comments": []},
            {"id": 202, "subject": "Database maintenance", "description": "Plan downtime", "comments": ["Backup first"]},
            {"id": 203, "subject": "Onboarding checklist", "description": "Steps for new hires", "comments": ["Add the upgrade guide link"]},
            {"id": 204, "subject": "Budget review", "description": "Quarterly numbers", "comments": []}]},
         "typed": ["Budget", [204]], "entered": ["upgrade", [201, 203]]},
    ],
    "journey_js": r"""
  const n=index+1;const rows=()=>page.locator('#rows tr').evaluateAll(ns=>ns.map(x=>Number(x.dataset.id)));
  const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);const all=fixture.state.workPackages.map(w=>w.id);
  if(!same(await rows(),all))throw new InterfaceError('table does not show all work packages');
  const field=await one(page,'#filter-text');
  await field.click();await field.pressSequentially(fixture.typed[0]);await page.waitForTimeout(500);
  check(`results_update_while_typing_${n}`,same(await rows(),fixture.typed[1]));
  await field.fill('');await field.pressSequentially(fixture.entered[0]);await field.press('Enter');await page.waitForTimeout(300);
  check(`text_matches_subject_description_comments_${n}`,same(await rows(),fixture.entered[1]));
  await field.fill('');await field.press('Enter');await page.waitForTimeout(300);
  check(`empty_text_shows_all_${n}`,same(await rows(),all));
""",
    "target": ["results_update_while_typing_1", "results_update_while_typing_2"],
    "non_target": ["text_matches_subject_description_comments_1", "text_matches_subject_description_comments_2",
                   "empty_text_shows_all_1", "empty_text_shows_all_2"],
    "controls": {
        "reference": ("const filter=t=>{const q=t.trim().toLowerCase();app.showWorkPackages(app.workPackages().filter(w=>!q||[w.subject,w.description,...w.comments].some(s=>s.toLowerCase().includes(q))).map(w=>w.id))};app.onFilterText(filter);document.querySelector('#filter-text').addEventListener('input',e=>filter(e.target.value));", "pass"),
        "alternative": ("var timer=null;function run(t){app.showWorkPackages(app.workPackages().filter(function(w){return t===''||(w.subject+'\\n'+w.description+'\\n'+w.comments.join('\\n')).indexOf(t)>=0}).map(function(w){return w.id}))}app.onFilterText(run);document.querySelector('#filter-text').addEventListener('keyup',function(e){clearTimeout(timer);timer=setTimeout(function(){run(e.target.value)},150)});", "pass"),
        "target-mutant": ("app.onFilterText(t=>{const q=t.trim().toLowerCase();app.showWorkPackages(app.workPackages().filter(w=>!q||[w.subject,w.description,...w.comments].some(s=>s.toLowerCase().includes(q))).map(w=>w.id))});", "target_only_failure"),
        "non-target-mutant": ("const filter=t=>{const q=t.trim().toLowerCase();app.showWorkPackages(app.workPackages().filter(w=>w.subject.toLowerCase().includes(q)).map(w=>w.id))};app.onFilterText(filter);document.querySelector('#filter-text').addEventListener('input',e=>filter(e.target.value));", "non_target_only_failure"),
        "empty-shows-none": ("const filter=t=>{const q=t.trim().toLowerCase();app.showWorkPackages(q?app.workPackages().filter(w=>[w.subject,w.description,...w.comments].some(s=>s.toLowerCase().includes(q))).map(w=>w.id):[])};app.onFilterText(filter);document.querySelector('#filter-text').addEventListener('input',e=>filter(e.target.value));", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement the Filter by text field of the work package table. The table shows the work packages passed "
             "to app.showWorkPackages(ids), in the order of app.workPackages(); an empty field shows all work "
             "packages. If you want to search for specific text in the subject, description, or comments of a work "
             "package, type your search term into the Filter by text field. The results will automatically update "
             "and display in the work package table.",
        "B": "In the work package table, the Filter by text field narrows the work packages shown through "
             "app.showWorkPackages(ids), keeping the order of app.workPackages(); with the field empty, every work "
             "package is shown. A search term typed into Filter by text is looked up in each work package's subject, "
             "description and comments, and the table refreshes its results by itself and shows them.",
        "C": "Implement the Filter by text field of the work package table. The table shows the work packages passed "
             "to app.showWorkPackages(ids), in the order of app.workPackages(); an empty field shows all work "
             "packages. If you want to search for specific text in the subject, description, or comments of a work "
             "package, type your search term into the Filter by text field. The results will display in the work "
             "package table.",
    },
}

INVITE_PRINCIPALS = [
    {"id": "u1", "name": "Alice Wong", "kind": "user"},
    {"id": "u2", "name": "Ben Ortiz", "kind": "user"},
    {"id": "g1", "name": "Design team", "kind": "group"},
    {"id": "g2", "name": "Support staff", "kind": "group"},
    {"id": "ph1", "name": "Contractor TBD", "kind": "placeholder_user"},
    {"id": "ph2", "name": "Future tester", "kind": "placeholder_user"},
]

INVITE = {
    "case": "openproject-invite-permission-basis",
    "candidate_id": "rc-17b31565c57c",
    "project_id": "openproject",
    "source": {"commit": "b09683d857", "file": "docs/getting-started/invite-members/README.md",
               "snapshot": SNAPSHOT, "snapshot_file": "docs/getting-started/invite-members/README.md"},
    "title": "Members",
    "register": "app.onInvite",
    "control": "Invite button of the Invite user dialog",
    "body": '<h1>Members</h1><button id="open-invite" type="button">Invite user</button>'
            '<section id="invite" hidden aria-label="Invite user"><h2>Invite user</h2>'
            '<label>Project <select id="invite-project"></select></label>'
            '<label>Name or email <input id="invite-name"></label>'
            '<label>Role <select id="invite-role"></select></label>'
            '<button id="invite-submit" type="button">Invite</button><p id="message" role="status"></p></section>'
            '<h2>Project members</h2><ul id="members" aria-label="Project members"></ul>',
    "state_js": r"""
const S=window.initialState;let members=load(S.members);
const known=(list,id)=>list.some(x=>x.id===id);
const app=Object.freeze({
  onInvite:register,
  projects(){return structuredClone(S.projects)},
  roles(){return structuredClone(S.roles)},
  principals(){return structuredClone(S.principals)},
  members(){return structuredClone(members)},
  addMember(projectId,principalId,roleId,basis='user'){if(!known(S.projects,projectId)||!known(S.principals,principalId)||!known(S.roles,roleId))throw new Error('known project, principal and role required');
    if(members.some(m=>m.project===projectId&&m.principal===principalId)){app.showMessage('Already a member.');return}
    const p=S.principals.find(x=>x.id===principalId);members.push({project:projectId,principal:principalId,kind:p.kind,name:p.name,email:'',role:roleId,basis});store(members);render()},
  inviteByEmail(projectId,email,roleId,basis='user'){if(!known(S.projects,projectId)||!known(S.roles,roleId)||typeof email!=='string'||!/^[^@\s]+@[^@\s]+$/.test(email))throw new Error('known project, email and role required');
    members.push({project:projectId,principal:'',kind:'user',name:email,email,role:roleId,basis});store(members);render()},
  showMessage(text){document.querySelector('#message').textContent=String(text)}
});
function render(){const list=document.querySelector('#members');list.replaceChildren();
  for(const m of members){const project=S.projects.find(p=>p.id===m.project).name,role=S.roles.find(r=>r.id===m.role).name;
    list.append(el('li',{'data-project':m.project,'data-principal':m.principal,'data-kind':m.kind,'data-email':m.email,'data-role':m.role,'data-basis':m.basis||m.kind},m.name+' — '+project+' ('+role+'; permission basis: '+(m.basis||m.kind)+')'))}}
for(const p of S.projects)document.querySelector('#invite-project').append(el('option',{value:p.id},p.name));
for(const r of S.roles)document.querySelector('#invite-role').append(el('option',{value:r.id},r.name));
document.querySelector('#invite-project').value=S.current;
document.querySelector('#open-invite').addEventListener('click',()=>{document.querySelector('#invite').hidden=false});
document.querySelector('#invite-submit').addEventListener('click',()=>{if(behavior)behavior({project:document.querySelector('#invite-project').value,name:document.querySelector('#invite-name').value.trim(),role:document.querySelector('#invite-role').value})});
""",
    "fixtures": [
        {"state": {"projects": [{"id": "pr1", "name": "Website relaunch"}, {"id": "pr2", "name": "Data center"}],
                   "current": "pr1", "roles": [{"id": "r1", "name": "Member"}, {"id": "r2", "name": "Reader"}],
                   "principals": INVITE_PRINCIPALS,
                   "members": [{"project": "pr1", "principal": "u1", "kind": "user", "name": "Alice Wong",
                                "email": "", "role": "r1"}]},
         "first": {"project": "pr2", "name": "new.person@example.org", "role": "r2"},
         "second": {"kind": "group", "project": "pr1", "name": "Ben Ortiz", "id": "u2", "role": "r1"}},
        {"state": {"projects": [{"id": "pq1", "name": "Mobile app"}, {"id": "pq2", "name": "Office move"}],
                   "current": "pq2", "roles": [{"id": "s1", "name": "Project admin"}, {"id": "s2", "name": "Member"}],
                   "principals": INVITE_PRINCIPALS,
                   "members": [{"project": "pq2", "principal": "g2", "kind": "group", "name": "Support staff",
                                "email": "", "role": "s2"}]},
         "first": {"project": "pq2", "name": "Ben Ortiz", "id": "u2", "role": "s1"},
         "second": {"kind": "placeholder_user", "project": "pq1", "name": "Contractor TBD", "id": "ph1", "role": "s2"}},
    ],
    "journey_js": r"""
  const n=index+1;const dlg=page.locator('#invite');
  const members=()=>page.locator('#members li').evaluateAll(ns=>ns.map(x=>({...x.dataset})));
  if((await members()).length!==fixture.state.members.length||await dlg.isVisible())throw new InterfaceError('members changed or dialog open before inviting');
  const KIND={user:/^\s*(an?\s+)?(existing\s+)?users?(\s+role)?\s*$/i,group:/^\s*(an?\s+)?groups?\b/i,placeholder_user:/placeholder/i};
  async function choose(kind){
    const re=KIND[kind];
    const valueRadio=dlg.locator(`input[type=radio][value="${kind}"]`);
    if(await valueRadio.count()===1&&await valueRadio.isVisible()&&await valueRadio.isEnabled()){await valueRadio.check();return true}
    const radio=dlg.getByRole('radio',{name:re});if(await radio.count()===1&&await radio.isVisible()){await radio.check();return true}
    for(const s of await dlg.locator('select').all()){const id=await s.getAttribute('id');if(id==='invite-project'||id==='invite-role'||!await s.isVisible())continue;
      const hit=(await s.locator('option').evaluateAll(os=>os.map(o=>[o.value,o.textContent.trim()]))).filter(o=>o[0]===kind||re.test(o[1]));
      if(hit.length===1){await s.selectOption(hit[0][0]);return true}}
    const tab=dlg.getByRole('tab',{name:re});if(await tab.count()===1&&await tab.isVisible()){await tab.click();return true}
    const button=dlg.getByRole('button',{name:re});if(await button.count()===1&&await button.isVisible()){await button.click();return true}
    return false}
  async function invite(step){
    await (await one(page,'#invite-project')).selectOption(step.project);
    await (await one(page,'#invite-name')).fill(step.name);
    await (await one(page,'#invite-role')).selectOption(step.role);
    await (await one(page,'#invite-submit')).click();await reload(page)}
  const f=fixture.first;await (await one(page,'#open-invite')).click();await choose('user');await invite(f);
  const after1=await members();
  if(n===1)check('new_user_invited_by_email_1',after1.some(m=>m.email===f.name&&m.kind==='user'&&m.project===f.project&&m.role===f.role));
  else check('existing_user_added_2',after1.some(m=>m.principal===f.id&&m.kind==='user'&&m.project===f.project&&m.role===f.role));
  const s=fixture.second;let added=false;
  await (await one(page,'#open-invite')).click();
  if(await choose(s.kind)){await invite(s);added=(await members()).some(m=>m.principal===s.id&&m.kind===(s.kind==='group'?'user':s.kind)&&m.basis===s.kind&&m.project===s.project&&m.role===s.role)}
  check(n===1?'group_basis_selectable_1':'placeholder_basis_selectable_2',added);
  const final=await members();
  check(`existing_members_kept_${n}`,fixture.state.members.every(e=>final.some(m=>m.project===e.project&&m.principal===e.principal&&m.role===e.role)));
""",
    "target": ["group_basis_selectable_1", "placeholder_basis_selectable_2"],
    "non_target": ["new_user_invited_by_email_1", "existing_user_added_2", "existing_members_kept_1",
                   "existing_members_kept_2"],
    "controls": {
        "group-principal-mutant": ("const box=document.createElement('fieldset');box.append(el('legend',{},'Invite a'));for(const [v,l] of [['user','User'],['group','Group'],['placeholder_user','Placeholder user']]){const lab=el('label');const r=el('input',{type:'radio',name:'kind',value:v});r.checked=v==='user';lab.append(r,' '+l);box.append(lab)}document.querySelector('#invite-name').closest('label').before(box);app.onInvite(f=>{const kind=document.querySelector('input[name=kind]:checked').value;if(kind==='user'&&f.name.includes('@')){app.inviteByEmail(f.project,f.name,f.role);return}const p=app.principals().find(x=>x.kind===kind&&x.name===f.name);if(!p){app.showMessage('No '+kind+' named '+f.name);return}app.addMember(f.project,p.id,f.role)});", "target_only_failure"),
        "renamed-bases": ("const box=document.createElement('fieldset');box.append(el('legend',{},'Invite a'));for(const [v,l] of [['user','User'],['group','Permission collective'],['placeholder_user','Reserved identity']]){const lab=el('label');const r=el('input',{type:'radio',name:'kind',value:v});r.checked=v==='user';lab.append(r,' '+l);box.append(lab)}document.querySelector('#invite-name').closest('label').before(box);app.onInvite(f=>{const kind=document.querySelector('input[name=kind]:checked').value;if((kind==='user'||kind==='group')&&f.name.includes('@')){app.inviteByEmail(f.project,f.name,f.role,kind);return}const p=app.principals().find(x=>x.kind===(kind==='group'?'user':kind)&&x.name===f.name);if(!p){app.showMessage('No '+kind+' named '+f.name);return}app.addMember(f.project,p.id,f.role,kind)});", "pass"),
        "reference": ("const box=document.createElement('fieldset');box.append(el('legend',{},'Invite a'));for(const [v,l] of [['user','User'],['group','Group'],['placeholder_user','Placeholder user']]){const lab=el('label');const r=el('input',{type:'radio',name:'kind',value:v});r.checked=v==='user';lab.append(r,' '+l);box.append(lab)}document.querySelector('#invite-name').closest('label').before(box);app.onInvite(f=>{const kind=document.querySelector('input[name=kind]:checked').value;if((kind==='user'||kind==='group')&&f.name.includes('@')){app.inviteByEmail(f.project,f.name,f.role,kind);return}const p=app.principals().find(x=>x.kind===(kind==='group'?'user':kind)&&x.name===f.name);if(!p){app.showMessage('No '+kind+' named '+f.name);return}app.addMember(f.project,p.id,f.role,kind)});", "pass"),
        "alternative": ("var sel=document.createElement('select');sel.id='principal-type';[['user','User'],['group','Group'],['placeholder_user','Placeholder user']].forEach(function(o){var op=document.createElement('option');op.value=o[0];op.textContent=o[1];sel.appendChild(op)});var lab=document.createElement('label');lab.textContent='Permissions based on ';lab.appendChild(sel);document.querySelector('#invite-project').parentNode.after(lab);app.onInvite(function(f){var kind=sel.value;var p=app.principals().filter(function(x){return x.kind===(kind==='group'?'user':kind)&&x.name.toLowerCase()===f.name.toLowerCase()})[0];if(p)app.addMember(f.project,p.id,f.role,kind);else if((kind==='user'||kind==='group')&&/@/.test(f.name))app.inviteByEmail(f.project,f.name,f.role,kind);else app.showMessage('Not found')});", "pass"),
        "target-mutant": ("app.onInvite(f=>{if(f.name.includes('@')){app.inviteByEmail(f.project,f.name,f.role);return}const p=app.principals().find(x=>x.kind==='user'&&x.name===f.name);if(p)app.addMember(f.project,p.id,f.role);else app.showMessage('User not found')});", "target_only_failure"),
        "two-bases-mutant": ("const box=document.createElement('fieldset');for(const [v,l] of [['user','User'],['group','Group']]){const lab=el('label');const r=el('input',{type:'radio',name:'kind',value:v});r.checked=v==='user';lab.append(r,' '+l);box.append(lab)}document.querySelector('#invite-name').closest('label').before(box);app.onInvite(f=>{const kind=document.querySelector('input[name=kind]:checked').value;if((kind==='user'||kind==='group')&&f.name.includes('@')){app.inviteByEmail(f.project,f.name,f.role,kind);return}const p=app.principals().find(x=>x.kind===(kind==='group'?'user':kind)&&x.name===f.name);if(p)app.addMember(f.project,p.id,f.role,kind)});", "target_only_failure"),
        "non-target-mutant": ("const box=document.createElement('fieldset');for(const [v,l] of [['user','User'],['group','Group'],['placeholder_user','Placeholder user']]){const lab=el('label');const r=el('input',{type:'radio',name:'kind',value:v});r.checked=v==='user';lab.append(r,' '+l);box.append(lab)}document.querySelector('#invite-name').closest('label').before(box);app.onInvite(f=>{const kind=document.querySelector('input[name=kind]:checked').value;if(kind==='user')return;const p=app.principals().find(x=>x.kind===(kind==='group'?'user':kind)&&x.name===f.name);if(p)app.addMember(f.project,p.id,f.role,kind)});", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement the Invite user dialog. Once you click Invite user, a dialogue will open. Here you can select "
             "the project, to which project you want to invite new members. Select whether the permissions assigned "
             "to the new user should be based on an existing user role, group or a placeholder user permissions. "
             "With User or Group, select an existing user or enter an email address for a new one; with "
             "Placeholder user, enter the name of a placeholder user. "
             "Then enter the name of an existing principal (listed by app.principals()) or the email address of a new "
             "user, assign a role and click Invite: add an existing principal with app.addMember(projectId, "
             "principalId, roleId, basis) or invite a new user by email with app.inviteByEmail(projectId, email, roleId, basis).",
        "B": "Clicking Invite user opens a dialog where the project that new members are invited to is picked, and "
             "where the user decides whether the new member's permissions come from an existing user role, from a "
             "group, or from a placeholder user's permissions. User and Group accept an existing user or a new "
             "user's email; Placeholder user accepts a placeholder's name. Next comes the name of an existing principal (see "
             "app.principals()) or a new user's email address, then a role, then a click on Invite; existing "
             "principals are added through app.addMember(projectId, principalId, roleId, basis) and new users are invited "
             "by email through app.inviteByEmail(projectId, email, roleId, basis).",
        "C": "Implement the Invite user dialog. Once you click Invite user, a dialogue will open. Here you can select "
             "the project, to which project you want to invite new members. "
             "Then enter the name of an existing principal (listed by app.principals()) or the email address of a new "
             "user, assign a role and click Invite: add an existing principal with app.addMember(projectId, "
             "principalId, roleId, basis) or invite a new user by email with app.inviteByEmail(projectId, email, roleId, basis).",
    },
}

ARCHIVED_SELECTOR = {
    "case": "openproject-archived-project-selector",
    "candidate_id": "rc-2c13970217ea",
    "project_id": "openproject",
    "source": {"commit": "784ed0fb52", "file": "docs/user-guide/projects/README.md",
               "snapshot": SNAPSHOT,
               "snapshot_file": "docs/user-guide/projects/project-settings/project-information/README.md",
               "snapshot_context_file": "docs/getting-started/projects/README.md"},
    "title": "Project information",
    "register": "app.onProjectSearch",
    "control": "All projects dropdown and its search field",
    "body": '<header><button id="all-projects" type="button" aria-expanded="false">All projects</button>'
            '<div id="project-menu" hidden><label>Search <input id="project-search"></label>'
            '<ul id="project-options" aria-label="Projects"></ul></div></header>'
            '<h1>Project information: <span id="current"></span></h1>'
            '<button id="more" type="button" aria-expanded="false">More</button>'
            '<div id="more-menu" hidden><button id="archive" type="button">Archive project</button></div>',
    "state_js": r"""
let state=load({projects:window.initialState.projects,current:window.initialState.current});let options=[];
const app=Object.freeze({
  onProjectSearch:register,
  projects(){return structuredClone(state.projects)},
  showOptions(ids){if(!Array.isArray(ids)||!ids.every(id=>state.projects.some(p=>p.id===id)))throw new Error('project ids required');options=[...ids];render()}
});
function render(){const p=state.projects.find(x=>x.id===state.current);const c=document.querySelector('#current');
  c.dataset.id=p.id;c.dataset.archived=String(p.archived);c.textContent=p.name+(p.archived?' (archived)':'');
  const list=document.querySelector('#project-options');list.replaceChildren();
  for(const id of options){const li=el('li');li.append(el('button',{type:'button','data-id':id},state.projects.find(x=>x.id===id).name));list.append(li)}}
const menu=document.querySelector('#project-menu');
document.querySelector('#all-projects').addEventListener('click',e=>{menu.hidden=!menu.hidden;e.target.setAttribute('aria-expanded',String(!menu.hidden));
  if(!menu.hidden){document.querySelector('#project-search').value='';options=[];render();if(behavior)behavior('')}});
document.querySelector('#project-search').addEventListener('input',e=>{if(behavior)behavior(e.target.value)});
document.querySelector('#project-options').addEventListener('click',e=>{const id=e.target.dataset?.id;if(!id)return;state.current=id;store(state);menu.hidden=true;render()});
document.querySelector('#more').addEventListener('click',()=>{const m=document.querySelector('#more-menu');m.hidden=!m.hidden});
document.querySelector('#archive').addEventListener('click',()=>{state.projects.find(x=>x.id===state.current).archived=true;store(state);document.querySelector('#more-menu').hidden=true;render()});
""",
    "fixtures": [
        {"state": {"current": "p3", "projects": [
            {"id": "p1", "name": "Marketing campaign", "archived": False},
            {"id": "p2", "name": "Mobile app", "archived": False},
            {"id": "p3", "name": "Market research", "archived": False},
            {"id": "p4", "name": "Office move", "archived": False}]},
         "query": "Mar", "query_active": ["p1"], "open_next": "p2"},
        {"state": {"current": "q4", "projects": [
            {"id": "q1", "name": "Website relaunch", "archived": False},
            {"id": "q2", "name": "Web shop", "archived": True},
            {"id": "q3", "name": "Customer portal", "archived": False},
            {"id": "q4", "name": "Wiki cleanup", "archived": False}]},
         "query": "Web", "query_active": ["q1"], "open_next": "q3"},
    ],
    "journey_js": r"""
  const n=index+1;const cur=fixture.state.current;const projects=fixture.state.projects;
  const current=()=>page.locator('#current').evaluate(x=>({...x.dataset}));
  const options=()=>page.locator('#project-options [data-id]').evaluateAll(ns=>ns.map(x=>x.dataset.id));
  const openSelector=async()=>{await (await one(page,'#all-projects')).click();await page.waitForTimeout(150);return options()};
  const c0=await current();if(c0.id!==cur||c0.archived!=='false')throw new InterfaceError('current project missing or archived');
  const before=await openSelector();const archivedBefore=projects.filter(p=>p.archived).map(p=>p.id);
  const activeBefore=projects.filter(p=>!p.archived).map(p=>p.id);
  await reload(page);await (await one(page,'#more')).click();await (await one(page,'#archive')).click();await reload(page);
  if((await current()).archived!=='true')throw new InterfaceError('archiving through the page failed');
  const after=await openSelector();const archived=[...archivedBefore,cur];
  check(`archived_project_not_selectable_${n}`,!after.includes(cur)&&archivedBefore.every(id=>!before.includes(id)));
  check(`active_projects_selectable_${n}`,activeBefore.every(id=>before.includes(id))&&activeBefore.filter(id=>id!==cur).every(id=>after.includes(id)));
  await (await one(page,'#project-search')).fill(fixture.query);await page.waitForTimeout(150);const found=await options();
  const title=id=>projects.find(p=>p.id===id).name.toLowerCase();
  check(`archived_not_in_search_${n}`,archived.every(id=>!found.includes(id)));
  check(`search_filters_by_title_${n}`,fixture.query_active.every(id=>found.includes(id))&&found.every(id=>title(id).includes(fixture.query.toLowerCase())));
  await (await one(page,'#project-search')).fill('');await page.waitForTimeout(150);
  const next=page.locator(`#project-options [data-id="${fixture.open_next}"]`);let opened=false;
  if(await next.count()===1&&await next.isVisible()){await next.click();await reload(page);opened=(await current()).id===fixture.open_next}
  check(`option_opens_project_${n}`,opened);
""",
    "target": ["archived_project_not_selectable_1", "archived_project_not_selectable_2",
               "archived_not_in_search_1", "archived_not_in_search_2"],
    "non_target": ["active_projects_selectable_1", "active_projects_selectable_2", "search_filters_by_title_1",
                   "search_filters_by_title_2", "option_opens_project_1", "option_opens_project_2"],
    "controls": {
        "reference": ("app.onProjectSearch(q=>{const t=q.trim().toLowerCase();app.showOptions(app.projects().filter(p=>!p.archived&&p.name.toLowerCase().includes(t)).map(p=>p.id))});", "pass"),
        "alternative": ("app.onProjectSearch(function(q){var active=app.projects().filter(function(p){return p.archived!==true});app.showOptions(active.filter(function(p){return p.name.indexOf(q)!==-1}).map(function(p){return p.id}))});", "pass"),
        "target-mutant": ("app.onProjectSearch(q=>{const t=q.trim().toLowerCase();app.showOptions(app.projects().filter(p=>p.name.toLowerCase().includes(t)).map(p=>p.id))});", "target_only_failure"),
        "archived-in-search": ("app.onProjectSearch(q=>{const t=q.trim().toLowerCase();app.showOptions(app.projects().filter(p=>t?p.name.toLowerCase().includes(t):!p.archived).map(p=>p.id))});", "target_only_failure"),
        "non-target-mutant": ("app.onProjectSearch(()=>app.showOptions(app.projects().filter(p=>!p.archived).map(p=>p.id)));", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement the project list of the All projects dropdown in the header. In order to open an existing "
             "project, click the All projects dropdown menu in the upper left corner of the header and select the "
             "project you want to open. You can also start typing in a project name to filter by the project's title. "
             "When the dropdown opens and whenever its search text changes, list the selectable projects from "
             "app.projects() with app.showOptions(ids). In order to archive a project, click the More (three dots) "
             "icon and select Archive project. Once archived, a project can no longer be selected from the project "
             "list accessible via header navigation.",
        "B": "The All projects dropdown in the upper left corner of the header is how an existing project is opened: "
             "the user opens it and picks the project. Typing part of a project name filters the list by project "
             "title. Each time the dropdown opens or its search text changes, pass the selectable projects from "
             "app.projects() to app.showOptions(ids). A project is archived through the More (three dots) icon and "
             "Archive project, and from then on it cannot be chosen any more in the project list reached through the "
             "header navigation.",
        "C": "Implement the project list of the All projects dropdown in the header. In order to open an existing "
             "project, click the All projects dropdown menu in the upper left corner of the header and select the "
             "project you want to open. You can also start typing in a project name to filter by the project's title. "
             "When the dropdown opens and whenever its search text changes, list the selectable projects from "
             "app.projects() with app.showOptions(ids). In order to archive a project, click the More (three dots) "
             "icon and select Archive project.",
    },
}

MORE_MENU = {
    "case": "openproject-more-menu-subproject",
    "candidate_id": "rc-4efba0098a79",
    "project_id": "openproject",
    "source": {"commit": "60be87235a",
               "file": "docs/user-guide/projects/project-settings/project-information/README.md",
               "snapshot": SNAPSHOT,
               "snapshot_file": "docs/user-guide/projects/project-settings/project-information/README.md"},
    "title": "Project information",
    "register": "app.onMore",
    "control": "More button",
    "body": '<h1>Project information: <span id="project"></span></h1>'
            '<button id="more" type="button" aria-haspopup="menu" aria-expanded="false">More</button>'
            '<ul id="more-menu" role="menu" hidden></ul>'
            '<section id="new-project" hidden aria-label="New project"><h2>New project</h2>'
            '<label>Name <input id="np-name"></label><label>Subproject of <select id="np-parent"></select></label>'
            '<button id="np-create" type="button">Create</button></section>'
            '<h2>Projects</h2><ul id="projects" aria-label="Projects"></ul>',
    "state_js": r"""
let projects=load(window.initialState.projects);let menu=[];const currentId=window.initialState.current;
const cur=()=>projects.find(p=>p.id===currentId);
const flag=(key,value)=>{const p=cur();if(!p)throw new Error('project deleted');p[key]=value;store(projects);render()};
function openForm(name,parent){const form=document.querySelector('#new-project');const sel=document.querySelector('#np-parent');sel.replaceChildren(el('option',{value:''},'(none)'));
  for(const p of projects)sel.append(el('option',{value:p.id},p.name));sel.value=parent??'';document.querySelector('#np-name').value=name;form.hidden=false}
const app=Object.freeze({
  onMore:register,
  project(){return structuredClone(cur()??null)},
  projects(){return structuredClone(projects)},
  showMenu(items){if(!Array.isArray(items)||!items.every(i=>i&&typeof i.label==='string'&&i.label.trim()&&typeof i.run==='function'))throw new Error('items need label and run');menu=items.map(i=>({label:i.label,run:i.run}));render()},
  openProjectForm(options={}){const parent=options?.parent??null;if(parent!==null&&!projects.some(p=>p.id===parent))throw new Error('unknown parent');openForm('',parent)},
  duplicateProject(){const p=cur();openForm('Copy of '+p.name,p.parent)},
  makePublic(){flag('public',true)},
  setTemplate(){flag('template',true)},
  archive(){flag('archived',true)},
  deleteProject(){projects=projects.filter(p=>p.id!==currentId);store(projects);render()}
});
function render(){const p=cur();document.querySelector('#project').textContent=p?p.name:'(deleted)';
  const m=document.querySelector('#more-menu');m.replaceChildren();
  menu.forEach((item,i)=>{const li=el('li',{role:'none'});li.append(el('button',{type:'button',role:'menuitem','data-index':i},item.label));m.append(li)});
  const list=document.querySelector('#projects');list.replaceChildren();
  for(const x of projects)list.append(el('li',{'data-id':x.id,'data-name':x.name,'data-parent':x.parent??'','data-public':String(!!x.public),'data-template':String(!!x.template),'data-archived':String(!!x.archived)},
    x.name+(x.parent?' (subproject of '+projects.find(y=>y.id===x.parent)?.name+')':'')+(x.public?' · public':'')+(x.template?' · template':'')+(x.archived?' · archived':'')))}
document.querySelector('#more').addEventListener('click',e=>{const m=document.querySelector('#more-menu');
  if(m.hidden&&behavior)behavior(app.project());m.hidden=!m.hidden;e.target.setAttribute('aria-expanded',String(!m.hidden))});
document.querySelector('#more-menu').addEventListener('click',e=>{const i=e.target.dataset?.index;if(i===undefined)return;document.querySelector('#more-menu').hidden=true;menu[Number(i)].run()});
document.querySelector('#np-create').addEventListener('click',()=>{const name=document.querySelector('#np-name').value.trim();if(!name)return;
  projects.push({id:'n'+(projects.length+1),name,parent:document.querySelector('#np-parent').value||null,public:false,template:false,archived:false});store(projects);
  document.querySelector('#new-project').hidden=true;render()});
""",
    "fixtures": [
        {"state": {"current": "a1", "projects": [
            {"id": "a1", "name": "Website relaunch", "parent": None, "public": False, "template": False, "archived": False},
            {"id": "a2", "name": "Intranet", "parent": None, "public": False, "template": False, "archived": False}]},
         "other": {"key": "make_public_works", "re": "make\\s+(a\\s+|the\\s+)?(project\\s+)?public", "attr": "public"},
         "child": "Landing pages"},
        {"state": {"current": "b2", "projects": [
            {"id": "b1", "name": "Product line", "parent": None, "public": False, "template": False, "archived": False},
            {"id": "b2", "name": "Release 3.0", "parent": "b1", "public": False, "template": False, "archived": False},
            {"id": "b3", "name": "Support", "parent": None, "public": False, "template": False, "archived": False}]},
         "other": {"key": "set_template_works", "re": "template", "attr": "template"},
         "child": "Beta program"},
    ],
    "journey_js": r"""
  const n=index+1;const cur=fixture.state.current;
  const projects=()=>page.locator('#projects li').evaluateAll(ns=>ns.map(x=>({...x.dataset})));
  const initial=await projects();
  if(initial.length!==fixture.state.projects.length||!initial.some(p=>p.id===cur)||await page.locator('#new-project').isVisible())throw new InterfaceError('projects changed before the menu was used');
  async function useItem(re){await (await one(page,'#more')).click();await page.waitForTimeout(100);
    const item=page.locator('#more-menu').getByRole('menuitem',{name:re});
    if(await item.count()<1||!await item.first().isVisible())return false;await item.first().click();return true}
  const used=await useItem(new RegExp(fixture.other.re,'i'));await reload(page);
  const me=(await projects()).find(p=>p.id===cur);
  check(`${fixture.other.key}_${n}`,used&&me?.[fixture.other.attr]==='true');
  let created=false;
  if(await useItem(/add\s+(a\s+)?sub-?project/i)){const form=page.locator('#new-project');
    if(await form.isVisible()){await (await one(page,'#np-name')).fill(fixture.child);await (await one(page,'#np-create')).click();await reload(page);
      const made=(await projects()).filter(p=>p.name===fixture.child);created=made.length===1&&made[0].parent===cur}}
  check(`subproject_created_under_current_${n}`,created);
  const final=await projects();
  check(`existing_projects_kept_${n}`,fixture.state.projects.every(p=>final.some(f=>f.id===p.id&&f.parent===(p.parent??''))));
""",
    "target": ["subproject_created_under_current_1", "subproject_created_under_current_2"],
    "non_target": ["make_public_works_1", "set_template_works_2", "existing_projects_kept_1", "existing_projects_kept_2"],
    "controls": {
        "reference": ("app.onMore(p=>app.showMenu([{label:'Add a subproject',run:()=>app.openProjectForm({parent:p.id})},{label:'Duplicate a project',run:()=>app.duplicateProject()},{label:'Make a project public',run:()=>app.makePublic()},{label:'Set a project as a template',run:()=>app.setTemplate()},{label:'Archive a project',run:()=>app.archive()},{label:'Delete a project',run:()=>app.deleteProject()}]));", "pass"),
        "alternative": ("app.showMenu([{label:'+ Add subproject',run:function(){app.openProjectForm({parent:app.project().id})}},{label:'Duplicate',run:function(){app.duplicateProject()}},{label:'Make public',run:function(){app.makePublic()}},{label:'Set as template',run:function(){app.setTemplate()}},{label:'Archive project',run:function(){app.archive()}},{label:'Delete project',run:function(){app.deleteProject()}}]);app.onMore(function(){});", "pass"),
        "target-mutant": ("app.onMore(()=>app.showMenu([{label:'Duplicate a project',run:()=>app.duplicateProject()},{label:'Make a project public',run:()=>app.makePublic()},{label:'Set a project as a template',run:()=>app.setTemplate()},{label:'Archive a project',run:()=>app.archive()},{label:'Delete a project',run:()=>app.deleteProject()}]));", "target_only_failure"),
        "no-parent-mutant": ("app.onMore(()=>app.showMenu([{label:'Add a subproject',run:()=>app.openProjectForm()},{label:'Duplicate a project',run:()=>app.duplicateProject()},{label:'Make a project public',run:()=>app.makePublic()},{label:'Set a project as a template',run:()=>app.setTemplate()},{label:'Archive a project',run:()=>app.archive()},{label:'Delete a project',run:()=>app.deleteProject()}]));", "target_only_failure"),
        "non-target-mutant": ("app.onMore(p=>app.showMenu([{label:'Add a subproject',run:()=>app.openProjectForm({parent:p.id})},{label:'Duplicate a project',run:()=>app.duplicateProject()},{label:'Make a project public',run:()=>{}},{label:'Set a project as a template',run:()=>{}},{label:'Archive a project',run:()=>app.archive()},{label:'Delete a project',run:()=>app.deleteProject()}]));", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement the More menu of the project information page. When the user clicks More, show the menu items "
             "for the current project app.project() with app.showMenu([{label, run}]). In the top-right corner, click "
             "the More (three dots) icon to open a menu with additional project actions: Add a subproject "
             "(app.openProjectForm({parent: projectId})), Duplicate a project (app.duplicateProject()), Make a "
             "project public (app.makePublic()), Set a project as a template (app.setTemplate()), Archive a project "
             "(app.archive()), Delete a project (app.deleteProject()).",
        "B": "The project information page has a More (three dots) icon in its top-right corner; clicking it opens a "
             "menu of further actions for the current project app.project(), built with app.showMenu([{label, "
             "run}]). The menu offers: Delete a project (app.deleteProject()), Archive a project (app.archive()), Set "
             "a project as a template (app.setTemplate()), Make a project public (app.makePublic()), Duplicate a "
             "project (app.duplicateProject()) and Add a subproject (app.openProjectForm({parent: projectId})).",
        "C": "Implement the More menu of the project information page. When the user clicks More, show the menu items "
             "for the current project app.project() with app.showMenu([{label, run}]). In the top-right corner, click "
             "the More (three dots) icon to open a menu with additional project actions: Duplicate a project "
             "(app.duplicateProject()), Make a "
             "project public (app.makePublic()), Set a project as a template (app.setTemplate()), Archive a project "
             "(app.archive()), Delete a project (app.deleteProject()).",
    },
}

FILES_TAB = {
    "case": "openproject-files-tab-attachments",
    "candidate_id": "rc-e436521e462d",
    "project_id": "openproject",
    "source": {"commit": "4af6f743b0", "file": "docs/user-guide/projects/project-settings/files/README.md",
               "snapshot": SNAPSHOT, "snapshot_file": "docs/user-guide/projects/project-settings/files/README.md"},
    "title": "Work package",
    "register": "app.onFilesTab",
    "control": "Files tab",
    "body": '<section aria-label="Project settings"><h2>Project settings › Files › Attachments</h2>'
            '<label><input id="attachments-setting" type="checkbox"> Attachments</label>'
            '<button id="save-settings" type="button">Save</button><p id="settings-state"></p></section>'
            '<section aria-label="Work package"><h1 id="wp-title"></h1>'
            '<button id="files-tab" type="button">Files</button><div id="files-panel"></div></section>',
    "state_js": r"""
const S=window.initialState;let settings=load(S.settings);let sections=[];
const app=Object.freeze({
  onFilesTab:register,
  workPackage(){return structuredClone(S.workPackage)},
  storages(){return structuredClone(S.storages)},
  settings(){return structuredClone(settings)},
  showFilesTab(list){if(!Array.isArray(list)||!list.every(s=>s==='attachments'||S.storages.some(x=>x.id===s)))throw new Error('sections must be attachments or storage ids');sections=[...list];render()}
});
function render(){document.querySelector('#wp-title').textContent='#'+S.workPackage.id+' '+S.workPackage.subject;
  const st=document.querySelector('#settings-state');st.dataset.attachments=String(settings.attachments);st.textContent='Saved: '+(settings.attachments?'on':'off');
  const panel=document.querySelector('#files-panel');panel.replaceChildren();
  for(const s of sections){const box=el('div',{'data-section':s});
    if(s==='attachments'){box.append(el('h3',{},'Attachments'));const ul=el('ul');for(const a of S.workPackage.attachments)ul.append(el('li',{},a));box.append(ul)}
    else box.append(el('h3',{},S.storages.find(x=>x.id===s).name));
    panel.append(box)}}
document.querySelector('#attachments-setting').checked=settings.attachments;
document.querySelector('#save-settings').addEventListener('click',()=>{settings={...settings,attachments:document.querySelector('#attachments-setting').checked};store(settings);render()});
document.querySelector('#files-tab').addEventListener('click',()=>{if(behavior)behavior(app.workPackage())});
""",
    "fixtures": [
        {"state": {"settings": {"attachments": True},
                   "workPackage": {"id": 311, "subject": "Prepare kickoff", "attachments": ["agenda.pdf", "budget.xlsx"]},
                   "storages": [{"id": "nc1", "name": "Nextcloud"}]}},
        {"state": {"settings": {"attachments": False},
                   "workPackage": {"id": 422, "subject": "Supplier contract", "attachments": ["contract-draft.docx"]},
                   "storages": [{"id": "od1", "name": "OneDrive/SharePoint"}, {"id": "nc2", "name": "Nextcloud archive"}]}},
    ],
    "journey_js": r"""
  const n=index+1;const initialOn=fixture.state.settings.attachments;const storages=fixture.state.storages.map(s=>s.id);
  const sections=()=>page.locator('#files-panel [data-section]').evaluateAll(ns=>ns.map(x=>x.dataset.section));
  const saved=()=>page.locator('#settings-state').evaluate(x=>x.dataset.attachments);
  if(await saved()!==String(initialOn)||(await sections()).length!==0)throw new InterfaceError('setting changed or files shown before opening the tab');
  const openFiles=async()=>{await (await one(page,'#files-tab')).click();await page.waitForTimeout(150);return sections()};
  const first=await openFiles();
  const box=await one(page,'#attachments-setting');if(initialOn)await box.uncheck();else await box.check();
  await (await one(page,'#save-settings')).click();await reload(page);
  if(await saved()!==String(!initialOn))throw new InterfaceError('setting was not saved through the page');
  const second=await openFiles();const on=initialOn?first:second,off=initialOn?second:first;
  check(`attachments_hidden_when_disabled_${n}`,!off.includes('attachments'));
  check(`attachments_shown_when_enabled_${n}`,on.includes('attachments'));
  check(`storages_shown_${n}`,[first,second].every(s=>storages.every(id=>s.includes(id))));
""",
    "target": ["attachments_hidden_when_disabled_1", "attachments_hidden_when_disabled_2"],
    "non_target": ["attachments_shown_when_enabled_1", "attachments_shown_when_enabled_2", "storages_shown_1",
                   "storages_shown_2"],
    "controls": {
        "reference": ("app.onFilesTab(()=>app.showFilesTab([...(app.settings().attachments?['attachments']:[]),...app.storages().map(s=>s.id)]));", "pass"),
        "alternative": ("app.onFilesTab(function(){var list=app.storages().map(function(s){return s.id});if(app.settings().attachments===true)list.push('attachments');app.showFilesTab(list)});", "pass"),
        "target-mutant": ("app.onFilesTab(()=>app.showFilesTab(['attachments',...app.storages().map(s=>s.id)]));", "target_only_failure"),
        "non-target-mutant": ("app.onFilesTab(()=>app.showFilesTab(app.storages().map(s=>s.id)));", "non_target_only_failure"),
        "no-storages-mutant": ("app.onFilesTab(()=>app.showFilesTab(app.settings().attachments?['attachments']:[]));", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement the Files tab of the work package detailed view. When the user opens the Files tab, show its "
             "sections with app.showFilesTab(sections), where a section is 'attachments' (the work package's "
             "attachments) or the id of one of the project's file storages from app.storages(); every file storage "
             "of the project is shown. To activate or de-activate the attachments being shown under Files tab in work "
             "packages, navigate to Project settings > Files and select the Attachments tab (saved in "
             "app.settings().attachments). Here you can decide whether the attachments option will be shown under "
             "Files tab of work packages detailed view for a specific project.",
        "B": "The work package detailed view has a Files tab; opening it passes its sections to "
             "app.showFilesTab(sections), each section being either 'attachments' (the work package's attachments) "
             "or the id of a project file storage from app.storages(), and all of the project's file storages "
             "appear. Whether the attachments option appears under the Files tab of a project's work packages is "
             "decided per project in Project settings > Files, on the Attachments tab (saved in "
             "app.settings().attachments), where showing the attachments there is switched on or off.",
        "C": "Implement the Files tab of the work package detailed view. When the user opens the Files tab, show its "
             "sections with app.showFilesTab(sections), where a section is 'attachments' (the work package's "
             "attachments) or the id of one of the project's file storages from app.storages(); every file storage "
             "of the project is shown.",
    },
}

CASES = [AUTO_CONTRAST, FILTER_TEXT, INVITE, ARCHIVED_SELECTOR, MORE_MENU, FILES_TAB]
