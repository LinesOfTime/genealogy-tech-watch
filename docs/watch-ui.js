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
