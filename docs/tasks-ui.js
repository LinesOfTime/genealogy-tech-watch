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
      $('compare-results').innerHTML = selected.size ? '<p>Сопоставление существующих редакционных сведений, без рейтинга качества. Выбор сохраняется при смене фильтра в этой вкладке.</p><div class="comparison-grid">' + [...selected.values()].map(x => '<article class="comparison-card"><h3>'+esc(x.project)+'</h3><dl>' + [['Роль',x.role?.label||'Роль требует уточнения'],['География источников',x.usage_context?.label||'Не уточнена'],['Назначение',x.purpose],['Практический приоритет',x.practical_priority?.priority||'Не оценён'],['Сценарий',x.practical_priority?.task||x.use_case],['Ограничения',x.limitations],['Лицензия',x.license],['Проверка',WatchUI.testResult(x.test_status)]].filter(([,value])=>WatchUI.meaningful(value)).map(([label,value])=>'<dt>'+esc(label)+'</dt><dd>'+esc(value||'Сведения не указаны')+'</dd>').join('')+'</dl>'+(x.status==='candidate'?'<p>Возможный кандидат: применимость требует проверки</p>':'')+'<button type="button" data-compare="'+esc(x.project)+'">Убрать из сравнения</button> <a href="project.html?repo='+encodeURIComponent(x.project)+'">Источники и история</a></article>').join('')+'</div>' : '<p>Отметьте до трёх проектов в результатах подбора.</p>';
    }
    function render(){
      const task=$('task').value,status=$('status').value,role=$('role').value,q=$('query').value.toLocaleLowerCase('ru');
      const rows=data.matches.filter(x=>x.task===task&&(!status||x.status===status)&&(!role||(x.role?.id||'unknown')===role)&&(!q||[x.project,x.limitations,x.usage_context?.label,x.usage_context?.scenario,x.practical_priority?.scope,x.practical_priority?.task,...x.evidence.map(e=>e.excerpt)].join(' ').toLocaleLowerCase('ru').includes(q))).sort((a,b)=>a.project.localeCompare(b.project));
      $('stats').textContent=task?`Найдено ${rows.length} проектов.`:'Выберите задачу, чтобы увидеть проекты и основания.';
      const cards=rows.map(x=>`<article class="card"><button type="button" data-compare="${esc(x.project)}" aria-pressed="${selected.has(x.project)}">${selected.has(x.project)?'Убрать из сравнения':'Сравнить'}</button> ${x.status==='candidate'?'<span class="badge">Возможный кандидат</span>':''}<h2><a href="project.html?repo=${encodeURIComponent(x.project)}">${esc(x.project)}</a></h2>${x.repository_reference_issue?WatchUI.priorityNote(x):''}${x.practical_priority?`<p><b>Практический приоритет:</b> ${esc(x.practical_priority.priority)} · ${esc(x.practical_priority.scope)}</p>`:''}${WatchUI.usage(x.usage_context)}${x.usage_context?`<p><b>Когда смотреть:</b> ${esc(x.usage_context.scenario)}</p><p><b>Границы применения:</b> ${esc(x.usage_context.boundary)}</p>`:''}${!x.usage_context&&WatchUI.cardContent({use_case:x.use_case},{}).practical.text?`<p><b>${x.status==='candidate'?'Возможный сценарий':'Сценарий'}:</b> ${esc(WatchUI.cardContent({use_case:x.use_case},{}).practical.text)}</p>`:''}${WatchUI.cardContent({limitations:x.limitations},{}).limitations.text?`<p><b>Ограничения:</b> ${esc(WatchUI.cardContent({limitations:x.limitations},{}).limitations.text)}</p>`:''}${WatchUI.testResult(x.test_status)?`<p><b>Испытание:</b> ${esc(WatchUI.testResult(x.test_status))}</p>`:''}${WatchUI.meaningful(x.russia_applicability)?`<p><b>Для России:</b> ${esc(x.russia_applicability)}</p>`:''}<details><summary>Роль и основания подбора (${x.evidence.length})</summary><p><b>Роль:</b> ${esc(x.role?.label||'Роль требует уточнения')}. Группировка по существующему описанию, не оценка готовности.</p>${x.role?.source?`<p>${esc(x.role.source.excerpt)}<br><small>${esc(x.role.source.file)} → ${esc(x.role.source.field)}</small></p>`:''}<ul>${x.evidence.map(e=>`<li>${esc(e.excerpt)}<br><small>${esc(e.file)} → ${esc(e.key)} → ${esc(e.field)}. ${esc(e.basis)}</small></li>`).join('')}</ul></details><p><b>Проба на своих материалах:</b> ${esc(x.practical_priority?.pilot||x.next_check)}</p><a href="project.html?repo=${encodeURIComponent(x.project)}">Полное исследование и источники →</a></article>`);
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
