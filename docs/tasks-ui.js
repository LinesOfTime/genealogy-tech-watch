(async()=>{
  const {esc}=WatchUI,$=id=>document.getElementById(id);
  try {
    const response=await fetch('task-matches.json',{cache:'no-store'});
    if(!response.ok)throw Error('Не удалось загрузить основания подбора');
    const data=await response.json();
    $('task').innerHTML='<option value="">Выберите задачу</option>'+data.tasks.map(t=>`<option value="${esc(t.id)}">${esc(t.title)}</option>`).join('');
    const requested=new URLSearchParams(location.search).get('task');
    if(data.tasks.some(t=>t.id===requested))$('task').value=requested;
    const selected = new Map();
    const groups = [['tool','Инструменты и библиотеки'],['data','Наборы данных и примеры'],['reference','Спецификации и методики'],['unknown','Роль требует уточнения']];
    function comparison(){
      $('compare-count').textContent = 'Выбрано для сравнения: ' + selected.size + ' из 3';
      $('compare-results').innerHTML = selected.size ? '<p>Сопоставление существующих редакционных сведений, без рейтинга качества. Выбор сохраняется при смене фильтра в этой вкладке.</p><div class="comparison-grid">' + [...selected.values()].map(x => '<article class="comparison-card"><h3>'+esc(x.project)+'</h3><dl>' + [['Роль',x.role?.label||'Роль требует уточнения'],['Назначение',x.purpose],['Сценарий',x.use_case],['Ограничения',x.limitations],['Лицензия',x.license],['Проверка',x.test_status]].map(([label,value])=>'<dt>'+esc(label)+'</dt><dd>'+esc(value||'Сведения не указаны')+'</dd>').join('')+'</dl><p>'+esc(x.status==='candidate'?'Возможный кандидат: применимость требует проверки':'Описано в редакционных материалах; не независимое испытание')+'</p><button type="button" data-compare="'+esc(x.project)+'">Убрать из сравнения</button> <a href="project.html?repo='+encodeURIComponent(x.project)+'">Источники и история</a></article>').join('')+'</div>' : '<p>Отметьте до трёх проектов в результатах подбора.</p>';
    }
    function render(){
      const task=$('task').value,status=$('status').value,role=$('role').value,q=$('query').value.toLocaleLowerCase('ru');
      const rows=data.matches.filter(x=>x.task===task&&(!status||x.status===status)&&(!role||(x.role?.id||'unknown')===role)&&(!q||[x.project,x.limitations,...x.evidence.map(e=>e.excerpt)].join(' ').toLocaleLowerCase('ru').includes(q))).sort((a,b)=>a.project.localeCompare(b.project));
      $('stats').textContent=task?`Найдено ${rows.length} проектов. Сгруппировано по роли; внутри группы — по названию.`:'Выберите задачу, чтобы увидеть проекты и основания.';
      const cards=rows.map(x=>`<article class="card"><button type="button" data-compare="${esc(x.project)}" aria-pressed="${selected.has(x.project)}">${selected.has(x.project)?'Убрать из сравнения':'Сравнить'}</button> <span class="badge">${x.status==='candidate'?'Возможный кандидат':'Описано в редакционных материалах'}</span><h2><a href="project.html?repo=${encodeURIComponent(x.project)}">${esc(x.project)}</a></h2><p><b>Почему здесь:</b> ${esc(x.evidence[0].excerpt)}</p><p><b>Ограничения:</b> ${esc(WatchUI.cardContent({limitations:x.limitations},{}).limitations.text || 'Ограничения в имеющихся материалах не описаны')}</p><p><b>Независимое испытание:</b> ${esc(x.test_status)}. Подбор сам по себе испытанием не является.</p><p><b>Для России:</b> ${esc(x.russia_applicability)} — редакционная оценка.</p><details><summary>Роль и основания подбора (${x.evidence.length})</summary><p><b>Роль:</b> ${esc(x.role?.label||'Роль требует уточнения')}. Группировка по существующему описанию, не оценка готовности.</p>${x.role?.source?`<p>${esc(x.role.source.excerpt)}<br><small>${esc(x.role.source.file)} → ${esc(x.role.source.field)}</small></p>`:''}<ul>${x.evidence.map(e=>`<li>${esc(e.excerpt)}<br><small>${esc(e.file)} → ${esc(e.key)} → ${esc(e.field)}. ${esc(e.basis)}</small></li>`).join('')}</ul></details><p><b>Перед использованием:</b> ${esc(x.next_check)}</p><a href="project.html?repo=${encodeURIComponent(x.project)}">Полное исследование и источники →</a></article>`);
      $('results').innerHTML=groups.map(([id,label])=>{const group=rows.map((x,i)=>({x,html:cards[i]})).filter(({x})=>(x.role?.id||'unknown')===id);return group.length?'<section class="task-group"><h2>'+esc(label)+' <small>('+group.length+')</small></h2><div class="grid">'+group.map(x=>x.html).join('')+'</div></section>':'';}).join('')||(task?'<p>Нет совпадений. Попробуйте другое условие; отсутствие проекта здесь не доказывает отсутствие возможности.</p>':'');
    }
    const toggle = event => {
      const button = event.target.closest?.('[data-compare]');
      if(!button)return;
      const name=button.dataset.compare;
      const container=button.closest('#compare-results')?'compare-results':'results';
      if(selected.has(name)){selected.delete(name);$('compare-message').textContent='Проект убран из сравнения';}
      else if(selected.size<3){const x=data.matches.find(x=>x.project===name&&x.task===$('task').value);if(x)selected.set(name,x);$('compare-message').textContent='Проект добавлен в сравнение';}
      else {$('compare-message').textContent='Можно сравнить не больше трёх проектов. Уберите один из выбранных.';return;}
      comparison();render();
      if(typeof document.querySelectorAll==='function'){
        const replacement=[...document.querySelectorAll('#'+container+' [data-compare]')].find(n=>n.dataset.compare===name);
        (replacement||$('compare-heading')).focus();
      }
    };
    $('results').addEventListener('click',toggle);
    $('compare-results').addEventListener('click',toggle);
    $('clear-comparison').addEventListener('click',()=>{selected.clear();comparison();render();$('compare-message').textContent='Сравнение очищено';});
    comparison();
    if(!WatchUI.bindFilterState(['task','status','query','role'],render,'reset-tasks')){$('task').onchange=render;$('status').onchange=render;$('role').onchange=render;$('query').oninput=render;render();}
  }catch(error){$('stats').textContent=error.message;}
})();
