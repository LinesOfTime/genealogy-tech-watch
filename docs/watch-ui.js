/* Shared presentation helpers; no persistence or inferred research claims. */
globalThis.WatchUI = (() => {
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const url = value => { try { const u = new URL(value); return u.protocol === 'https:' && !u.username && !u.password ? u.href : ''; } catch { return ''; } };
  const link = (href, label) => url(href) ? `<a href="${esc(url(href))}" target="_blank" rel="noopener noreferrer">${esc(label)} ↗</a>` : '';
  const rating = card => card.russia_applicability?.rating || 'Не оценено';
  const text = value => typeof value === 'string' ? value : JSON.stringify(value ?? 'Не указано', null, 2);
  const para = value => `<p>${esc(text(value || 'Сведения не установлены'))}</p>`;
  const panel = (title, body) => `<section class="panel"><h2>${esc(title)}</h2>${body}</section>`;
  const sources = items => (Array.isArray(items) ? items : []).map(s => link(typeof s === 'string' ? s : s.url, typeof s === 'string' ? 'Источник' : s.type || 'Источник')).filter(Boolean).join(' · ');
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
  const cleanNote = value => String(value || '').split(/\s*\|\s*/).filter(part=>!/^\s*(Часть\s*\d+|Ч\d+)\s*:/i.test(part)).join(' | ').trim();
  const practical = (x,r) => {
    for (const [value,source] of [[r.editorial_use_case,'Редакционное исследование'],[x.use_case,'Каталог'],[guideField(r,'Возможности / сценарий'),'Путеводитель от 10 октября 2026']]) {
      if (meaningful(value)) return para(value)+`<small>${esc(source)}. Редакционный сценарий; независимое испытание не заявлено.</small>`;
    }
    return '<p>Конкретный сценарий в имеющихся материалах не описан.</p>';
  };
  const limitations = (x,r) => {
    const primary=[r.editorial_limitations,guideField(r,'Ограничения'),x.limitations].find(meaningful);
    const main=cleanNote(primary), note=cleanNote(r.audit_notes);
    let body=main?para(main):'<p>Ограничения в имеющихся материалах не описаны.</p>';
    if(note && note!==main)body+='<p><b>Редакционная заметка:</b> '+esc(note)+'</p>';
    const originals=[...new Set([x.limitations,r.editorial_limitations,r.audit_notes].filter(meaningful))];
    if(originals.some(value=>/Часть\s*\d+|Ч\d+\s*:/i.test(value))) body+='<details><summary>Исходные редакционные заметки</summary>'+originals.map(para).join('')+'</details>';
    return body;
  };
  return {esc, url, link, rating, text, para, panel, sources, claims, risks, practical, limitations};
})();
