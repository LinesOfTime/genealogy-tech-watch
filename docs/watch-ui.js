/* Shared presentation helpers; no persistence or inferred research claims. */
globalThis.WatchUI = (() => {
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const url = value => { try { const u = new URL(value); return u.protocol === 'https:' && !u.username && !u.password ? u.href : ''; } catch { return ''; } };
  const link = (href, label) => url(href) ? `<a href="${esc(url(href))}" target="_blank" rel="noopener noreferrer">${esc(label)} ↗</a>` : '';
  const rating = card => card.russia_applicability?.rating || 'Не оценено';
  const text = value => typeof value === 'string' ? value : JSON.stringify(value ?? 'Не указано', null, 2);
  const para = value => `<p>${esc(text(value || 'Сведения не установлены'))}</p>`;
  const panel = (title, body) => `<section class="panel"><h2>${esc(title)}</h2>${body}</section>`;
  const sourceLabel = source => {
    const href = typeof source === 'string' ? source : source.url;
    try {
      const path = decodeURIComponent(new URL(href).pathname);
      const file = path.split('/').pop();
      if (/^(license|copying)([.a-z0-9_-]*)?$/i.test(file)) return 'Лицензия';
      if (/\/releases\//i.test(path)) return 'Релиз ' + file;
      if (/\/commit\//i.test(path)) return 'Коммит ' + file.slice(0,8);
      if (/schema/i.test(file)) return 'Схема: ' + file;
      if (/test/i.test(path)) return 'Тест: ' + file;
      if (/\/blob\//i.test(path)) return (/spec|specification/i.test(path) ? 'Спецификация: ' : '') + file;
    } catch {}
    return typeof source === 'string' ? 'Источник' : ({release:'Релиз',commit:'Коммит',README:'Документация',ADR:'Архитектурное решение',paper:'Публикация',benchmark:'Оценочные материалы',PR:'Обсуждение изменения'}[source.type] || source.type || 'Источник');
  };
  const sources = items => (Array.isArray(items) ? items : []).map(s => link(typeof s === 'string' ? s : s.url, sourceLabel(s))).filter(Boolean).join(' · ');
  const claims = value => {
    if (!value || typeof value !== 'object' || Array.isArray(value)) return para(value);
    const labels = {verified:'Проверено по источнику', author_claims:'Заявления авторов', independent_testing:'Независимое тестирование'};
    return Object.entries(value).map(([key, entry]) => `<p><b>${esc(labels[key] || key)}:</b> ${esc(text(entry))}</p>`).join('');
  };
  const risks = value => Array.isArray(value) ? '<ul>' + value.map(entry => `<li>${esc(text(entry))}</li>`).join('') + '</ul>' : para(value);
  const meaningful = value => typeof value === 'string' && value.trim() && !/^(не установлен[аоы]?|сведения (пока )?не установлены|не указано|не оценено)[.!]?$/i.test(value.trim());
  const guideField = (r, label) => {
    const lines=(r.guide_excerpt || '').split(/\r?\n/).filter(line=>line.startsWith(label+':'));
    return lines.length===1 ? lines[0].slice(label.length+1).trim() : '';
  };
  const cleanNote = value => String(value || '').split(/\s*\|\s*/)
    .filter(part=>!/^\s*(Часть\s*\d+|Ч\d+)\s*:\s*незакрытые поля/i.test(part))
    .map(part=>part.replace(/^\s*(Часть\s*\d+|Ч\d+)\s*:\s*/i,'')).join(' | ').trim();
  const normalize = value => String(value || '').replace(/\s+/g,' ').trim().toLocaleLowerCase('ru');
  const cardContent = (x,r) => {
    const choose = options => options.map(([text,source])=>({text:cleanNote(text),source})).find(item=>meaningful(item.text)) || {text:'',source:null};
    const practical=choose([[r.editorial_use_case,'editorial_use_case'],[x.use_case,'use_case'],[guideField(r,'Возможности / сценарий'),'guide_excerpt:Возможности / сценарий']]);
    const limitations=choose([[r.editorial_limitations,'editorial_limitations'],[guideField(r,'Ограничения'),'guide_excerpt:Ограничения'],[x.limitations,'limitations']]);
    const note=cleanNote(r.audit_notes);
    limitations.note=meaningful(note)&&normalize(note)!==normalize(limitations.text)?note:'';
    limitations.originals=[...new Set([x.limitations,r.editorial_limitations,r.audit_notes].filter(value=>typeof value==='string'&&value.trim()))];
    return {practical,limitations};
  };
  const practical = (x,r) => {
    const chosen=cardContent(x,r).practical;
    const labels={editorial_use_case:'Редакционное исследование',use_case:'Каталог','guide_excerpt:Возможности / сценарий':'Путеводитель от 10 октября 2026'};
    if(chosen.text)return para(chosen.text)+`<small>${esc(labels[chosen.source])}. Редакционный сценарий; независимое испытание не заявлено.</small>`;
    return '<p>Конкретный сценарий в имеющихся материалах не описан.</p>';
  };
  const limitations = (x,r) => {
    const chosen=cardContent(x,r).limitations;
    let body=chosen.text?para(chosen.text):'<p>Ограничения в имеющихся материалах не описаны.</p>';
    if(chosen.note)body+='<p><b>Редакционная заметка:</b> '+esc(chosen.note)+'</p>';
    const originals=chosen.originals;
    if(originals.some(value=>/Часть\s*\d+|Ч\d+\s*:/i.test(value))) body+='<details><summary>Исходные редакционные заметки</summary>'+originals.map(para).join('')+'</details>';
    return body;
  };
  return {esc, url, link, rating, text, para, panel, sources, claims, risks, practical, limitations, cardContent};
})();

// Persist filter values, never catalogue data, in the current URL.
WatchUI.bindFilterState = (ids, render, resetId) => {
  if (typeof history === 'undefined' || !globalThis.addEventListener) return false;
  const fields = ids.map(id => document.getElementById(id));
  const restore = () => {
    const params = new URLSearchParams(location.search);
    fields.forEach(field => {
      const value = params.get(field.id) || '';
      field.value = field.tagName === 'SELECT' && ![...field.options].some(o => o.value === value) ? '' : value;
    });
    render();
  };
  const update = () => {
    const next = new URL(location.href);
    fields.forEach(field => field.value ? next.searchParams.set(field.id, field.value) : next.searchParams.delete(field.id));
    history.replaceState(null, '', next);
    render();
  };
  fields.forEach(field => field.addEventListener(field.tagName === 'SELECT' ? 'change' : 'input', update));
  document.getElementById(resetId)?.addEventListener('click', () => {
    fields.forEach(field => field.value = '');
    update();
    fields[0]?.focus();
  });
  globalThis.addEventListener('pageshow', restore);
  globalThis.addEventListener('popstate', restore);
  restore();
  return true;
};
