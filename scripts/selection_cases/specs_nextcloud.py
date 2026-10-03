"""Nextcloud selection cases (six selected rules; arm A text from the frame-end documentation snapshot)."""

SNAPSHOT = "8d7403649929d9ddb1bd6a5a073d6869071db8c3"

DEVICE_PASSWORD = {
    "case": "nextcloud-device-password-once",
    "candidate_id": "rc-3d153b91ab4e",
    "project_id": "nextcloud",
    "source": {"commit": "a806a064bc", "file": "user_manual/session_management.rst",
               "snapshot": SNAPSHOT, "snapshot_file": "user_manual/session_management.rst"},
    "title": "Security",
    "register": "app.onAction",
    "control": "Create new app password and Show password buttons",
    "body": '<h1>Security</h1><h2>Devices &amp; sessions</h2><ul id="devices" aria-label="Devices"></ul>'
            '<label>App name <input id="app-name"></label>'
            '<button id="create" type="button">Create new app password</button>'
            '<section id="credentials" hidden aria-label="New app password"><p>Login name: <code id="login-name"></code></p>'
            '<p>Password: <code id="password"></code></p><button id="close" type="button">Close</button></section>'
            '<p id="message" role="status"></p>',
    "state_js": r"""
let state=load({devices:window.initialState.devices,next:0});
let shown=null;
const app=Object.freeze({
  onAction:register,
  loginName(){return window.initialState.user},
  devices(){return structuredClone(state.devices)},
  createDevice(name){if(typeof name!=='string'||!name.trim())throw new Error('app name required');
    const password=window.initialState.passwords[state.next];if(password===undefined)throw new Error('no password available');
    state.next+=1;const id='dev'+state.next;state.devices.push({id,name:name.trim()});store(state);render();
    return {id,loginName:window.initialState.user,password}},
  showCredentials(loginName,password){shown={loginName:String(loginName),password:String(password)};render()},
  showMessage(text){document.querySelector('#message').textContent=String(text)}
});
function render(){
  const list=document.querySelector('#devices');list.replaceChildren();
  for(const d of state.devices){const li=el('li',{'data-id':d.id,'data-name':d.name},d.name+' ');
    li.append(el('button',{type:'button',class:'show','data-id':d.id},'Show password'));list.append(li)}
  const c=document.querySelector('#credentials');c.hidden=!shown;c.dataset.password=shown?shown.password:'';
  document.querySelector('#login-name').textContent=shown?shown.loginName:'';
  document.querySelector('#password').textContent=shown?shown.password:'';
}
document.querySelector('#create').addEventListener('click',()=>{if(behavior)behavior({type:'create',name:document.querySelector('#app-name').value})});
document.querySelector('#close').addEventListener('click',()=>{shown=null;render()});
document.querySelector('#devices').addEventListener('click',e=>{const b=e.target.closest('button.show');if(b&&behavior)behavior({type:'show',id:b.dataset.id})});
""",
    "fixtures": [
        {"state": {"user": "alice", "devices": [{"id": "s1", "name": "Firefox on Linux"}],
                   "passwords": ["Xk7pQ-2mW9z-Lr4Tb-8vNc1-Hy3Ds"]},
         "create": ["Laptop sync client"], "reveal": ["Laptop sync client"]},
        {"state": {"user": "bruno", "devices": [{"id": "s7", "name": "Chrome on Windows"},
                                                {"id": "s8", "name": "Android phone"}],
                   "passwords": ["Pq2Rt-Vw8Yx-Bn5Mk-Jh4Gf-Dc6Sa", "Zt3Lm-Qa9Ws-Ed7Rf-Tg2Yh-Uj5Ik"]},
         "create": ["Desktop client", "Calendar app"], "reveal": ["Desktop client", "Calendar app", "Android phone"]},
    ],
    "journey_js": r"""
  const n=index+1;const pw=fixture.state.passwords;
  const rows=()=>page.locator('#devices li').evaluateAll(ns=>ns.map(x=>x.dataset.name));
  const cred=()=>page.locator('#credentials').evaluate(x=>({hidden:x.hidden,password:x.dataset.password}));
  if(JSON.stringify(await rows())!==JSON.stringify(fixture.state.devices.map(d=>d.name))||!(await cred()).hidden)throw new InterfaceError('device list missing or password shown before creating');
  let shownAtCreation=true;
  for(const [i,name] of fixture.create.entries()){
    await (await one(page,'#app-name')).fill(name);await (await one(page,'#create')).click();
    const c=await cred();shownAtCreation=shownAtCreation&&!c.hidden&&c.password===pw[i];
    const close=page.locator('#close');if(await close.isVisible())await close.click();
  }
  let notRevealed=true;
  const reveal=async()=>{for(const name of fixture.reveal){const b=page.locator(`#devices li[data-name="${name}"] button.show`);
      if(await b.count()===1&&await b.isVisible()&&await b.isEnabled())await b.click();
      const text=await page.evaluate(()=>document.body.innerText);const c=await cred();
      notRevealed=notRevealed&&pw.every(p=>!text.includes(p)&&!c.password.includes(p))}};
  await reveal();await reload(page);await reveal();
  check(`password_not_revealed_later_${n}`,notRevealed);
  check(`password_shown_at_creation_${n}`,shownAtCreation);
  check(`devices_listed_${n}`,JSON.stringify(await rows())===JSON.stringify([...fixture.state.devices.map(d=>d.name),...fixture.create]));
""",
    "target": ["password_not_revealed_later_1", "password_not_revealed_later_2"],
    "non_target": ["password_shown_at_creation_1", "password_shown_at_creation_2", "devices_listed_1", "devices_listed_2"],
    "controls": {
        "reference": ("app.onAction(a=>{if(a.type==='create'){const d=app.createDevice(a.name);app.showCredentials(d.loginName,d.password)}else app.showMessage('The device password is only shown when it is created.')});", "pass"),
        "alternative": ("app.onAction(function(a){if(a.type!=='create')return;var d=app.createDevice(a.name.trim()||'Device');app.showCredentials(d.loginName,d.password)});", "pass"),
        "disable-show": ("const off=()=>document.querySelectorAll('#devices button.show').forEach(b=>b.disabled=true);new MutationObserver(off).observe(document.querySelector('#devices'),{childList:true});off();app.onAction(a=>{if(a.type==='create'){const d=app.createDevice(a.name);app.showCredentials(d.loginName,d.password)}});", "pass"),
        "target-mutant": ("const secrets={};app.onAction(a=>{if(a.type==='create'){const d=app.createDevice(a.name);secrets[d.id]=d.password;app.showCredentials(d.loginName,d.password)}else if(secrets[a.id])app.showCredentials(app.loginName(),secrets[a.id])});", "target_only_failure"),
        "stored-secret-mutant": ("const key='device-secrets';const read=()=>JSON.parse(localStorage.getItem(key)||'{}');app.onAction(a=>{if(a.type==='create'){const d=app.createDevice(a.name);localStorage.setItem(key,JSON.stringify({...read(),[d.id]:d.password}));app.showCredentials(d.loginName,d.password)}else if(read()[a.id])app.showCredentials(app.loginName(),read()[a.id])});", "target_only_failure"),
        "non-target-mutant": ("app.onAction(a=>{if(a.type==='create')app.createDevice(a.name)});", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement the device passwords in the Security settings. The list of connected browsers and devices "
             "shows which browsers and devices have connected to the account recently. At the bottom of the list, you "
             "can create a new device-specific password: when the user clicks Create new app password, create it with "
             "app.createDevice(name) using the entered app name; the generated password is used for configuring the "
             "new client and is shown with app.showCredentials(loginName, password). Each device row also has a Show "
             "password button; both kinds of button are handled by app.onAction. You only have access to the device "
             "password when creating it. Nextcloud does not save the plain password, so enter the password on the new "
             "client immediately.",
        "B": "The Security settings list the browsers and devices that recently connected to the account, and each "
             "row carries a Show password button; app.onAction handles that button as well as Create new app password. "
             "Below the list a new device-specific password can be made: clicking Create new app password creates it "
             "through app.createDevice(name) with the typed app name, and the generated password, which is what the "
             "new client is configured with, is displayed through app.showCredentials(loginName, password). The "
             "device password can be seen only at the moment it is created. Because Nextcloud does not store the "
             "plain password, it should be entered on the new client right away.",
        "C": "Implement the device passwords in the Security settings. The list of connected browsers and devices "
             "shows which browsers and devices have connected to the account recently. At the bottom of the list, you "
             "can create a new device-specific password: when the user clicks Create new app password, create it with "
             "app.createDevice(name) using the entered app name; the generated password is used for configuring the "
             "new client and is shown with app.showCredentials(loginName, password). Each device row also has a Show "
             "password button; both kinds of button are handled by app.onAction. Nextcloud does not save the plain "
             "password, so enter the password on the new client immediately.",
    },
}

BREAKOUT_ROOMS = {
    "case": "nextcloud-breakout-rooms",
    "candidate_id": "rc-946f02ef19b6",
    "project_id": "nextcloud",
    "source": {"commit": "a88e2fc1fb", "file": "user_manual/talk/call.rst",
               "snapshot": SNAPSHOT, "snapshot_file": "user_manual/talk/call.rst"},
    "title": "Talk call",
    "register": "app.onCreate",
    "control": "Create breakout rooms button",
    "body": '<h1>Call: <span id="conversation"></span></h1>'
            '<section aria-label="Participants"><h2>Participants</h2><ul id="participants"></ul></section>'
            '<section aria-label="Set up breakout rooms"><h2>Set up breakout rooms</h2>'
            '<label>Number of rooms <input id="room-count" type="number" min="1" value="1"></label>'
            '<button id="create-rooms" type="button">Create breakout rooms</button><p id="message" role="status"></p></section>'
            '<section aria-label="Breakout rooms"><h2>Breakout rooms</h2><ul id="rooms"></ul></section>',
    "state_js": r"""
let rooms=load([]);
const people=window.initialState.participants;
const app=Object.freeze({
  onCreate:register,
  conversation(){return window.initialState.conversation},
  participants(){return structuredClone(people)},
  rooms(){return structuredClone(rooms)},
  createBreakoutRooms(list){if(!Array.isArray(list)||!list.length||!list.every(r=>r&&typeof r.name==='string'&&r.name.trim()&&Array.isArray(r.participants)&&r.participants.every(id=>people.some(p=>p.id===id))))throw new Error('rooms need a name and known participant ids');
    rooms=list.map(r=>({name:r.name.trim(),participants:[...r.participants]}));store(rooms);render()},
  showMessage(text){document.querySelector('#message').textContent=String(text)}
});
function render(){
  document.querySelector('#conversation').textContent=window.initialState.conversation;
  const pl=document.querySelector('#participants');pl.replaceChildren();
  pl.append(el('li',{},window.initialState.moderator+' (you, moderator)'));
  for(const p of people)pl.append(el('li',{'data-id':p.id},p.name));
  const rl=document.querySelector('#rooms');rl.replaceChildren();
  for(const r of rooms)rl.append(el('li',{'data-name':r.name,'data-participants':r.participants.join(',')},
    r.name+': '+(r.participants.map(id=>people.find(p=>p.id===id).name).join(', ')||'no participants')));
}
document.querySelector('#create-rooms').addEventListener('click',()=>{if(behavior)behavior({count:Number(document.querySelector('#room-count').value)})});
""",
    "fixtures": [
        {"state": {"conversation": "Product team", "moderator": "Alice", "participants": [
            {"id": "p1", "name": "Bob"}, {"id": "p2", "name": "Carol"}, {"id": "p3", "name": "Dan"},
            {"id": "p4", "name": "Erin"}, {"id": "p5", "name": "Femi"}]}, "count": 2},
        {"state": {"conversation": "Workshop", "moderator": "Grace", "participants": [
            {"id": "q1", "name": "Hana"}, {"id": "q2", "name": "Ivan"}, {"id": "q3", "name": "Jon"},
            {"id": "q4", "name": "Kemal"}, {"id": "q5", "name": "Lina"}, {"id": "q6", "name": "Mo"},
            {"id": "q7", "name": "Nora"}]}, "count": 3},
    ],
    "journey_js": r"""
  const n=index+1;const ids=fixture.state.participants.map(p=>p.id);
  const read=()=>page.locator('#rooms li').evaluateAll(ns=>ns.map(x=>({name:x.dataset.name,participants:x.dataset.participants?x.dataset.participants.split(','):[]})));
  if((await read()).length!==0||await page.locator('#participants li[data-id]').count()!==ids.length)throw new InterfaceError('participants missing or rooms present before setup');
  await (await one(page,'#room-count')).fill(String(fixture.count));await (await one(page,'#create-rooms')).click();await reload(page);
  const rooms=await read();const assigned=rooms.flatMap(r=>r.participants);
  check(`requested_rooms_created_${n}`,rooms.length===fixture.count&&new Set(rooms.map(r=>r.name)).size===rooms.length);
  check(`each_participant_in_one_room_${n}`,assigned.length===ids.length&&ids.every(id=>assigned.includes(id)));
  check(`rooms_are_smaller_groups_${n}`,rooms.length>1&&rooms.every(r=>r.participants.length>0&&r.participants.length<ids.length));
""",
    "target": ["each_participant_in_one_room_1", "each_participant_in_one_room_2",
               "rooms_are_smaller_groups_1", "rooms_are_smaller_groups_2"],
    "non_target": ["requested_rooms_created_1", "requested_rooms_created_2"],
    "controls": {
        "reference": ("app.onCreate(({count})=>{const rooms=Array.from({length:count},(_,i)=>({name:'Room '+(i+1),participants:[]}));app.participants().forEach((p,i)=>rooms[i%count].participants.push(p.id));app.createBreakoutRooms(rooms)});", "pass"),
        "alternative": ("app.onCreate(function(o){var ps=app.participants(),size=Math.ceil(ps.length/o.count),rooms=[];for(var i=0;i<o.count;i++)rooms.push({name:'Group '+(i+1),participants:ps.slice(i*size,(i+1)*size).map(function(p){return p.id})});app.createBreakoutRooms(rooms)});", "pass"),
        "target-mutant": ("app.onCreate(({count})=>app.createBreakoutRooms(Array.from({length:count},(_,i)=>({name:'Room '+(i+1),participants:[]}))));", "target_only_failure"),
        "everyone-everywhere-mutant": ("app.onCreate(({count})=>app.createBreakoutRooms(Array.from({length:count},(_,i)=>({name:'Room '+(i+1),participants:app.participants().map(p=>p.id)}))));", "target_only_failure"),
        "non-target-mutant": ("app.onCreate(()=>{const rooms=[{name:'Room 1',participants:[]},{name:'Room 2',participants:[]}];app.participants().forEach((p,i)=>rooms[i%2].participants.push(p.id));app.createBreakoutRooms(rooms)});", "non_target_only_failure"),
        "single-room-mutant": ("app.onCreate(()=>app.createBreakoutRooms([{name:'Room 1',participants:app.participants().map(p=>p.id)}]));", "mixed_failure"),
    },
    "arms": {
        "A": "Implement Set up breakout rooms in a Talk call. The moderator enters the number of rooms and clicks Create "
             "breakout rooms; create the rooms with app.createBreakoutRooms(rooms), where each room is {name, "
             "participants} and participants is a list of participant ids from app.participants(). Breakout rooms "
             "allow you to divide a call into smaller groups for more focused discussions. Depending on your "
             "permissions and how your instance is configured, this option may not be available to you.",
        "B": "In a Talk call, the moderator types how many rooms are wanted and clicks Create breakout rooms, which "
             "should create them through app.createBreakoutRooms(rooms); every room is {name, participants}, with "
             "participants given as ids taken from app.participants(). With breakout rooms a call is split into "
             "smaller groups so that discussions can be more focused. This option might not be offered to you, "
             "depending on your permissions and on the configuration of your instance.",
        "C": "Implement Set up breakout rooms in a Talk call. The moderator enters the number of rooms and clicks Create "
             "breakout rooms; create the rooms with app.createBreakoutRooms(rooms), where each room is {name, "
             "participants} and participants is a list of participant ids from app.participants(). Depending on your "
             "permissions and how your instance is configured, this option may not be available to you.",
    },
}

FOLDER_TRASH = {
    "case": "nextcloud-delete-folder-trash",
    "candidate_id": "rc-9d801a70d5d2",
    "project_id": "nextcloud",
    "source": {"commit": "f9dff2cff3", "file": "user_manual/files/deleted_file_management.rst",
               "snapshot": SNAPSHOT, "snapshot_file": "user_manual/files/deleted_file_management.rst"},
    "title": "Files",
    "register": "app.onAction",
    "control": "Delete, Restore and Delete permanently buttons",
    "body": '<h1>Files</h1><h2>All files</h2><ul id="files" aria-label="All files"></ul>'
            '<h2>Deleted files</h2><ul id="deleted" aria-label="Deleted files"></ul><p id="message" role="status"></p>',
    "state_js": r"""
let state=load({files:window.initialState.files,deleted:window.initialState.deleted});
function take(list,id){const i=state[list].findIndex(x=>x.id===id);if(i<0)throw new Error('unknown item');return state[list].splice(i,1)[0]}
const app=Object.freeze({
  onAction:register,
  files(){return structuredClone(state.files)},
  deletedFiles(){return structuredClone(state.deleted)},
  moveToTrash(id){const item=take('files',id);state.deleted.push({id:item.id,name:item.name,type:item.type,originalPath:item.path});store(state);render()},
  restore(id){const item=take('deleted',id);state.files.push({id:item.id,name:item.name,type:item.type,path:item.originalPath});store(state);render()},
  erase(id){take(state.files.some(x=>x.id===id)?'files':'deleted',id);store(state);render()},
  showMessage(text){document.querySelector('#message').textContent=String(text)}
});
function render(){
  const fl=document.querySelector('#files');fl.replaceChildren();
  for(const f of state.files){const li=el('li',{'data-id':f.id,'data-type':f.type},(f.type==='folder'?'Folder ':'File ')+f.path+f.name+' ');
    li.append(el('button',{type:'button',class:'delete','data-id':f.id},'Delete'));fl.append(li)}
  const dl=document.querySelector('#deleted');dl.replaceChildren();
  for(const f of state.deleted){const li=el('li',{'data-id':f.id,'data-type':f.type},(f.type==='folder'?'Folder ':'File ')+f.originalPath+f.name+' ');
    li.append(el('button',{type:'button',class:'restore','data-id':f.id},'Restore'),el('button',{type:'button',class:'erase','data-id':f.id},'Delete permanently'));dl.append(li)}
}
document.querySelector('#files').addEventListener('click',e=>{const b=e.target.closest('button.delete');if(b&&behavior)behavior({type:'delete',item:app.files().find(x=>x.id===b.dataset.id)})});
document.querySelector('#deleted').addEventListener('click',e=>{const b=e.target.closest('button');if(!b||!behavior)return;
  behavior({type:b.classList.contains('restore')?'restore':'delete-permanently',item:app.deletedFiles().find(x=>x.id===b.dataset.id)})});
""",
    "fixtures": [
        {"state": {"files": [{"id": "f1", "name": "Documents", "type": "folder", "path": "/"},
                             {"id": "f2", "name": "Photos", "type": "folder", "path": "/"},
                             {"id": "f3", "name": "notes.md", "type": "file", "path": "/"}],
                   "deleted": [{"id": "t1", "name": "old-report.pdf", "type": "file", "originalPath": "/"},
                               {"id": "t2", "name": "Drafts", "type": "folder", "originalPath": "/"}]},
         "folder": "f2", "restore": "t1", "erase": "t2"},
        {"state": {"files": [{"id": "g1", "name": "Projects", "type": "folder", "path": "/"},
                             {"id": "g2", "name": "Invoices", "type": "folder", "path": "/"},
                             {"id": "g3", "name": "budget.ods", "type": "file", "path": "/"},
                             {"id": "g4", "name": "Music", "type": "folder", "path": "/"}],
                   "deleted": [{"id": "u1", "name": "Archive", "type": "folder", "originalPath": "/"},
                               {"id": "u2", "name": "photo.jpg", "type": "file", "originalPath": "/"},
                               {"id": "u3", "name": "scan.pdf", "type": "file", "originalPath": "/"}]},
         "folder": "g2", "restore": "u1", "erase": "u3"},
    ],
    "journey_js": r"""
  const n=index+1;
  const read=sel=>page.locator(sel+' li').evaluateAll(ns=>ns.map(x=>x.dataset.id));
  if(JSON.stringify(await read('#files'))!==JSON.stringify(fixture.state.files.map(f=>f.id))||JSON.stringify(await read('#deleted'))!==JSON.stringify(fixture.state.deleted.map(f=>f.id)))throw new InterfaceError('files or deleted files missing or changed');
  await (await one(page,`#files li[data-id="${fixture.folder}"] button.delete`)).click();await reload(page);
  let files=await read('#files'),deleted=await read('#deleted');
  check(`folder_removed_from_files_${n}`,!files.includes(fixture.folder)&&fixture.state.files.filter(f=>f.id!==fixture.folder).every(f=>files.includes(f.id)));
  check(`folder_in_trash_bin_${n}`,deleted.filter(id=>id===fixture.folder).length===1);
  await (await one(page,`#deleted li[data-id="${fixture.restore}"] button.restore`)).click();await reload(page);
  files=await read('#files');deleted=await read('#deleted');
  check(`restore_returns_item_${n}`,files.includes(fixture.restore)&&!deleted.includes(fixture.restore));
  await (await one(page,`#deleted li[data-id="${fixture.erase}"] button.erase`)).click();await reload(page);
  files=await read('#files');deleted=await read('#deleted');
  check(`delete_permanently_removes_${n}`,!files.includes(fixture.erase)&&!deleted.includes(fixture.erase));
""",
    "target": ["folder_in_trash_bin_1", "folder_in_trash_bin_2"],
    "non_target": ["folder_removed_from_files_1", "folder_removed_from_files_2", "restore_returns_item_1",
                   "restore_returns_item_2", "delete_permanently_removes_1", "delete_permanently_removes_2"],
    "controls": {
        "reference": ("app.onAction(a=>{if(a.type==='delete')app.moveToTrash(a.item.id);else if(a.type==='restore')app.restore(a.item.id);else app.erase(a.item.id)});", "pass"),
        "alternative": ("app.onAction(function(a){switch(a.type){case 'restore':app.restore(a.item.id);break;case 'delete-permanently':app.erase(a.item.id);break;default:app.moveToTrash(a.item.id);app.showMessage(a.item.name+' moved to Deleted files')}});", "pass"),
        "target-mutant": ("app.onAction(a=>{if(a.type==='restore')app.restore(a.item.id);else app.erase(a.item.id)});", "target_only_failure"),
        "folder-erase-mutant": ("app.onAction(a=>{if(a.type==='delete'){if(a.item.type==='folder')app.erase(a.item.id);else app.moveToTrash(a.item.id)}else if(a.type==='restore')app.restore(a.item.id);else app.erase(a.item.id)});", "target_only_failure"),
        "non-target-mutant": ("app.onAction(a=>{if(a.type==='delete')app.moveToTrash(a.item.id)});", "non_target_only_failure"),
        "no-delete-mutant": ("app.onAction(a=>{if(a.type==='restore')app.restore(a.item.id);else if(a.type==='delete-permanently')app.erase(a.item.id)});", "mixed_failure"),
    },
    "arms": {
        "A": "Implement deleting in Files. Each item under All files has a Delete button, and each item under Deleted "
             "files has Restore and Delete permanently buttons; app.onAction handles all of them. When you delete a "
             "file or folder in Nextcloud, it is normally moved to the trash bin (app.moveToTrash) instead of being "
             "deleted immediately. This allows you to restore it later. Items in the trash bin are permanently deleted "
             "(app.erase) when you manually select Delete permanently, or when the Deleted Files app removes them "
             "according to the retention policy or to free space. Find your deleted files under Deleted files; from "
             "there, you can restore items (app.restore) or delete them permanently.",
        "B": "app.onAction handles the Delete button of every item under All files and the Restore and Delete "
             "permanently buttons of every item under Deleted files. Deleting a file or a folder in Nextcloud does not "
             "normally remove it at once: it goes to the trash bin (app.moveToTrash), so that it can be restored "
             "later. Something in the trash bin is removed for good (app.erase) once you choose Delete permanently, or "
             "when the Deleted Files app clears it because of the retention policy or to make room. Deleted files "
             "lists what you deleted, and there you can restore an item (app.restore) or delete it permanently.",
        "C": "Implement deleting in Files. Each item under All files has a Delete button, and each item under Deleted "
             "files has Restore and Delete permanently buttons; app.onAction handles all of them. Items in the trash "
             "bin are permanently deleted (app.erase) when you manually select Delete permanently, or when the Deleted "
             "Files app removes them according to the retention policy or to free space. Find your deleted files under "
             "Deleted files; from there, you can restore items (app.restore) or delete them permanently.",
    },
}

FAVORITES_UP = {
    "case": "nextcloud-mail-favorites-up",
    "candidate_id": "rc-ab0227c1eb5b",
    "project_id": "nextcloud",
    "source": {"commit": "215c005b07", "file": "user_manual/groupware/mail.rst",
               "snapshot": SNAPSHOT, "snapshot_file": "user_manual/groupware/mail.rst"},
    "title": "Mail",
    "register": "app.onOpen",
    "control": "Inbox button and mail settings",
    "body": '<h1>Mail</h1><nav><button id="open-inbox" type="button">Inbox</button></nav>'
            '<section aria-label="Mail settings"><h2>Mail settings</h2><h3>Sorting</h3>'
            '<label>Sort order <select id="sort-order"><option value="newest">Newest first</option>'
            '<option value="oldest">Oldest first</option></select></label>'
            '<h3>Appearance</h3><label><input id="favorites-up" type="checkbox"> Sort favorites up</label></section>'
            '<section aria-label="Message list"><h2>Message list</h2><div id="list"></div></section>',
    "state_js": r"""
let settings=load(window.initialState.settings);
let opened=false,sections=[];
const msgs=window.initialState.messages;
const app=Object.freeze({
  onOpen:register,
  settings(){return structuredClone(settings)},
  messages(){return structuredClone(msgs)},
  showMessageList(list){if(!Array.isArray(list)||!list.every(s=>s&&Array.isArray(s.ids)&&s.ids.every(id=>msgs.some(m=>m.id===id))))throw new Error('sections of known message ids required');
    sections=list.map(s=>({heading:String(s.heading??''),ids:[...s.ids]}));render()}
});
function render(){
  document.querySelector('#sort-order').value=settings.sortOrder;document.querySelector('#favorites-up').checked=settings.sortFavoritesUp;
  const box=document.querySelector('#list');box.replaceChildren();
  for(const s of sections){const sec=el('section',{'data-ids':s.ids.join(',')});if(s.heading)sec.append(el('h3',{},s.heading));const ul=el('ul');
    for(const id of s.ids){const m=msgs.find(x=>x.id===id);ul.append(el('li',{'data-id':id},(m.favorite?'Favorite · ':'')+m.from+': '+m.subject+' ('+m.date.slice(0,10)+')'))}
    sec.append(ul);box.append(sec)}
}
function open(){opened=true;if(behavior)behavior(app.settings(),app.messages())}
document.querySelector('#open-inbox').addEventListener('click',open);
document.querySelector('#sort-order').addEventListener('change',e=>{settings={...settings,sortOrder:e.target.value};store(settings);if(opened)open()});
document.querySelector('#favorites-up').addEventListener('change',e=>{settings={...settings,sortFavoritesUp:e.target.checked};store(settings);if(opened)open()});
""",
    "fixtures": [
        {"state": {"settings": {"sortOrder": "newest", "sortFavoritesUp": False}, "messages": [
            {"id": "m1", "from": "Ana", "subject": "Quarterly numbers", "date": "2026-09-01T08:00:00Z", "favorite": False},
            {"id": "m2", "from": "Ben", "subject": "Lunch on Friday", "date": "2026-09-03T12:30:00Z", "favorite": False},
            {"id": "m3", "from": "Chen", "subject": "Contract draft", "date": "2026-09-02T09:15:00Z", "favorite": True},
            {"id": "m4", "from": "Dora", "subject": "Server maintenance", "date": "2026-09-05T18:00:00Z", "favorite": False},
            {"id": "m5", "from": "Emil", "subject": "Travel booking", "date": "2026-08-28T07:45:00Z", "favorite": True},
            {"id": "m6", "from": "Fay", "subject": "Newsletter", "date": "2026-09-04T06:00:00Z", "favorite": False}]},
         "order": "newest"},
        {"state": {"settings": {"sortOrder": "newest", "sortFavoritesUp": False}, "messages": [
            {"id": "n1", "from": "Gil", "subject": "Invoice 4471", "date": "2026-07-14T10:00:00Z", "favorite": True},
            {"id": "n2", "from": "Hanne", "subject": "Team photo", "date": "2026-07-10T16:20:00Z", "favorite": False},
            {"id": "n3", "from": "Igor", "subject": "Release notes", "date": "2026-07-12T11:05:00Z", "favorite": False},
            {"id": "n4", "from": "Jana", "subject": "Board agenda", "date": "2026-07-16T08:40:00Z", "favorite": True},
            {"id": "n5", "from": "Kai", "subject": "Parking permit", "date": "2026-07-11T13:00:00Z", "favorite": False}]},
         "order": "oldest"},
    ],
    "journey_js": r"""
  const n=index+1;const msgs=fixture.state.messages;
  const groups=()=>page.locator('#list > section').evaluateAll(ns=>ns.map(x=>x.dataset.ids?x.dataset.ids.split(','):[]).filter(g=>g.length));
  if((await groups()).length!==0||await page.locator('#favorites-up').isChecked())throw new InterfaceError('message list shown or favorites setting on before opening');
  const sorted=[...msgs].sort((a,b)=>fixture.order==='newest'?b.date.localeCompare(a.date):a.date.localeCompare(b.date)).map(m=>m.id);
  await (await one(page,'#open-inbox')).click();
  if(fixture.order==='oldest')await (await one(page,'#sort-order')).selectOption('oldest');
  let g=await groups();
  const offOk=JSON.stringify(g.flat())===JSON.stringify(sorted);
  await (await one(page,'#favorites-up')).check();
  g=await groups();const fav=new Set(msgs.filter(m=>m.favorite).map(m=>m.id));
  check(`favorites_in_top_section_${n}`,g.length===2&&g[0].length===fav.size&&g[0].every(id=>fav.has(id))&&g[1].every(id=>!fav.has(id)));
  check(`order_without_favorites_up_${n}`,offOk);
  check(`every_message_listed_once_${n}`,g.flat().length===msgs.length&&new Set(g.flat()).size===msgs.length);
  const flat=g.flat();const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
  check(`sort_order_kept_${n}`,flat.length>0&&same(flat.filter(id=>fav.has(id)),sorted.filter(id=>fav.has(id)))&&same(flat.filter(id=>!fav.has(id)),sorted.filter(id=>!fav.has(id))));
""",
    "target": ["favorites_in_top_section_1", "favorites_in_top_section_2"],
    "non_target": ["order_without_favorites_up_1", "order_without_favorites_up_2", "every_message_listed_once_1",
                   "every_message_listed_once_2", "sort_order_kept_1", "sort_order_kept_2"],
    "controls": {
        "reference": ("app.onOpen((s,msgs)=>{const ids=[...msgs].sort((a,b)=>s.sortOrder==='oldest'?a.date.localeCompare(b.date):b.date.localeCompare(a.date)).map(m=>m.id);const fav=new Set(msgs.filter(m=>m.favorite).map(m=>m.id));if(s.sortFavoritesUp)app.showMessageList([{heading:'Favorites',ids:ids.filter(id=>fav.has(id))},{heading:'Other messages',ids:ids.filter(id=>!fav.has(id))}]);else app.showMessageList([{heading:'',ids}])});", "pass"),
        "alternative": ("app.onOpen(function(s,msgs){var dir=s.sortOrder==='oldest'?1:-1;var list=msgs.slice().sort(function(a,b){return dir*(Date.parse(a.date)-Date.parse(b.date))});var favs=list.filter(function(m){return m.favorite}),rest=list.filter(function(m){return !m.favorite});var out=s.sortFavoritesUp&&favs.length?[{ids:favs.map(function(m){return m.id})},{ids:rest.map(function(m){return m.id})}]:[{ids:list.map(function(m){return m.id})}];app.showMessageList(out)});", "pass"),
        "target-mutant": ("app.onOpen((s,msgs)=>app.showMessageList([{heading:'',ids:[...msgs].sort((a,b)=>s.sortOrder==='oldest'?a.date.localeCompare(b.date):b.date.localeCompare(a.date)).map(m=>m.id)}]));", "target_only_failure"),
        "inline-pin-mutant": ("app.onOpen((s,msgs)=>{const list=[...msgs].sort((a,b)=>s.sortOrder==='oldest'?a.date.localeCompare(b.date):b.date.localeCompare(a.date));const ids=s.sortFavoritesUp?[...list.filter(m=>m.favorite),...list.filter(m=>!m.favorite)].map(m=>m.id):list.map(m=>m.id);app.showMessageList([{heading:'',ids}])});", "target_only_failure"),
        "non-target-mutant": ("app.onOpen((s,msgs)=>{const ids=[...msgs].sort((a,b)=>b.date.localeCompare(a.date)).map(m=>m.id);const fav=new Set(msgs.filter(m=>m.favorite).map(m=>m.id));if(s.sortFavoritesUp)app.showMessageList([{heading:'Favorites',ids:ids.filter(id=>fav.has(id))},{heading:'Other messages',ids:ids.filter(id=>!fav.has(id))}]);else app.showMessageList([{heading:'',ids}])});", "non_target_only_failure"),
        "always-pinned-mutant": ("app.onOpen((s,msgs)=>{const ids=[...msgs].sort((a,b)=>s.sortOrder==='oldest'?a.date.localeCompare(b.date):b.date.localeCompare(a.date)).map(m=>m.id);const fav=new Set(msgs.filter(m=>m.favorite).map(m=>m.id));app.showMessageList([{heading:'Favorites',ids:ids.filter(id=>fav.has(id))},{heading:'Other messages',ids:ids.filter(id=>!fav.has(id))}])});", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement the message list of the Mail inbox. When the user opens Inbox, or changes a mail setting while "
             "the list is open, app.onOpen is called with app.settings() and app.messages(); show the list with "
             "app.showMessageList(sections), where each section is {heading, ids} and is shown as its own block of "
             "the list. Change sort order: in the mail settings under Sorting you can choose Oldest or Newest mail "
             "first; this change applies across all your accounts and folders. Sort favorites up. This setting allows "
             "you to show messages set as favorite in a separate section on top of the message list. To use it, visit "
             "mail settings, go to Appearance and enable sorting favorites up.",
        "B": "app.onOpen is called with app.settings() and app.messages() whenever the user opens Inbox or changes a "
             "mail setting while the list is displayed, and it should render the list through "
             "app.showMessageList(sections), each section being {heading, ids} and appearing as a separate block. "
             "Under Sorting in the mail settings, Newest or Oldest mail first can be chosen, and the choice holds for "
             "all accounts and folders. The Sort favorites up setting, enabled from the Appearance part of the mail "
             "settings, puts the messages marked as favorite in a section of their own at the top of the message "
             "list.",
        "C": "Implement the message list of the Mail inbox. When the user opens Inbox, or changes a mail setting while "
             "the list is open, app.onOpen is called with app.settings() and app.messages(); show the list with "
             "app.showMessageList(sections), where each section is {heading, ids} and is shown as its own block of "
             "the list. Change sort order: in the mail settings under Sorting you can choose Oldest or Newest mail "
             "first; this change applies across all your accounts and folders. Sort favorites up. To use it, visit "
             "mail settings, go to Appearance and enable sorting favorites up.",
    },
}

MAIL_DELEGATION = {
    "case": "nextcloud-mail-delegation",
    "candidate_id": "rc-c38fa60b1164",
    "project_id": "nextcloud",
    "source": {"commit": "58b21da96d", "file": "user_manual/groupware/mail.rst",
               "snapshot": SNAPSHOT, "snapshot_file": "user_manual/groupware/mail.rst"},
    "title": "Mail accounts",
    "register": "app.onDelegation",
    "control": "Delegate access and Revoke access buttons",
    "body": '<h1>Mail</h1><p id="signed-in"></p>'
            '<section aria-label="Your accounts"><h2>Your accounts</h2><ul id="accounts"></ul></section>'
            '<section id="dialog" hidden aria-label="Delegation"><h2>Delegation: <span id="dialog-account"></span></h2>'
            '<ul id="delegates" aria-label="Delegates"></ul><button id="add-delegate" type="button">Add delegate</button>'
            '<div id="picker" hidden><label>Select a user <select id="user"></select></label>'
            '<button id="delegate-access" type="button">Delegate access</button></div>'
            '<div id="confirm" hidden><p id="confirm-text"></p><button id="revoke-access" type="button">Revoke access</button></div>'
            '<button id="close-dialog" type="button">Close</button></section>'
            '<section aria-label="Account lists"><h2>Account lists</h2><div id="account-lists"></div></section>'
            '<p id="message" role="status"></p>',
    "state_js": r"""
const users=window.initialState.users,accounts=window.initialState.accounts,actor=window.initialState.actor;
let state=load({delegations:[],lists:window.initialState.lists});
let dialog=null,picking=false,pending=null;
const known=(a,u)=>accounts.some(x=>x.id===a)&&users.some(x=>x.id===u);
const app=Object.freeze({
  onDelegation:register,
  actor(){return structuredClone(users.find(u=>u.id===actor))},
  users(){return structuredClone(users)},
  accounts(){return structuredClone(accounts)},
  delegates(accountId){return state.delegations.filter(d=>d.accountId===accountId).map(d=>d.userId)},
  addDelegate(accountId,userId){if(!known(accountId,userId))throw new Error('unknown account or user');
    if(!state.delegations.some(d=>d.accountId===accountId&&d.userId===userId))state.delegations.push({accountId,userId});store(state);render()},
  removeDelegate(accountId,userId){state.delegations=state.delegations.filter(d=>!(d.accountId===accountId&&d.userId===userId));store(state);render()},
  accountList(userId){return structuredClone(state.lists[userId]??[])},
  setAccountList(userId,entries){if(!users.some(u=>u.id===userId)||!Array.isArray(entries)||!entries.every(e=>e&&accounts.some(a=>a.id===e.accountId)&&(e.tag===undefined||typeof e.tag==='string')))throw new Error('known user and entries {accountId, tag} required');
    state.lists[userId]=entries.map(e=>({accountId:e.accountId,tag:e.tag??''}));store(state);render()},
  showMessage(text){document.querySelector('#message').textContent=String(text)}
});
function render(){
  const name=id=>users.find(u=>u.id===id).name;
  document.querySelector('#signed-in').textContent='Signed in as '+name(actor);
  const al=document.querySelector('#accounts');al.replaceChildren();
  for(const a of accounts.filter(a=>a.owner===actor)){const ds=app.delegates(a.id);
    const li=el('li',{'data-id':a.id,'data-delegates':ds.join(',')},a.email+(a.provisioned?' (provisioned)':'')+(ds.length?' — delegates: '+ds.map(name).join(', '):'')+' ');
    li.append(el('button',{type:'button',class:'delegate','data-id':a.id},'Delegate account'));al.append(li)}
  document.querySelector('#dialog').hidden=!dialog;
  const dl=document.querySelector('#delegates');dl.replaceChildren();
  if(dialog){document.querySelector('#dialog-account').textContent=accounts.find(a=>a.id===dialog).email;
    for(const u of app.delegates(dialog)){const li=el('li',{'data-user':u},name(u)+' ');li.append(el('button',{type:'button',class:'revoke','data-user':u},'Revoke'));dl.append(li)}}
  document.querySelector('#picker').hidden=!picking;document.querySelector('#confirm').hidden=!pending;
  document.querySelector('#confirm-text').textContent=pending?'Revoke access for '+name(pending)+'?':'';
  const box=document.querySelector('#account-lists');box.replaceChildren();
  for(const u of users){const sec=el('section',{'data-user':u.id});sec.append(el('h3',{},'Account list of '+u.name));const ul=el('ul');
    for(const e of state.lists[u.id]??[])ul.append(el('li',{'data-account':e.accountId,'data-tag':e.tag},accounts.find(a=>a.id===e.accountId).email+(e.tag?' ('+e.tag+')':'')));
    sec.append(ul);box.append(sec)}
}
const select=document.querySelector('#user');
for(const u of users.filter(u=>u.id!==actor))select.append(el('option',{value:u.id},u.name));
document.querySelector('#accounts').addEventListener('click',e=>{const b=e.target.closest('button.delegate');if(!b)return;dialog=b.dataset.id;picking=false;pending=null;render()});
document.querySelector('#add-delegate').addEventListener('click',()=>{picking=true;pending=null;render()});
document.querySelector('#delegate-access').addEventListener('click',()=>{const ev={type:'delegate',accountId:dialog,userId:select.value};picking=false;render();if(behavior)behavior(ev)});
document.querySelector('#delegates').addEventListener('click',e=>{const b=e.target.closest('button.revoke');if(!b)return;pending=b.dataset.user;picking=false;render()});
document.querySelector('#revoke-access').addEventListener('click',()=>{const ev={type:'revoke',accountId:dialog,userId:pending};pending=null;render();if(behavior)behavior(ev)});
document.querySelector('#close-dialog').addEventListener('click',()=>{dialog=null;picking=false;pending=null;render()});
""",
    "fixtures": [
        {"state": {"actor": "alice",
                   "users": [{"id": "alice", "name": "Alice"}, {"id": "bob", "name": "Bob"}, {"id": "carol", "name": "Carol"}],
                   "accounts": [{"id": "a1", "email": "alice@example.org", "owner": "alice", "provisioned": False},
                                {"id": "b1", "email": "bob@example.org", "owner": "bob", "provisioned": False},
                                {"id": "c1", "email": "carol@example.org", "owner": "carol", "provisioned": False}],
                   "lists": {"alice": [{"accountId": "a1", "tag": "Default"}],
                             "bob": [{"accountId": "b1", "tag": "Default"}],
                             "carol": [{"accountId": "c1", "tag": "Default"}]}},
         "delegate": ["a1", "bob"], "provisioned": None},
        {"state": {"actor": "dana",
                   "users": [{"id": "dana", "name": "Dana"}, {"id": "erin", "name": "Erin"}, {"id": "femi", "name": "Femi"}],
                   "accounts": [{"id": "d1", "email": "dana@example.net", "owner": "dana", "provisioned": False},
                                {"id": "d2", "email": "team@example.net", "owner": "dana", "provisioned": False},
                                {"id": "d3", "email": "dana@corp.example.net", "owner": "dana", "provisioned": True},
                                {"id": "e1", "email": "erin@example.net", "owner": "erin", "provisioned": False},
                                {"id": "f1", "email": "femi@example.net", "owner": "femi", "provisioned": False}],
                   "lists": {"dana": [{"accountId": "d1", "tag": "Default"}, {"accountId": "d2", "tag": ""},
                                      {"accountId": "d3", "tag": ""}],
                             "erin": [{"accountId": "e1", "tag": "Default"}],
                             "femi": [{"accountId": "f1", "tag": "Default"}]}},
         "delegate": ["d2", "femi"], "provisioned": ["d3", "erin"]},
    ],
    "journey_js": r"""
  const n=index+1;const [acc,user]=fixture.delegate;
  const state=()=>page.evaluate(()=>({acc:Object.fromEntries([...document.querySelectorAll('#accounts li')].map(x=>[x.dataset.id,x.dataset.delegates])),
    lists:Object.fromEntries([...document.querySelectorAll('#account-lists section')].map(s=>[s.dataset.user,[...s.querySelectorAll('li')].map(l=>[l.dataset.account,l.dataset.tag])]))}));
  const expected=Object.fromEntries(fixture.state.users.map(u=>[u.id,(fixture.state.lists[u.id]??[]).map(e=>[e.accountId,e.tag])]));
  const s0=await state();
  if(JSON.stringify(s0.lists)!==JSON.stringify(expected)||Object.values(s0.acc).some(v=>v!==''))throw new InterfaceError('accounts or account lists missing or changed');
  const usable=async sel=>{const x=page.locator(sel);return await x.count()===1&&await x.isVisible()&&await x.isEnabled()};
  const delegate=async(a,u,strict)=>{
    for(const sel of [`#accounts li[data-id="${a}"] button.delegate`,'#add-delegate','#user','#delegate-access']){
      if(!strict&&!await usable(sel))return;const node=await one(page,sel);
      if(sel==='#user')await node.selectOption(u);else await node.click()}
    await reload(page)};
  const delegatesOf=(s,a)=>(s.acc[a]||'').split(',').filter(Boolean);
  await delegate(acc,user,true);
  const s1=await state();const mine=(s1.lists[user]||[]).filter(e=>e[0]===acc);
  check(`delegate_sees_delegated_account_${n}`,mine.length===1&&/delegat/i.test(mine[0][1]||''));
  const recorded=delegatesOf(s1,acc).includes(user);
  check(`delegation_recorded_${n}`,recorded);
  check(`other_account_lists_unchanged_${n}`,Object.entries(expected).every(([u,l])=>JSON.stringify((s1.lists[u]||[]).filter(e=>!(u===user&&e[0]===acc)))===JSON.stringify(l)));
  if(fixture.provisioned){const [pa,pu]=fixture.provisioned;await delegate(pa,pu,false);await reload(page);const s=await state();
    check(`provisioned_not_delegated_${n}`,delegatesOf(s,pa).length===0&&!(s.lists[pu]||[]).some(e=>e[0]===pa))}
  await (await one(page,`#accounts li[data-id="${acc}"] button.delegate`)).click();
  const revoke=`#delegates li[data-user="${user}"] button.revoke`;
  if(await usable(revoke)){await page.locator(revoke).click();if(await usable('#revoke-access'))await page.locator('#revoke-access').click()}
  await reload(page);
  check(`revoke_removes_delegate_${n}`,recorded&&!delegatesOf(await state(),acc).includes(user));
""",
    "target": ["delegate_sees_delegated_account_1", "delegate_sees_delegated_account_2"],
    "non_target": ["delegation_recorded_1", "delegation_recorded_2", "other_account_lists_unchanged_1",
                   "other_account_lists_unchanged_2", "provisioned_not_delegated_2", "revoke_removes_delegate_1",
                   "revoke_removes_delegate_2"],
    "controls": {
        "reference": ("app.onDelegation(e=>{const acc=app.accounts().find(a=>a.id===e.accountId);if(e.type==='delegate'){if(acc.provisioned){app.showMessage('Provisioned accounts cannot be delegated.');return}app.addDelegate(e.accountId,e.userId);const list=app.accountList(e.userId).filter(x=>x.accountId!==e.accountId);app.setAccountList(e.userId,[...list,{accountId:e.accountId,tag:'Delegated'}])}else{app.removeDelegate(e.accountId,e.userId);app.setAccountList(e.userId,app.accountList(e.userId).filter(x=>x.accountId!==e.accountId))}});", "pass"),
        "alternative": ("app.onDelegation(function(e){var acc=app.accounts().filter(function(a){return a.id===e.accountId})[0];if(e.type==='revoke'){app.removeDelegate(e.accountId,e.userId);return}if(acc.provisioned)return;app.addDelegate(e.accountId,e.userId);var list=app.accountList(e.userId);if(!list.some(function(x){return x.accountId===e.accountId}))list.unshift({accountId:e.accountId,tag:'delegated by '+app.actor().name});app.setAccountList(e.userId,list)});", "pass"),
        "target-mutant": ("app.onDelegation(e=>{if(e.type==='delegate'){if(app.accounts().find(a=>a.id===e.accountId).provisioned)return;app.addDelegate(e.accountId,e.userId)}else app.removeDelegate(e.accountId,e.userId)});", "target_only_failure"),
        "untagged-mutant": ("app.onDelegation(e=>{if(e.type==='delegate'){if(app.accounts().find(a=>a.id===e.accountId).provisioned)return;app.addDelegate(e.accountId,e.userId);app.setAccountList(e.userId,[...app.accountList(e.userId),{accountId:e.accountId}])}else app.removeDelegate(e.accountId,e.userId)});", "target_only_failure"),
        "non-target-mutant": ("app.onDelegation(e=>{if(e.type==='delegate'&&!app.accounts().find(a=>a.id===e.accountId).provisioned)app.setAccountList(e.userId,[...app.accountList(e.userId),{accountId:e.accountId,tag:'Delegated'}])});", "non_target_only_failure"),
        "provisioned-mutant": ("app.onDelegation(e=>{if(e.type==='delegate'){app.addDelegate(e.accountId,e.userId);app.setAccountList(e.userId,[...app.accountList(e.userId),{accountId:e.accountId,tag:'Delegated'}])}else app.removeDelegate(e.accountId,e.userId)});", "non_target_only_failure"),
    },
    "arms": {
        "A": "Implement native account delegation in Mail. Native account delegation lets you grant other Nextcloud "
             "users access to one of your mail accounts directly from the app, without any server-side alias "
             "configuration. A delegate can do everything the account owner can (send, receive, and delete mail on "
             "your behalf) except deleting the account or updating its authentication information. To delegate one of "
             "your accounts, click Delegate account on the account, click Add delegate in the Delegation dialog, "
             "choose the Nextcloud user in the Select a user field and confirm with Delegate access; app.onDelegation "
             "then receives {type: 'delegate', accountId, userId}, and the delegate is recorded with "
             "app.addDelegate(accountId, userId). The shared account then appears in the delegate's account list "
             "(app.accountList(userId) and app.setAccountList(userId, entries), entries being {accountId, tag}), "
             "marked as delegated. To remove access, open the Delegation dialog again, click Revoke next to the "
             "delegate and confirm with Revoke access; app.onDelegation then receives {type: 'revoke', accountId, "
             "userId}, and the delegate is removed with app.removeDelegate(accountId, userId). Provisioned accounts "
             "cannot be delegated.",
        "B": "With native account delegation, the app itself lets you give other Nextcloud users access to one of "
             "your mail accounts, with no alias configuration on the server. Delegates may do anything the owner of "
             "the account may do, such as sending, receiving and deleting mail for you, apart from deleting the "
             "account or changing its authentication information. You delegate an account by clicking its Delegate "
             "account button, then Add delegate in the Delegation dialog, picking the Nextcloud user in Select a user "
             "and confirming with Delegate access; app.onDelegation receives {type: 'delegate', accountId, userId} "
             "and records the delegate through app.addDelegate(accountId, userId). After that the shared account is "
             "listed, marked as delegated, in the account list of the delegate (read with app.accountList(userId) "
             "and written with app.setAccountList(userId, entries), each entry being {accountId, tag}). Access is "
             "withdrawn by reopening the Delegation dialog, clicking Revoke beside the delegate and confirming with "
             "Revoke access; app.onDelegation receives {type: 'revoke', accountId, userId} and removes the delegate "
             "through app.removeDelegate(accountId, userId). A provisioned account cannot be delegated.",
        "C": "Implement native account delegation in Mail. Native account delegation lets you grant other Nextcloud "
             "users access to one of your mail accounts directly from the app, without any server-side alias "
             "configuration. A delegate can do everything the account owner can (send, receive, and delete mail on "
             "your behalf) except deleting the account or updating its authentication information. To delegate one of "
             "your accounts, click Delegate account on the account, click Add delegate in the Delegation dialog, "
             "choose the Nextcloud user in the Select a user field and confirm with Delegate access; app.onDelegation "
             "then receives {type: 'delegate', accountId, userId}, and the delegate is recorded with "
             "app.addDelegate(accountId, userId). To remove access, open the Delegation dialog again, click Revoke "
             "next to the delegate and confirm with Revoke access; app.onDelegation then receives {type: 'revoke', "
             "accountId, userId}, and the delegate is removed with app.removeDelegate(accountId, userId). Provisioned "
             "accounts cannot be delegated.",
    },
}

CALENDAR_TALK = {
    "case": "nextcloud-calendar-talk-location",
    "candidate_id": "rc-e594b40135ff",
    "project_id": "nextcloud",
    "source": {"commit": "ce0623394e", "file": "user_manual/talk/advanced_features.rst",
               "snapshot": SNAPSHOT, "snapshot_file": "user_manual/talk/calendar_integration.rst"},
    "title": "Calendar and Talk",
    "register": "app.onSave",
    "control": "Save button of the new event",
    "body": '<h1>Workspace</h1><section aria-label="Calendar"><h2>Calendar</h2><h3>New event</h3>'
            '<label>Title <input id="event-title"></label><label>Start <input id="event-start" type="datetime-local"></label>'
            '<fieldset><legend>Location</legend>'
            '<label><input type="radio" name="location-type" value="address" checked> Address</label>'
            '<label><input type="radio" name="location-type" value="talk"> Talk conversation</label>'
            '<label>Location <input id="location" list="conversation-names"></label>'
            '<datalist id="conversation-names"></datalist></fieldset>'
            '<button id="save-event" type="button">Save</button><p id="message" role="status"></p>'
            '<h3>Events</h3><ul id="events" aria-label="Events"></ul></section>'
            '<section aria-label="Talk"><h2>Talk</h2><h3>Conversations</h3><ul id="conversations" aria-label="Conversations"></ul></section>',
    "state_js": r"""
let state=load({conversations:window.initialState.conversations,events:[],next:0});
const LINK='https://cloud.example.com/call/';
const app=Object.freeze({
  onSave:register,
  conversations(){return structuredClone(state.conversations)},
  createConversation(name){if(typeof name!=='string'||!name.trim())throw new Error('conversation name required');
    state.next+=1;const token=window.initialState.tokenPrefix+state.next;state.conversations.push({token,name:name.trim()});store(state);render();return token},
  conversationLink(token){if(!state.conversations.some(c=>c.token===token))throw new Error('unknown conversation');return LINK+token},
  events(){return structuredClone(state.events)},
  createEvent(ev){if(!ev||typeof ev.title!=='string'||!ev.title.trim()||typeof ev.start!=='string'||typeof ev.location!=='string')throw new Error('title, start and location required');
    state.events.push({title:ev.title.trim(),start:ev.start,location:ev.location});store(state);render()},
  showMessage(text){document.querySelector('#message').textContent=String(text)}
});
function render(){
  const dl=document.querySelector('#conversation-names');dl.replaceChildren();for(const c of state.conversations)dl.append(el('option',{value:c.name}));
  const cl=document.querySelector('#conversations');cl.replaceChildren();for(const c of state.conversations)cl.append(el('li',{'data-token':c.token,'data-name':c.name},c.name));
  const list=document.querySelector('#events');list.replaceChildren();
  for(const e of state.events)list.append(el('li',{'data-title':e.title,'data-start':e.start,'data-location':e.location},e.title+' — '+e.start.replace('T',' ')+(e.location?' — '+e.location:'')));
}
document.querySelector('#save-event').addEventListener('click',()=>{if(behavior)behavior({title:document.querySelector('#event-title').value,start:document.querySelector('#event-start').value,
  location:{type:document.querySelector('input[name=location-type]:checked').value,value:document.querySelector('#location').value}})});
""",
    "fixtures": [
        {"state": {"tokenPrefix": "nw", "conversations": [{"token": "t1a9", "name": "Team weekly"},
                                                          {"token": "t2b7", "name": "Design"}]},
         "events": [{"title": "Weekly sync", "start": "2026-10-12T09:00", "type": "talk", "value": "Team weekly"},
                    {"title": "Sprint review", "start": "2026-10-16T14:00", "type": "talk", "value": "Sprint review"}]},
        {"state": {"tokenPrefix": "ev", "conversations": [{"token": "k4c2", "name": "Ops"},
                                                          {"token": "k5d8", "name": "Release planning"}]},
         "events": [{"title": "Board meeting", "start": "2026-11-03T10:30", "type": "address", "value": "Room 4.2"},
                    {"title": "Release party", "start": "2026-11-07T18:00", "type": "talk", "value": "Release party"}]},
    ],
    "journey_js": r"""
  const n=index+1;const LINK='https://cloud.example.com/call/';const c0=fixture.state.conversations;
  const convs=()=>page.locator('#conversations li').evaluateAll(ns=>ns.map(x=>({token:x.dataset.token,name:x.dataset.name})));
  const events=()=>page.locator('#events li').evaluateAll(ns=>ns.map(x=>({title:x.dataset.title,start:x.dataset.start,location:x.dataset.location})));
  if(JSON.stringify(await convs())!==JSON.stringify(c0)||(await events()).length!==0)throw new InterfaceError('conversations missing or events present before saving');
  const save=async e=>{await (await one(page,'#event-title')).fill(e.title);await (await one(page,'#event-start')).fill(e.start);
    await (await one(page,`input[name=location-type][value=${e.type}]`)).check();await (await one(page,'#location')).fill(e.value);
    await (await one(page,'#save-event')).click();await reload(page)};
  const [first,second]=fixture.events;
  await save(first);let cs=await convs();let evs=await events();const e1=evs.filter(e=>e.title===first.title);
  if(first.type==='talk'){const t=c0.find(c=>c.name===first.value).token;
    check(`existing_conversation_linked_${n}`,e1.length===1&&e1[0].location===LINK+t);
    check(`existing_conversation_not_duplicated_${n}`,JSON.stringify(cs)===JSON.stringify(c0));
  }else check(`address_location_kept_${n}`,e1.length===1&&e1[0].location===first.value&&JSON.stringify(cs)===JSON.stringify(c0));
  await save(second);cs=await convs();evs=await events();const e2=evs.filter(e=>e.title===second.title);const made=cs.filter(c=>c.name===second.value);
  check(`new_conversation_created_${n}`,made.length===1&&!c0.some(c=>c.token===made[0].token)&&e2.length===1&&e2[0].location===LINK+made[0].token);
  check(`events_saved_${n}`,evs.length===2&&[first,second].every(f=>evs.filter(e=>e.title===f.title&&e.start===f.start).length===1));
""",
    "target": ["new_conversation_created_1", "new_conversation_created_2", "existing_conversation_not_duplicated_1"],
    "non_target": ["existing_conversation_linked_1", "address_location_kept_2", "events_saved_1", "events_saved_2"],
    "controls": {
        "reference": ("app.onSave(f=>{let location=f.location.value.trim();if(f.location.type==='talk'){const c=app.conversations().find(c=>c.name===location);location=app.conversationLink(c?c.token:app.createConversation(location))}app.createEvent({title:f.title,start:f.start,location})});", "pass"),
        "alternative": ("app.onSave(function(f){var loc=f.location.value.trim();if(f.location.type==='talk'){var hit=app.conversations().filter(function(c){return c.name.toLowerCase()===loc.toLowerCase()})[0];var token=hit?hit.token:app.createConversation(loc);loc=app.conversationLink(token);app.showMessage('Talk conversation linked')}app.createEvent({title:f.title.trim(),start:f.start,location:loc})});", "pass"),
        "target-mutant": ("app.onSave(f=>{let location=f.location.value.trim();if(f.location.type==='talk'){const c=app.conversations().find(c=>c.name===location);if(c)location=app.conversationLink(c.token)}app.createEvent({title:f.title,start:f.start,location})});", "target_only_failure"),
        "prefix-match-mutant": ("app.onSave(f=>{let location=f.location.value.trim();if(f.location.type==='talk'){const c=app.conversations().find(c=>c.name===location||c.name.startsWith(location.split(' ')[0]));location=app.conversationLink(c?c.token:app.createConversation(location))}app.createEvent({title:f.title,start:f.start,location})});", "target_only_failure"),
        "non-target-mutant": ("app.onSave(f=>{let location='';if(f.location.type==='talk'){const name=f.location.value.trim();const c=app.conversations().find(c=>c.name===name);location=app.conversationLink(c?c.token:app.createConversation(name))}app.createEvent({title:f.title,start:f.start,location})});", "non_target_only_failure"),
        "always-create-mutant": ("app.onSave(f=>{let location=f.location.value.trim();if(f.location.type==='talk')location=app.conversationLink(app.createConversation(location));app.createEvent({title:f.title,start:f.start,location})});", "mixed_failure"),
    },
    "arms": {
        "A": "Implement saving a new event in Calendar. When the user clicks Save, create the event with "
             "app.createEvent({title, start, location}). When creating a new event in Calendar, you can set a Talk "
             "conversation as event location (Location type Talk conversation, with the conversation name entered in "
             "Location); otherwise the location is the entered address. This will create a new conversation if one "
             "does not exist yet (app.createConversation(name) returns its token). When the event is created, you will "
             "see a link to the conversation in the event details: the event location is "
             "app.conversationLink(token). The conversation will also appear in the list of conversations.",
        "B": "Clicking Save on a new Calendar event creates it through app.createEvent({title, start, location}). The "
             "event location can be a Talk conversation (choose the Talk conversation location type and type the "
             "conversation name in Location) or else the typed address. If no such conversation exists yet, a new one "
             "is created (app.createConversation(name), which returns its token). Once the event exists, its details "
             "show a link to the conversation, so the event location is app.conversationLink(token), and the "
             "conversation is also listed among the conversations.",
        "C": "Implement saving a new event in Calendar. When the user clicks Save, create the event with "
             "app.createEvent({title, start, location}). When creating a new event in Calendar, you can set a Talk "
             "conversation as event location (Location type Talk conversation, with the conversation name entered in "
             "Location); otherwise the location is the entered address. When the event is created, you will "
             "see a link to the conversation in the event details: the event location is "
             "app.conversationLink(token). The conversation will also appear in the list of conversations.",
    },
}

CASES = [DEVICE_PASSWORD, BREAKOUT_ROOMS, FOLDER_TRASH, FAVORITES_UP, MAIL_DELEGATION, CALENDAR_TALK]
