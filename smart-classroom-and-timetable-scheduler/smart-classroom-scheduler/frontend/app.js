const days = ["Mon","Tue","Wed","Thu","Fri"];

const state = {
  classes: [], teachers: [], subjects: [], rooms: [], timeslots: [],
  schedule: {},
  currentClassId: null,
};

function colorFor(text){
  // Stable pastel color from string
  let hash = 0;
  for (let i=0;i<text.length;i++) hash = text.charCodeAt(i) + ((hash<<5)-hash);
  const h = Math.abs(hash)%360;
  return `hsl(${h}, 70%, 90%)`;
}

async function api(path, opts={}){
  const res = await fetch(path, {headers:{"Content-Type":"application/json"}, ...opts});
  if(!res.ok){
    const msg = await res.text();
    throw new Error(msg || res.statusText);
  }
  return res.json();
}

async function loadAll(){
  const [classes, teachers, subjects, rooms, timeslots] = await Promise.all([
    api('/api/classes'), api('/api/teachers'), api('/api/subjects'), api('/api/rooms'), api('/api/timeslots')
  ]);
  state.classes = classes; state.teachers = teachers; state.subjects = subjects; state.rooms = rooms; state.timeslots = timeslots;
  state.currentClassId = classes[0]?.id || null;
  refreshRoster();
  refreshLegend();
  await reloadSchedule();
  drawGrid();
  bindControls();
}

async function reloadSchedule(){
  const data = await api('/api/schedule?class_id=' + state.currentClassId);
  state.schedule = data;
}

function refreshRoster(){
  const t = document.getElementById('teacher-list');
  const s = document.getElementById('subject-list');
  const r = document.getElementById('room-list');
  t.innerHTML = state.teachers.map(x=>`<li>${x.name}</li>`).join('');
  s.innerHTML = state.subjects.map(x=>`<li>${x.name}</li>`).join('');
  r.innerHTML = state.rooms.map(x=>`<li>${x.name} — ${x.capacity}</li>`).join('');

  const sel = document.getElementById('class-select');
  sel.innerHTML = state.classes.map(c=>`<option value="${c.id}">${c.name}</option>`).join('');
  sel.value = state.currentClassId;
  sel.onchange = async (e)=>{
    state.currentClassId = parseInt(e.target.value,10);
    await reloadSchedule();
    drawGrid();
  };
}

function refreshLegend(){
  const legend = document.getElementById('legend');
  legend.innerHTML = state.subjects.map(s=>`<div class="chip" style="background:${colorFor(s.name)}">${s.name}</div>`).join('');
}

function drawGrid(){
  const grid = document.getElementById('grid');
  grid.innerHTML = '';
  const labelsByDay = {};
  for(const ts of state.timeslots){
    labelsByDay[ts.day] = labelsByDay[ts.day] || [];
    labelsByDay[ts.day].push(ts.label);
  }
  // header row
  grid.appendChild(cell('','header'));
  for(const lbl of labelsByDay[0]) grid.appendChild(cell(lbl,'header'));
  // rows
  for(let d=0; d<5; d++){
    grid.appendChild(cell(days[d],'header'));
    for(let s=0; s<labelsByDay[d].length; s++){
      const tsObj = state.timeslots.find(t=>t.day===d && t.slot===s);
      const key = `${d},${s}`;
      const entry = (state.schedule[state.currentClassId]||{})[[d,s]];
      const c = document.createElement('div');
      c.className = 'cell';
      if(entry){
        c.style.background = colorFor(entry.subject);
        c.innerHTML = `
          <div class="subject">${entry.subject}</div>
          <div class="meta">${entry.teacher} • ${entry.room}</div>
        `;
      }else{
        c.innerHTML = `<div class="meta">—</div>`;
      }
      c.onclick = ()=> openOverride(d, s, tsObj.label);
      grid.appendChild(c);
    }
  }

  document.getElementById('grid-title').textContent = `Weekly Grid — ${state.classes.find(c=>c.id===state.currentClassId)?.name||''}`;
}

function cell(text, cls){
  const c = document.createElement('div');
  c.className = 'cell ' + (cls||'');
  c.textContent = text;
  return c;
}

function bindControls(){
  document.getElementById('btn-generate').onclick = async ()=>{
    const res = await api('/api/schedule/generate', {method:'POST'});
    await reloadSchedule();
    drawGrid();
    alert(`Placed ${res.stats.placed} of ${res.stats.needed} required periods.`);
  };
  document.getElementById('btn-clear').onclick = async ()=>{
    await api('/api/schedule/clear', {method:'POST'});
    await reloadSchedule();
    drawGrid();
  };
}

function openOverride(day, slot, label){
  const dlg = document.getElementById('override-dialog');
  document.getElementById('slot-label').textContent = `${days[day]} ${label}`;

  // fill selects
  const ovS = document.getElementById('ov-subject');
  ovS.innerHTML = state.subjects.map(s=>`<option value="${s.id}">${s.name}</option>`).join('');

  const ovT = document.getElementById('ov-teacher');
  ovT.innerHTML = state.teachers.map(t=>`<option value="${t.id}">${t.name}</option>`).join('');

  const ovR = document.getElementById('ov-room');
  ovR.innerHTML = state.rooms.map(r=>`<option value="${r.id}">${r.name}</option>`).join('');

  dlg.showModal();

  const save = document.getElementById('ov-save');
  const form = document.getElementById('override-form');
  save.onclick = async (e)=>{
    e.preventDefault();
    try{
      await api('/api/schedule/override', {
        method:'POST',
        body: JSON.stringify({
          class_id: state.currentClassId,
          day, slot,
          subject_id: parseInt(ovS.value,10),
          teacher_id: parseInt(ovT.value,10),
          room_id: parseInt(ovR.value,10)
        })
      });
      dlg.close();
      await reloadSchedule();
      drawGrid();
    }catch(err){
      alert('Could not override: ' + err.message);
    }
  };
}

loadAll().catch(err=>{
  console.error(err);
  alert('Failed to load app: ' + err.message);
});
