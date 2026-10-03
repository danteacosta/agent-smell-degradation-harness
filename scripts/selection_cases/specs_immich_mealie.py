"""Immich and Mealie selection cases (projects with at most six admitted rules)."""

VIDEO_LIST_A = ("3GPP (.3gp .3gpp), AVI (.avi), FLV (.flv), M4V (.m4v), MATROSKA (.mkv), MP2T (.mts .m2ts .m2t .ts), "
                "MP4 (.mp4 .insv), MPEG (.mpg .mpe .mpeg), QUICKTIME (.mov), WEBM (.webm), WMV (.wmv)")
VIDEO_LIST_C = VIDEO_LIST_A.replace("MP2T (.mts .m2ts .m2t .ts)", "MP2T (.mts .m2ts .ts)")
VIDEO_LIST_B = ("QUICKTIME (.mov), MP4 (.mp4 .insv), MATROSKA (.mkv), WEBM (.webm), AVI (.avi), WMV (.wmv), "
                "FLV (.flv), M4V (.m4v), MPEG (.mpg .mpe .mpeg), 3GPP (.3gp .3gpp) and MP2T (.mts .m2ts .m2t .ts)")

M2T = {
    "case": "immich-m2t-upload",
    "candidate_id": "rc-0ec1ac8f66bd",
    "project_id": "immich",
    "source": {"commit": "fcd372238f", "file": "docs/docs/features/supported-formats.md",
               "arm_a_snapshot_commit": "a3c8b359f2fdc47699f1530215a23fe8bd34c454",
               "frame_end": "2026-09-30T23:59:59Z"},
    "title": "Upload videos",
    "register": "app.onFiles",
    "control": "file input",
    "body": '<h1>Upload videos</h1><label>Choose files <input id="files" type="file" multiple></label>'
            '<ul id="results" aria-label="Upload results"></ul>',
    "state_js": r"""
let results=load({});
function decide(name,status,reason){if(typeof name!=='string'||!(name in pending))throw new Error('unknown file');results[name]={status,reason:String(reason??'')};store(results);render()}
let pending={};
const app=Object.freeze({
  onFiles:register,
  accept(name){decide(name,'accepted','')},
  reject(name,reason){decide(name,'rejected',reason||'Unsupported file type')}
});
function render(){const list=document.querySelector('#results');list.replaceChildren();
  for(const [name,r] of Object.entries(results))list.append(el('li',{'data-name':name,'data-status':r.status},name+': '+r.status+(r.reason?' ('+r.reason+')':'')))}
document.querySelector('#files').addEventListener('change',e=>{const files=[...e.target.files].map(f=>({name:f.name,size:f.size,type:f.type}));
  for(const f of files)pending[f.name]=true;if(behavior)behavior(structuredClone(files))});
""",
    "fixtures": [
        {"state": {}, "files": [["holiday.m2t", "application/octet-stream", True, True],
                                ["clip.mov", "video/quicktime", False, True],
                                ["transport.ts", "video/mp2t", False, True],
                                ["notes.txt", "text/plain", False, False]]},
        {"state": {}, "files": [["race.m2t", "application/octet-stream", True, True],
                                ["match.mts", "video/mp2t", False, True],
                                ["stream.ts", "video/mp2t", False, True],
                                ["scan.pdf", "application/pdf", False, False]]},
    ],
    "journey_js": r"""
  const n=index+1;
  if(await page.locator('#results li').count()!==0)throw new InterfaceError('results present before upload');
  const input=page.locator('#files');if(await input.count()!==1)throw new InterfaceError('one file input required');
  await input.setInputFiles(fixture.files.map(([name,mimeType])=>({name,mimeType,buffer:Buffer.from('test video '+name)})));
  await page.waitForTimeout(300);await reload(page);
  const rows=await page.locator('#results li').evaluateAll(ns=>ns.map(x=>[x.dataset.name,x.dataset.status]));
  const status=Object.fromEntries(rows);
  check(`m2t_accepted_${n}`,fixture.files.filter(f=>f[2]).every(f=>status[f[0]]==='accepted'));
  check(`other_video_accepted_${n}`,fixture.files.filter(f=>!f[2]&&f[3]).every(f=>status[f[0]]==='accepted'));
  check(`non_video_rejected_${n}`,fixture.files.filter(f=>!f[3]).every(f=>status[f[0]]==='rejected'));
  check(`each_file_decided_once_${n}`,rows.length===fixture.files.length&&new Set(rows.map(r=>r[0])).size===rows.length);
""",
    "target": ["m2t_accepted_1", "m2t_accepted_2"],
    "non_target": ["other_video_accepted_1", "other_video_accepted_2", "non_video_rejected_1", "non_video_rejected_2",
                   "each_file_decided_once_1", "each_file_decided_once_2"],
    "controls": {
        "ts-missing-mutant": ("const VIDEO=['.3gp','.3gpp','.avi','.flv','.m4v','.mkv','.mts','.m2ts','.m2t','.mp4','.insv','.mpg','.mpe','.mpeg','.mov','.webm','.wmv'];app.onFiles(files=>{for(const f of files){const ext=f.name.slice(f.name.lastIndexOf('.')).toLowerCase();if(VIDEO.includes(ext))app.accept(f.name);else app.reject(f.name,'Unsupported file type')}});", "non_target_only_failure"),
        "reference": ("const VIDEO=['.3gp','.3gpp','.avi','.flv','.m4v','.mkv','.mts','.m2ts','.ts','.m2t','.mp4','.insv','.mpg','.mpe','.mpeg','.mov','.webm','.wmv'];app.onFiles(files=>{for(const f of files){const ext=f.name.slice(f.name.lastIndexOf('.')).toLowerCase();if(VIDEO.includes(ext))app.accept(f.name);else app.reject(f.name,'Unsupported file type')}});", "pass"),
        "alternative": ("app.onFiles(function(files){files.forEach(function(f){if(/\\.(3gpp?|avi|flv|m4v|mkv|mts|m2ts?|ts|mp4|insv|mp(g|e|eg)|mov|webm|wmv)$/i.test(f.name))app.accept(f.name);else app.reject(f.name)})});", "pass"),
        "target-mutant": ("const VIDEO=['.3gp','.3gpp','.avi','.flv','.m4v','.mkv','.mts','.m2ts','.ts','.mp4','.insv','.mpg','.mpe','.mpeg','.mov','.webm','.wmv'];app.onFiles(files=>{for(const f of files){const ext=f.name.slice(f.name.lastIndexOf('.')).toLowerCase();if(VIDEO.includes(ext))app.accept(f.name);else app.reject(f.name)}});", "target_only_failure"),
        "mime-mutant": ("app.onFiles(files=>files.forEach(f=>f.type.startsWith('video/')?app.accept(f.name):app.reject(f.name)));", "target_only_failure"),
        "non-target-mutant": ("app.onFiles(files=>files.forEach(f=>app.accept(f.name)));", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement the video upload check. When the user selects files, accept each file whose extension is a "
             "supported video format with app.accept(name) and reject every other file as unsupported with "
             f"app.reject(name, reason). Supported video formats and extensions: {VIDEO_LIST_A}.",
        "B": "When files are chosen for upload, decide for each one: a file with the extension of a supported video "
             "format is accepted through app.accept(name), and any other file is turned down as unsupported through "
             f"app.reject(name, reason). The supported video formats are {VIDEO_LIST_B}.",
        "C": "Implement the video upload check. When the user selects files, accept each file whose extension is a "
             "supported video format with app.accept(name) and reject every other file as unsupported with "
             f"app.reject(name, reason). Supported video formats and extensions: {VIDEO_LIST_C}.",
    },
}

LIBRARY_OWNER = {
    "case": "immich-library-single-owner",
    "candidate_id": "rc-c86728bbc029",
    "project_id": "immich",
    "source": {"commit": "eee793bfe4", "file": "docs/docs/features/libraries.md"},
    "title": "External libraries",
    "register": "app.onCreate",
    "control": "Create library button",
    "body": '<h1>External libraries</h1><fieldset><legend>Owner</legend><div id="users"></div></fieldset>'
            '<label>Name <input id="library-name"></label><button id="create" type="button">Create library</button>'
            '<p id="message" role="status"></p><ul id="libraries" aria-label="Libraries"></ul>',
    "state_js": r"""
let libraries=load([]);
const users=window.initialState.users;
const app=Object.freeze({
  onCreate:register,
  users(){return structuredClone(users)},
  libraries(){return structuredClone(libraries)},
  createLibrary(library){if(typeof library!=='object'||library===null||typeof library.name!=='string'||!Array.isArray(library.owners)||!library.owners.length||!library.owners.every(id=>users.some(u=>u.id===id)))throw new Error('name and known owners required');
    libraries.push({name:library.name,owners:[...library.owners]});store(libraries);render()},
  showMessage(text){document.querySelector('#message').textContent=String(text)}
});
function render(){const list=document.querySelector('#libraries');list.replaceChildren();
  for(const l of libraries)list.append(el('li',{'data-name':l.name,'data-owners':l.owners.join(',')},l.name+' — owner: '+l.owners.map(id=>users.find(u=>u.id===id).name).join(', ')))}
const box=document.querySelector('#users');
for(const u of users){const label=el('label');label.append(el('input',{type:'checkbox',name:'owner',value:u.id}),document.createTextNode(' '+u.name));box.append(label)}
document.querySelector('#create').addEventListener('click',()=>{if(behavior)behavior({name:document.querySelector('#library-name').value,owners:[...document.querySelectorAll('input[name=owner]:checked')].map(b=>b.value)})});
""",
    "fixtures": [
        {"state": {"users": [{"id": "u1", "name": "Alice"}, {"id": "u2", "name": "Bob"}, {"id": "u3", "name": "Carol"}]},
         "multi": ["u1", "u2"], "multi_name": "Photos NAS", "single": "u3", "single_name": "Archive"},
        {"state": {"users": [{"id": "v1", "name": "Dan"}, {"id": "v2", "name": "Erin"}, {"id": "v3", "name": "Femi"}]},
         "multi": ["v1", "v2", "v3"], "multi_name": "Family drive", "single": "v2", "single_name": "Camera roll"},
    ],
    "journey_js": r"""
  const n=index+1;const libs=()=>page.locator('#libraries li').evaluateAll(ns=>ns.map(x=>({name:x.dataset.name,owners:x.dataset.owners.split(',')})));
  if((await libs()).length!==0||await page.locator('input[name=owner]').count()!==fixture.state.users.length)throw new InterfaceError('owner choices missing or libraries present');
  for(const id of fixture.multi){const b=page.locator(`input[name=owner][value="${id}"]`);if(await b.isEnabled())await b.click()}
  await (await one(page,'#library-name')).fill(fixture.multi_name);await (await one(page,'#create')).click();await reload(page);
  check(`no_multi_owner_library_${n}`,(await libs()).every(l=>l.owners.length===1));
  const b=page.locator(`input[name=owner][value="${fixture.single}"]`);await b.click();
  await (await one(page,'#library-name')).fill(fixture.single_name);await (await one(page,'#create')).click();await reload(page);
  const created=(await libs()).filter(l=>l.name===fixture.single_name);
  check(`single_owner_library_created_${n}`,created.length===1&&created[0].owners.length===1&&created[0].owners[0]===fixture.single);
""",
    "target": ["no_multi_owner_library_1", "no_multi_owner_library_2"],
    "non_target": ["single_owner_library_created_1", "single_owner_library_created_2"],
    "controls": {
        "reference": ("app.onCreate(f=>{if(f.owners.length!==1){app.showMessage('Select exactly one owner.');return}app.createLibrary(f)});", "pass"),
        "first-owner": ("app.onCreate(function(f){if(!f.owners.length)return;app.createLibrary({name:f.name,owners:[f.owners[0]]})});", "pass"),
        "radio-like": ("document.querySelectorAll('input[name=owner]').forEach(b=>b.addEventListener('change',()=>{if(b.checked)document.querySelectorAll('input[name=owner]').forEach(o=>{if(o!==b)o.checked=false})}));app.onCreate(f=>app.createLibrary(f));", "pass"),
        "target-mutant": ("app.onCreate(f=>app.createLibrary(f));", "target_only_failure"),
        "non-target-mutant": ("app.onCreate(f=>{if(f.owners.length===1)return;app.createLibrary({name:f.name,owners:[f.owners[0]]})});", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement creating an external library. External libraries track assets stored in the filesystem outside "
             "of Immich. When the user clicks Create library, create it with app.createLibrary({name, owners}) using "
             "the entered name and the owner chosen in the Owner section. An external library can only belong to a "
             "single user, which is selected when the library is initially created.",
        "B": "Clicking Create library makes a new external library (a library that tracks assets kept on the "
             "filesystem outside Immich) through app.createLibrary({name, owners}), with the typed name and the owner "
             "picked under Owner. Each external library belongs to exactly one user, chosen when the library is "
             "first created.",
        "C": "Implement creating an external library. External libraries track assets stored in the filesystem outside "
             "of Immich. When the user clicks Create library, create it with app.createLibrary({name, owners}) using "
             "the entered name and the owner chosen in the Owner section.",
    },
}

PATH_SEARCH = {
    "case": "immich-path-search",
    "candidate_id": "rc-b6f382226c41",
    "project_id": "immich",
    "source": {"commit": "90a69e2ba6", "file": "docs/docs/features/searching.md"},
    "title": "Search",
    "register": "app.onSearch",
    "control": "Search button",
    "body": '<h1>Search</h1><p>Search type: Full path or folder</p><label>Query <input id="query"></label>'
            '<button id="search" type="button">Search</button><ul id="results" aria-label="Results"></ul>',
    "state_js": r"""
let shown=[];
const app=Object.freeze({
  onSearch:register,
  assets(){return structuredClone(window.initialState.assets)},
  showResults(ids){if(!Array.isArray(ids)||!ids.every(id=>window.initialState.assets.some(a=>a.id===id)))throw new Error('asset ids required');shown=[...ids];render()}
});
function render(){const list=document.querySelector('#results');list.replaceChildren();
  for(const id of shown){const a=window.initialState.assets.find(x=>x.id===id);list.append(el('li',{'data-id':id},a.originalPath))}}
document.querySelector('#search').addEventListener('click',()=>{if(behavior)behavior(document.querySelector('#query').value)});
""",
    "fixtures": [
        {"state": {"assets": [
            {"id": "a1", "originalPath": "/John/Projects/3D_Printing/2026-07-01/IMG_0001.jpg"},
            {"id": "a2", "originalPath": "/John/Holidays/Lisbon/IMG_2001.jpg"},
            {"id": "a3", "originalPath": "/Maria/Recipes/Bread/IMG_3001.jpg"}]},
         "queries": [["Printing", ["a1"], True], ["3D", ["a1"], True], ["Holidays", ["a2"], False],
                     ["Kitchen", [], False]]},
        {"state": {"assets": [
            {"id": "b1", "originalPath": "/Ana/Work/Client_Reports/2025-11/scan_004.png"},
            {"id": "b2", "originalPath": "/Ana/Family/Birthday/IMG_0005.jpg"},
            {"id": "b3", "originalPath": "/Rui/Work/Invoices/inv_17.png"}]},
         "queries": [["Reports", ["b1"], True], ["2025", ["b1"], True], ["Family", ["b2"], False],
                     ["Work", ["b1", "b3"], False]]},
    ],
    "journey_js": r"""
  const n=index+1;let target=true,other=true;
  if(await page.locator('#results li').count()!==0)throw new InterfaceError('results present before searching');
  for(const [query,expected,isTarget] of fixture.queries){
    await (await one(page,'#query')).fill(query);await (await one(page,'#search')).click();
    const got=(await page.locator('#results li').evaluateAll(ns=>ns.map(x=>x.dataset.id))).sort();
    // target queries: the matching asset must be included; other queries: the exact result set
    if(isTarget)target=target&&expected.every(id=>got.includes(id));
    else other=other&&JSON.stringify(got)===JSON.stringify([...expected].sort());
  }
  check(`part_of_folder_name_matches_${n}`,target);
  check(`whole_folder_and_no_match_${n}`,other);
""",
    "target": ["part_of_folder_name_matches_1", "part_of_folder_name_matches_2"],
    "non_target": ["whole_folder_and_no_match_1", "whole_folder_and_no_match_2"],
    "controls": {
        "reference": ("app.onSearch(q=>{const t=q.trim().toLowerCase();app.showResults(t?app.assets().filter(a=>a.originalPath.toLowerCase().includes(t)).map(a=>a.id):[])});", "pass"),
        "tokens": ("app.onSearch(function(q){var t=q.toLowerCase();app.showResults(app.assets().filter(function(a){return a.originalPath.toLowerCase().split(/[\\/_\\-.]/).some(function(p){return p.indexOf(t)===0})}).map(function(a){return a.id}))});", "pass"),
        "target-mutant": ("app.onSearch(q=>app.showResults(app.assets().filter(a=>a.originalPath.split('/').includes(q)).map(a=>a.id)));", "target_only_failure"),
        "non-target-mutant": ("app.onSearch(()=>app.showResults(app.assets().map(a=>a.id)));", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement the \"Full path or folder\" search mode. When the user clicks Search, show with "
             "app.showResults(ids) the assets that match the query, using each asset's original path from "
             "app.assets(). Use this mode when you know a folder name or part of the original asset path. Example: "
             "for /John/Projects/3D_Printing/2026-07-01/IMG_0001.jpg, searches like Projects, 3D, Printing, or 2026 "
             "match the asset.",
        "B": "Clicking Search in \"Full path or folder\" mode lists, through app.showResults(ids), the assets whose "
             "original path (from app.assets()) matches the query. The mode is meant for when you remember a folder "
             "name or some piece of the original path: the asset at /John/Projects/3D_Printing/2026-07-01/IMG_0001.jpg "
             "is found by Projects, by 3D, by Printing and by 2026.",
        "C": "Implement the \"Full path or folder\" search mode. When the user clicks Search, show with "
             "app.showResults(ids) the assets that match the query, using each asset's original path from "
             "app.assets(). Use this mode when you know a folder name or part of the original asset path.",
    },
}

ORGANIZE_FOODS = {
    "case": "mealie-organize-food-permission",
    "candidate_id": "rc-106bac72c813",
    "project_id": "mealie",
    "source": {"commit": "05521f0e6f",
               "file": "docs/docs/documentation/getting-started/usage/permissions-and-public-access.md"},
    "title": "Foods",
    "register": "app.onAdd",
    "control": "Add food button",
    "body": '<h1>Foods</h1><p id="signed-in"></p><ul id="foods" aria-label="Foods"></ul>'
            '<label>New food <input id="food-name"></label><button id="add-food" type="button">Add food</button>'
            '<p id="message" role="status"></p>',
    "state_js": r"""
let foods=load(window.initialState.foods);
const app=Object.freeze({
  onAdd:register,
  user(){return structuredClone(window.initialState.user)},
  foods(){return structuredClone(foods)},
  createFood(name){if(typeof name!=='string'||!name.trim())throw new Error('food name required');foods.push(name.trim());store(foods);render()},
  showMessage(text){document.querySelector('#message').textContent=String(text)}
});
function render(){document.querySelector('#signed-in').textContent='Signed in as '+window.initialState.user.username;
  const list=document.querySelector('#foods');list.replaceChildren();for(const f of foods)list.append(el('li',{'data-food':f},f))}
document.querySelector('#add-food').addEventListener('click',()=>{if(behavior)behavior(document.querySelector('#food-name').value)});
""",
    "fixtures": [
        {"state": {"user": {"username": "pat", "permissions": {"administrator": False, "invite": True,
                                                              "manageGroup": True, "organizeGroupData": False}},
                   "foods": ["Rice", "Onion"]}, "food": "Salmon"},
        {"state": {"user": {"username": "sam", "permissions": {"administrator": False, "invite": False,
                                                              "manageGroup": False, "organizeGroupData": True}},
                   "foods": ["Garlic"]}, "food": "Tofu"},
    ],
    "journey_js": r"""
  const n=index+1;const foods=()=>page.locator('#foods li').evaluateAll(ns=>ns.map(x=>x.dataset.food));
  if(JSON.stringify(await foods())!==JSON.stringify(fixture.state.foods))throw new InterfaceError('food list missing or changed');
  const button=page.locator('#add-food');const buttonCount=await button.count();
  if(buttonCount>1)throw new InterfaceError('at most one Add food button required');
  const usable=buttonCount===1&&await button.isVisible()&&await button.isEnabled();
  if(n===2&&!usable)throw new InterfaceError('one visible enabled Add food button required with permission');
  if(usable){await (await one(page,'#food-name')).fill(fixture.food);await button.click()}
  await reload(page);
  const after=await foods();
  if(n===1)check('food_not_created_without_organize_1',!after.includes(fixture.food));
  else check('food_created_with_organize_2',after.filter(f=>f===fixture.food).length===1);
  check(`existing_foods_kept_${n}`,fixture.state.foods.every(f=>after.includes(f)));
""",
    "target": ["food_not_created_without_organize_1"],
    "non_target": ["food_created_with_organize_2", "existing_foods_kept_1", "existing_foods_kept_2"],
    "controls": {
        "reference": ("app.onAdd(name=>{if(!app.user().permissions.organizeGroupData){app.showMessage('You need the Organize group data permission to add foods.');return}app.createFood(name)});", "pass"),
        "alternative": ("app.onAdd(function(n){var p=app.user().permissions;if(p.organizeGroupData||p.administrator)app.createFood(n);else app.showMessage('Not allowed')});", "pass"),
        "disabled-add-control": ("document.querySelector('#add-food').disabled=!app.user().permissions.organizeGroupData;app.onAdd(name=>{if(app.user().permissions.organizeGroupData)app.createFood(name)});", "pass"),
        "hidden-add-control": ("document.querySelector('#add-food').hidden=!app.user().permissions.organizeGroupData;app.onAdd(name=>{if(app.user().permissions.organizeGroupData)app.createFood(name)});", "pass"),
        "removed-add-control": ("if(!app.user().permissions.organizeGroupData)document.querySelector('#add-food').remove();app.onAdd(name=>{if(app.user().permissions.organizeGroupData)app.createFood(name)});", "pass"),
        "duplicate-add-control": ("document.querySelector('#add-food').after(document.querySelector('#add-food').cloneNode(true));app.onAdd(name=>{if(app.user().permissions.organizeGroupData)app.createFood(name)});", "interface_error"),
        "target-mutant": ("app.onAdd(name=>app.createFood(name));", "target_only_failure"),
        "manage-group-mutant": ("app.onAdd(name=>{if(app.user().permissions.manageGroup)app.createFood(name)});", "mixed_failure"),
        "non-target-mutant": ("app.onAdd(()=>{});", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement adding a food on the Foods page. When the user clicks Add food, create it with "
             "app.createFood(name); the signed-in user and their permissions come from app.user(). Users can have "
             "these permissions: Administrator (access to administrator tools), Invite (generating invitation links "
             "for other users), Manage group (access to group management areas and settings) and Organize group data "
             "(creating, updating, deleting, and merging group data such as foods, tags, and categories). The Manage "
             "group and Organize group data permissions are separate. Users need Organize group data to add new "
             "foods, tags, or categories, including when creating missing ingredients during recipe parsing.",
        "B": "Clicking Add food on the Foods page creates the food through app.createFood(name); app.user() gives the "
             "signed-in user and their permissions. The possible permissions are Administrator (administrator "
             "tools), Invite (making invitation links for others), Manage group (group management areas and "
             "settings) and Organize group data (creating, updating, deleting and merging group data like foods, "
             "tags and categories). Manage group and Organize group data are independent, and adding a new food, tag "
             "or category, also while creating missing ingredients in recipe parsing, requires Organize group data.",
        "C": "Implement adding a food on the Foods page. When the user clicks Add food, create it with "
             "app.createFood(name); the signed-in user and their permissions come from app.user(). Users can have "
             "these permissions: Administrator (access to administrator tools), Invite (generating invitation links "
             "for other users), Manage group (access to group management areas and settings) and Organize group data "
             "(creating, updating, deleting, and merging group data such as foods, tags, and categories). The Manage "
             "group and Organize group data permissions are separate.",
    },
}

FOOD_LABEL = {
    "case": "mealie-planner-food-label",
    "candidate_id": "rc-0f453b1f0a55",
    "project_id": "mealie",
    "source": {"commit": "cbcd7f3744", "file": "docs/docs/documentation/getting-started/features.md"},
    "title": "Meal planner rule",
    "register": "app.onPreview",
    "control": "Preview recipe pool button",
    "body": '<h1>Meal planner rule</h1><p id="rule"></p><button id="preview" type="button">Preview recipe pool</button>'
            '<ul id="pool" aria-label="Recipe pool"></ul>',
    "state_js": r"""
let pool=[];
const app=Object.freeze({
  onPreview:register,
  rule(){return structuredClone(window.initialState.rule)},
  recipes(){return structuredClone(window.initialState.recipes)},
  showPool(ids){if(!Array.isArray(ids)||!ids.every(id=>window.initialState.recipes.some(r=>r.id===id)))throw new Error('recipe ids required');pool=[...ids];render()}
});
function render(){const r=window.initialState.rule;document.querySelector('#rule').textContent='Rule: ingredient is '+r.value;
  const list=document.querySelector('#pool');list.replaceChildren();
  for(const id of pool)list.append(el('li',{'data-id':id},window.initialState.recipes.find(x=>x.id===id).name))}
document.querySelector('#preview').addEventListener('click',()=>{if(behavior)behavior(app.rule(),app.recipes())});
""",
    "fixtures": [
        {"state": {"rule": {"type": "ingredient", "value": "Fish"}, "recipes": [
            {"id": "r1", "name": "Salmon bowl", "ingredients": [{"food": "Salmon", "label": "Fish"}, {"food": "Rice", "label": "Grain"}]},
            {"id": "r2", "name": "Tuna pasta", "ingredients": [{"food": "Tuna", "label": "Fish"}, {"food": "Pasta", "label": "Grain"}]},
            {"id": "r3", "name": "Fish pie", "ingredients": [{"food": "Fish", "label": "Fish"}, {"food": "Potato", "label": "Vegetable"}]},
            {"id": "r4", "name": "Chicken curry", "ingredients": [{"food": "Chicken", "label": "Meat"}, {"food": "Rice", "label": "Grain"}]}]},
         "by_label": ["r1", "r2"], "by_food": ["r3"], "excluded": ["r4"]},
        {"state": {"rule": {"type": "ingredient", "value": "Citrus"}, "recipes": [
            {"id": "s1", "name": "Lemon tart", "ingredients": [{"food": "Lemon", "label": "Citrus"}, {"food": "Flour", "label": "Baking"}]},
            {"id": "s2", "name": "Orange cake", "ingredients": [{"food": "Orange", "label": "Citrus"}]},
            {"id": "s3", "name": "Apple pie", "ingredients": [{"food": "Apple", "label": "Fruit"}]},
            {"id": "s4", "name": "Citrus salad", "ingredients": [{"food": "Citrus", "label": "Citrus"}]}]},
         "by_label": ["s1", "s2"], "by_food": ["s4"], "excluded": ["s3"]},
    ],
    "journey_js": r"""
  const n=index+1;
  if(await page.locator('#pool li').count()!==0)throw new InterfaceError('pool shown before preview');
  await (await one(page,'#preview')).click();
  const got=await page.locator('#pool li').evaluateAll(ns=>ns.map(x=>x.dataset.id));
  check(`food_label_matches_included_${n}`,fixture.by_label.every(id=>got.includes(id)));
  check(`food_name_matches_included_${n}`,fixture.by_food.every(id=>got.includes(id)));
  check(`non_matching_excluded_${n}`,fixture.excluded.every(id=>!got.includes(id))&&new Set(got).size===got.length);
""",
    "target": ["food_label_matches_included_1", "food_label_matches_included_2"],
    "non_target": ["food_name_matches_included_1", "food_name_matches_included_2",
                   "non_matching_excluded_1", "non_matching_excluded_2"],
    "controls": {
        "reference": ("app.onPreview((rule,recipes)=>app.showPool(recipes.filter(r=>r.ingredients.some(i=>i.food===rule.value||i.label===rule.value)).map(r=>r.id)));", "pass"),
        "case-insensitive": ("app.onPreview(function(rule,recipes){var v=rule.value.toLowerCase();app.showPool(recipes.filter(function(r){return r.ingredients.some(function(i){return i.food.toLowerCase()===v||(i.label||'').toLowerCase()===v})}).map(function(r){return r.id}))});", "pass"),
        "target-mutant": ("app.onPreview((rule,recipes)=>app.showPool(recipes.filter(r=>r.ingredients.some(i=>i.food===rule.value)).map(r=>r.id)));", "target_only_failure"),
        "non-target-mutant": ("app.onPreview((rule,recipes)=>app.showPool(recipes.map(r=>r.id)));", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement the recipe pool preview of a meal planner rule. When the user clicks Preview recipe pool, show "
             "with app.showPool(ids) the recipes from app.recipes() that the rule from app.rule() allows. Plan rules "
             "restrict the pool of recipes based on the Tags and/or Categories of a recipe, or on its ingredients. "
             "Ingredients can be matched by their Food Label as well, so a \"fish day\" only takes one rule instead "
             "of a list of every fish you cook with.",
        "B": "Clicking Preview recipe pool shows, through app.showPool(ids), which recipes from app.recipes() the "
             "meal planner rule from app.rule() lets into the pool. A plan rule narrows the recipe pool by a "
             "recipe's Tags and/or Categories or by its ingredients, and an ingredient also matches through its Food "
             "Label, so one rule is enough for a \"fish day\" instead of listing every kind of fish you cook.",
        "C": "Implement the recipe pool preview of a meal planner rule. When the user clicks Preview recipe pool, show "
             "with app.showPool(ids) the recipes from app.recipes() that the rule from app.rule() allows. Plan rules "
             "restrict the pool of recipes based on the Tags and/or Categories of a recipe, or on its ingredients.",
    },
}

CASES = [M2T, LIBRARY_OWNER, PATH_SEARCH, ORGANIZE_FOODS, FOOD_LABEL]
