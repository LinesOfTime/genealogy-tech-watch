(async () => {
  const {esc, link, para, panel, rating, sources} = WatchUI;
  const content = document.getElementById('content');
  try {
    const load = async path => { const response = await fetch(path, {cache:'no-store'}); if (!response.ok) throw Error(`Не удалось загрузить ${path}`); return response.json(); };
    const [catalog, research, digest] = await Promise.all(['catalog.json','research.json','digest.json'].map(load));
    const requested = (new URLSearchParams(location.search).get('repo') || '').toLowerCase();
    const x = catalog.find(v => v.name.toLowerCase() === requested || v.url.toLowerCase().replace(/\/$/, '').replace('https://github.com/', '') === requested);
    if (!x) throw Error('Проект не найден: ' + requested);
    const key = x.name.toLowerCase(), r = research[key] || {};
    document.title = x.name + ' — исследование';
    document.getElementById('title').textContent = x.name;
    document.getElementById('subtitle').textContent = x.section + ' · редакционный приоритет ' + x.priority;
    const applicability = r.russia_applicability || x.russia_applicability;
    let html = panel('Применимость для России', para(rating(r.russia_applicability ? r : x)) + para(applicability?.basis || 'Оценка не установлена') +
      (applicability?.original_line ? para('Исходная строка: ' + applicability.original_line) + '<small>Источник: путеводитель от 10 октября 2026, guide_excerpt. Редакционная оценка.</small>' : '') +
      para('Доступность сервиса из РФ: ' + (r.russia_service_availability || 'не проверена')));
    html += panel('Тип проекта', para(r.project_type || 'Тип проекта не установлен'));
    const purpose = x.description_provenance ? x.description : r.editorial_summary || x.description;
    html += panel('Назначение', para(purpose));
    if (x.description_provenance) {
      const p = x.description_provenance;
      html += panel('Происхождение описания назначения', para('Прежнее описание: ' + p.original_description) +
        para('Источник: ' + p.source.file + ' → ' + p.source.key + ' → ' + p.source.field) +
        para('Исходный текст: ' + p.source.original_text) +
        para('Редакционный материал; назначение и функции независимо не подтверждены. Тип проекта не выводился из описания.'));
    }
    html += panel('Практическое применение', WatchUI.practical(x,r));
    html += panel('Ограничения и редакционная оценка', WatchUI.limitations(x,r));
    if(r.editorial_corrections?.length) {
      const labels={description:'Назначение',use_case:'Практическое применение',limitations:'Ограничения',
        editorial_summary:'Редакционное описание назначения',editorial_use_case:'Редакционный сценарий',editorial_limitations:'Редакционные ограничения'};
      const previous=(values,origin)=>Object.entries(values||{}).map(([field,value])=>
        para(origin+' — '+(labels[field]||field)+': '+(value===null||value===undefined?'Значение отсутствовало':value===''?'Поле было пустым':value))).join('');
      html+=panel('Основания редакционного уточнения',r.editorial_corrections.map(c=>
        '<div class="entry">'+(c.checked_at?para('Дата уточнения: '+c.checked_at):'')+para(c.basis)+sources(c.sources)+
        (c.previous_catalog||c.previous_research?'<details><summary>Прежние значения до уточнения</summary>'+previous(c.previous_catalog,'Каталог')+previous(c.previous_research,'Исследовательская карточка')+'</details>':'')+'</div>').join(''));
    }
    if (r.guide_excerpt) html += panel('Из путеводителя от 10 октября 2026', para(r.guide_excerpt) + '<small>Полный исходный текст сохранён. Это редакционное описание, не независимое испытание.</small>');
    html += panel('Лицензия и проверка', para('Лицензия: ' + (r.license || x.license || 'Не определена')) + para('Статус лицензии: ' + (r.license_status || x.license_status || 'Не подтверждён')) +
      para('Основание: ' + (r.license_evidence || 'Не указано')) + para('Открытость: ' + (r.opensource_status || 'Не установлена')) +
      para('Аудит: ' + (r.audit_status || 'Не указан')) + para('Метод проверки: ' + (r.verification_basis || x.verification || 'Не указан')) +
      para('Дата проверки: ' + (r.verification_date || x.verified_at || 'Не указана')) +
      para('Независимое тестирование: ' + (r.test_status || x.test_status || 'Не подтверждено')) + link(x.url, 'Репозиторий') + ' · ' + link(x.source, 'Источник каталога') + ' · ' + link(r.source_evidence, 'Источник исследования'));
    const events = [...(r.watch_events || []), ...(x.history || [])];
    const repository = x.url.toLowerCase().replace(/\/$/, '').replace('https://github.com/', '');
    for (const day of digest) for (const item of day.items || []) if ([key,repository].includes(item.repo.toLowerCase())) events.push({...item, date:item.event_date || day.date, url:item.link});
    events.sort((a,b) => String(b.date).localeCompare(String(a.date)));
    const seen = new Set();
    html += panel('Хронология исследований', events.map(e => {
      const id = e.discovery_id || e.date + '|' + e.change;
      if (seen.has(id)) return ''; seen.add(id);
      return `<div class="entry"><small>${esc(e.date)}</small>` + para(e.change) +
        (e.previous_state ? para('До: ' + e.previous_state) + para('После: ' + e.new_state) : '') +
        (e.significance_reason ? para('Значимость: ' + e.significance_reason) : '') +
        (e.claims_vs_verified ? '<p><b>Заявления и проверка</b></p>' + WatchUI.claims(e.claims_vs_verified) : '') +
        (e.risks ? '<p><b>Риски</b></p>' + WatchUI.risks(e.risks) : '') +
        (e.license ? para('Лицензия по событию: ' + e.license) + sources(e.license_evidence) : '') +
        (e.action ? para('Редакционная рекомендация: ' + e.action) : '') +
        para(e.review_status === 'approved' ? 'Событие утверждено редактором; это не подтверждение независимого испытания. Проверяющий: ' + e.reviewer : 'Историческое событие: статус новой проверки не указан') +
        sources(e.source_urls) + ' ' + link(e.url, 'Источник изменения') + '</div>';
    }).join('') || para('Пока нет датированных обновлений'));
    html += panel('Происхождение сведений', para('Редакционный реестр от 8 октября 2026; путеводитель от 10 октября 2026; записи GitHub Watch. Источники и статусы проверки указаны отдельно.'));
    content.innerHTML = html;
  } catch (error) { content.textContent = 'Ошибка: ' + error.message; }
})();
