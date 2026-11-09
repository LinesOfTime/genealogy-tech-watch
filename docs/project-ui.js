(async () => {
  const {esc, link, para, panel, rating, sources} = WatchUI;
  const content = document.getElementById('content');
  try {
    const load = async path => { const response = await fetch(path, {cache:'no-store'}); if (!response.ok) throw Error(`Не удалось загрузить ${path}`); return response.json(); };
    const [catalog, research, digest, usage] = await Promise.all(['catalog.json','research.json','digest.json','usage-context.json'].map(load));
    // Optional commentary must never make an existing project detail unavailable.
    const updates = await load('source-updates.json').catch(error => { console.warn('Source update notes unavailable', error); return {items:[]}; }) || {items:[]};
    const requested = (new URLSearchParams(location.search).get('repo') || '').toLowerCase();
    const x = catalog.find(v => v.name.toLowerCase() === requested || v.url.toLowerCase().replace(/\/$/, '').replace('https://github.com/', '') === requested);
    if (!x) throw Error('Проект не найден: ' + requested);
    const key = x.name.toLowerCase(), r = research[key] || {};
    document.title = x.name + ' — исследование';
    document.getElementById('title').textContent = x.name;
    document.getElementById('subtitle').textContent = x.section + ' · практический приоритет ' + WatchUI.priorityValue(x) + ' · редакционный приоритет ' + WatchUI.editorialPriority(x);
    const applicability = r.russia_applicability || x.russia_applicability;
    const russiaPanel = panel('Применимость для России', para(rating(r.russia_applicability ? r : x)) + para(applicability?.basis || 'Оценка не установлена') +
      (applicability?.original_line ? para('Исходная строка: ' + applicability.original_line) + '<small>Источник: путеводитель от 10 октября 2026, guide_excerpt. Редакционная оценка.</small>' : '') +
      para('Доступность сервиса из РФ: ' + (r.russia_service_availability || 'не проверена')));
    let html = '';
    const model=x.classification, currency=x.assessment_currency;
    const typePanel = panel('Тип и функциональные направления',
      para(model?.type_label || 'Не определено') + para((model?.domain_labels || []).join(' · ') || 'Направления не определены') +
      para('Происхождение записи: '+(model?.origin_label || x.origin || 'Не установлено')) +
      '<details><summary>Основание классификации и прежний раздел</summary>' +
      para(model?.reason) + para('Исторический раздел: '+x.section) +
      (model?.sources||[]).map(source=>para(source.file+' → '+source.field+' — '+JSON.stringify(source.value))).join('')+'</details>');
    const purpose = x.description_provenance ? x.description : r.editorial_summary || x.description;
    html += panel('Назначение', para(purpose));
    const p=x.practical_priority;
    const practicalDetails=p?'<p><b>'+esc(p.task)+'</b></p>'+para(p.scope)+para(p.rationale)+'<p><b>Небольшая проба:</b> '+esc(p.pilot)+'</p>':'';
    html += panel('Практическое применение', practicalDetails+ WatchUI.usage(usage?.projects?.[key],true)+WatchUI.practical(x,r));
    html += panel('Ограничения и редакционная оценка', WatchUI.limitations(x,r));
    const latest = (updates.items || []).filter(u => u.project.toLowerCase() === key);
    if (latest.length) {
      html += panel('Новая проверка первоисточников', latest.map(u =>
        '<div class="entry"><p><b>' + esc(u.checked_at) + ' · ' + esc(u.status) + '</b></p>' +
        para(u.summary) + '<p><b>Подтверждено:</b> ' + esc(u.verified) + '</p>' +
        '<p><b>Ограничения проверки:</b> ' + esc(u.limitations) + '</p>' +
        '<p><b>Следующее действие:</b> ' + esc(u.next_action) + '</p>' +
        '<p>' + (u.sources || []).map((url,i) => link(url,'Первоисточник ' + (i+1))).join(' · ') + '</p></div>'
      ).join(''));
    }

    html += typePanel + russiaPanel;
    if(x.repository_access_notes?.length)html+=panel('Доступность репозитория',
      x.repository_access_notes.map(note=>para(note.notes?.join(' '))).join(''));
    if(currency)html += panel('Актуальность практической оценки',
      para(currency.label) + para(currency.reason) +
      para('Утверждение оценки: '+(currency.assessment_approved_at || 'отсутствует')) +
      para('Содержательная проверка источника: '+(currency.last_substantive_source_check || 'не датирована')) +
      para('Сверка актуальности: '+(currency.reviewed_at || 'не проводилась')) +
      (currency.pending_proposal ? '<details><summary>Предложение, ожидающее утверждения</summary>'+
        para(currency.pending_proposal.previous_priority+' → '+currency.pending_proposal.proposed_priority)+
        para(currency.pending_proposal.reason)+para(currency.pending_proposal.pilot)+sources(currency.pending_proposal.sources)+'</details>':'')+
      '<details><summary>Источники и границы сверки</summary>'+currency.sources.map(row=>para(row.checked_at+' · '+row.kind)+sources(row.urls)).join('')+'</details>');
    html += panel('Приоритеты и доказательность', WatchUI.priorityAxes(x)+WatchUI.priorityNote(x)+para(x.practical_priority?.rationale||x.evaluation?.priority_rationale||'Обоснование оценки отсутствует.')+'<a href="priorities.html?q='+encodeURIComponent(x.name)+'">Проверить актуальность и следующий шаг →</a> · <a href="trials.html?project='+encodeURIComponent(x.name)+'">Протоколы испытаний →</a>', 'evidence');
    const report=x.practical_priority?.test_report_url || x.evaluation?.test_report_url;
    html += panel('Практическое испытание', report ? link(report,'Протокол испытания') : para('Ссылка на воспроизводимый протокол в оценке не указана.'));
    if (x.description_provenance) {
      const p = x.description_provenance;
      html += '<details class="panel"><summary>Происхождение описания назначения</summary>' + ( para('Прежнее описание: ' + p.original_description) +
        para('Источник: ' + p.source.file + ' → ' + p.source.key + ' → ' + p.source.field) +
        para('Исходный текст: ' + p.source.original_text) +
        para('Редакционный материал; тип проекта не выводился из описания.')) + '</details>';
    }
    const housekeeping=[...(x.editorial_service_notes||[]),...(r.editorial_service_notes||[])];
    if(housekeeping.length)html+='<details class="panel"><summary>Служебные редакционные пометки</summary>'+[...new Set(housekeeping.flatMap(n=>n.notes||[]))].map(para).join('')+'<small>Историческая очередь проверки полей; это не описание ограничений инструмента.</small></details>';
    if(r.editorial_corrections?.length) {
      const labels={description:'Назначение',use_case:'Практическое применение',limitations:'Ограничения',
        editorial_summary:'Редакционное описание назначения',editorial_use_case:'Редакционный сценарий',editorial_limitations:'Редакционные ограничения'};
      const previous=(values,origin)=>Object.entries(values||{}).map(([field,value])=>
        para(origin+' — '+(labels[field]||field)+': '+(value===null||value===undefined?'Значение отсутствовало':value===''?'Поле было пустым':value))).join('');
      html+=panel('Основания редакционного уточнения',r.editorial_corrections.map(c=>
        '<div class="entry">'+(c.checked_at?para('Дата уточнения: '+c.checked_at):'')+para(c.basis)+sources(c.sources)+
        (c.previous_catalog||c.previous_research?'<details><summary>Прежние значения до уточнения</summary>'+previous(c.previous_catalog,'Каталог')+previous(c.previous_research,'Исследовательская карточка')+'</details>':'')+'</div>').join(''));
    }
    if (r.guide_excerpt) html += '<details class="panel"><summary>Из путеводителя от 10 октября 2026</summary>'+para(r.guide_excerpt)+'<small>Полный исходный текст сохранён. Это редакционное описание.</small></details>';
    html += panel('Лицензия и проверка', para('Лицензия: ' + (r.license || x.license || 'Не определена')) + para('Статус лицензии: ' + (r.license_status || x.license_status || 'Не подтверждён')) +
      para('Основание: ' + (r.license_evidence || 'Не указано')) + para('Открытость: ' + (r.opensource_status || 'Не установлена')) +
      para('Аудит: ' + (r.audit_status || 'Не указан')) + para('Метод проверки: ' + (r.verification_basis || x.verification || 'Не указан')) +
      para('Дата проверки: ' + (r.verification_date || x.verified_at || 'Не указана')) +
      ((x.evaluation?.independent_test === true || x.practical_priority?.independent_test === true || x.evaluation?.test_report_url) ? para('Испытание: ' + (r.test_status || x.test_status || 'См. протокол испытания')) : '') + link(x.url, 'Репозиторий') + ' · ' + link(x.source, 'Источник каталога') + ' · ' + link(r.source_evidence, 'Источник исследования'));
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
        para(e.review_status === 'approved' ? 'Событие утверждено редактором. Проверяющий: ' + e.reviewer :
             e.review_status === 'proposed' ? 'Кандидат редакционного обзора; ожидает утверждения.' : 'Историческое событие: статус новой проверки не указан') +
        sources(e.source_urls) + ' ' + link(e.url, 'Источник изменения') + '</div>';
    }).join('') || para('Пока нет датированных обновлений'));
    html += panel('Происхождение сведений', para('Редакционный реестр от 8 октября 2026; путеводитель от 10 октября 2026; записи GitHub Watch. Источники и статусы проверки указаны отдельно.'));
    content.innerHTML = html;
  } catch (error) { content.textContent = 'Ошибка: ' + error.message; }
})();
