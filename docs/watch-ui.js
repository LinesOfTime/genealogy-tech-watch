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
  return {esc, url, link, rating, text, para, panel, sources, claims, risks};
})();
