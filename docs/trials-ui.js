(async () => {
  const {esc,link}=WatchUI;
  const $=id=>document.getElementById(id);
  const labels={submitted:'На рассмотрении',reviewed:'Проверено редактором',accepted:'Принято в реестр',rejected:'Отклонено'};
  try {
    const response=await fetch('trials.json',{cache:'no-store'});
    if(!response.ok)throw Error('Реестр недоступен');
    const data=await response.json();
    if(data.schema_version!=='1.0'||!Array.isArray(data.trials))throw Error('Неизвестная схема реестра');
    const params=new URLSearchParams(location.search);
    $('project').value=params.get('project')||'';
    if(Object.hasOwn(labels,params.get('status')))$('status').value=params.get('status');
    const render=()=>{
      const q=$('project').value.trim().toLocaleLowerCase('ru'),status=$('status').value;
      const rows=data.trials.filter(x=>(!q||x.project.toLocaleLowerCase('ru').includes(q))&&(!status||x.status===status));
      $('count').textContent='Опубликовано протоколов: '+data.trials.length+'. Показано: '+rows.length+'.';
      $('items').innerHTML=rows.map(x=>'<article class="panel"><h2>'+esc(x.project)+' · '+esc(x.id)+'</h2><p><b>Статус:</b> '+esc(labels[x.status]||'Не определён')+' · '+esc(x.performed_at)+'</p><p><b>Версия:</b> '+esc(x.project_version)+'</p><p><b>Корпус:</b> '+esc(x.dataset.name)+' · '+esc(x.dataset.version)+'</p><p><b>Метод:</b> '+esc(x.method)+'</p><p><b>Результат:</b> '+esc(x.outcome)+'</p><p><b>Ограничения:</b> '+esc(x.limitations)+'</p><p><b>Независимо от автора:</b> '+(x.independent_of_author?'да':'нет')+'</p><p>'+link(x.report_url,'Протокол и данные')+'</p></article>').join('')||'<p class="panel">Для выбранных условий опубликованных протоколов нет.</p>';
    };
    for(const id of ['project','status'])$(id).addEventListener(id==='project'?'input':'change',()=>{
      const url=new URL(location.href);
      for(const field of ['project','status'])$(field).value?url.searchParams.set(field,$(field).value):url.searchParams.delete(field);
      history.replaceState(null,'',url);render();
    });
    render();
  }catch(error){$('count').textContent='Ошибка: '+error.message}
})();