(() => {
  const {esc, link} = WatchUI, $ = id => document.getElementById(id);
  const data = JSON.parse($('seed').textContent);
  function render() {
    const q = $('q').value.toLowerCase(), priority = $('prio').value;
    let visible = 0;
    $('content').innerHTML = data.map(day => {
      const items = day.items.filter(x => (!priority || x.priority === priority) && (!q || [x.repo,x.change,x.components,x.action,day.title].join(' ').toLowerCase().includes(q)));
      visible += items.length;
      if (!items.length) return '';
      return `<section class="day"><div class="date">${esc(day.date)}</div><h2>${esc(day.title)}</h2><p>${esc(day.summary)}</p><div class="items">` + items.map(x =>
        `<article class="item"><span class="badge">${esc(x.priority)}</span><h3>${esc(x.repo)}</h3><p>${esc(x.change)}</p>` +
        (x.previous_state ? `<p class="small">До: ${esc(x.previous_state)}<br>После: ${esc(x.new_state)}</p>` : '') +
        `<p class="small">Компоненты: ${esc(x.components)}</p><p class="small">Действие: ${esc(x.action)}</p>` +
        `<p class="small">${x.review_status === 'approved' ? 'Событие утверждено редактором' : 'Исторический обзор; новая проверка не указана'}</p>` +
        link(x.link, 'Первоисточник / основание') + ' · ' + `<a href="project.html?repo=${encodeURIComponent(x.repo)}">Исследование →</a>` +
        (x.source_urls ? '<p class="small">' + WatchUI.sources(x.source_urls) + '</p>' : '') + '</article>').join('') + '</div></section>';
    }).join('') || '<div class="empty">Нет совпадений.</div>';
    $('stats').textContent = `Показано ${visible} событий; выпусков: ${data.length}. Повторные проекты отражают отдельные изменения.`;
  }
  $('q').oninput = render; $('prio').onchange = render;
  $('export').onclick = () => { const href = URL.createObjectURL(new Blob([JSON.stringify(data,null,2)], {type:'application/json'})); const a = document.createElement('a'); a.href=href; a.download='genealogy-digest.json'; a.click(); setTimeout(() => URL.revokeObjectURL(href), 1000); };
  render();
})();
