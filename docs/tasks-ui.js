(async()=>{
  const {esc}=WatchUI,$=id=>document.getElementById(id);
  try {
    const response=await fetch('task-matches.json',{cache:'no-store'});
    if(!response.ok)throw Error('Не удалось загрузить основания подбора');
    const data=await response.json();
    $('task').innerHTML='<option value="">Выберите задачу</option>'+data.tasks.map(t=>`<option value="${esc(t.id)}">${esc(t.title)}</option>`).join('');
    const requested=new URLSearchParams(location.search).get('task');
    if(data.tasks.some(t=>t.id===requested))$('task').value=requested;
    function render(){
      const task=$('task').value,status=$('status').value,q=$('query').value.toLocaleLowerCase('ru');
      const rows=data.matches.filter(x=>x.task===task&&(!status||x.status===status)&&(!q||[x.project,x.limitations,...x.evidence.map(e=>e.excerpt)].join(' ').toLocaleLowerCase('ru').includes(q))).sort((a,b)=>a.project.localeCompare(b.project));
      $('stats').textContent=task?`Найдено ${rows.length} проектов. Порядок — по названию.`:'Выберите задачу, чтобы увидеть проекты и основания.';
      $('results').innerHTML=rows.map(x=>`<article class="card"><span class="badge">${x.status==='candidate'?'Возможный кандидат':'Описано в редакционных материалах'}</span><h2><a href="project.html?repo=${encodeURIComponent(x.project)}">${esc(x.project)}</a></h2><p><b>Почему здесь:</b> ${esc(x.evidence[0].excerpt)}</p><p><b>Ограничения:</b> ${esc(WatchUI.cardContent({limitations:x.limitations},{}).limitations.text || 'Ограничения в имеющихся материалах не описаны')}</p><p><b>Независимое испытание:</b> ${esc(x.test_status)}. Подбор сам по себе испытанием не является.</p><p><b>Для России:</b> ${esc(x.russia_applicability)} — редакционная оценка.</p><details><summary>Все основания подбора (${x.evidence.length})</summary><ul>${x.evidence.map(e=>`<li>${esc(e.excerpt)}<br><small>${esc(e.file)} → ${esc(e.key)} → ${esc(e.field)}. ${esc(e.basis)}</small></li>`).join('')}</ul></details><p><b>Перед использованием:</b> ${esc(x.next_check)}</p><a href="project.html?repo=${encodeURIComponent(x.project)}">Полное исследование и источники →</a></article>`).join('')||(task?'<p>Нет совпадений. Попробуйте другое условие; отсутствие проекта здесь не доказывает отсутствие возможности.</p>':'');
    }
    $('task').onchange=render;$('status').onchange=render;$('query').oninput=render;render();
  }catch(error){$('stats').textContent=error.message;}
})();
