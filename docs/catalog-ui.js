/* Published data and explicit local previews share the same filter/render path. */
const $ = id => document.getElementById(id);
const seed = JSON.parse($('seed').textContent);
const usage = JSON.parse($('usage-seed').textContent).projects;
const esc = WatchUI.esc;
let data = structuredClone(seed);

function knownProject(card) {
  return seed.some(row => row.name.toLowerCase() === card.name.toLowerCase() && row.url.toLowerCase() === card.url.toLowerCase());
}

function fillOptions(id, values, label) {
  const field = $(id), previous = field.value;
  field.innerHTML = '<option value="">' + esc(label) + '</option>' +
    [...new Set(values.filter(Boolean))].sort((a,b) => a.localeCompare(b,'ru'))
      .map(value => '<option value="' + esc(value) + '">' + esc(value) + '</option>').join('');
  field.value = previous;
}

function options() {
  fillOptions('section', data.map(card => card.section), 'Все исторические разделы');
  fillOptions('priority', data.map(WatchUI.priorityValue), 'Все практические оценки');
  fillOptions('editorial-priority', data.map(WatchUI.editorialPriority), 'Все редакционные оценки');
  fillOptions('project-type', data.map(card => card.classification?.type_label || 'Не определено'), 'Все типы');
  fillOptions('currency', data.map(card => card.assessment_currency?.label || 'Недостаточно данных'), 'Любая актуальность');
  const field = $('domains'), selected = selectedDomains();
  const labels = new Set(data.flatMap(card => card.classification?.domain_labels || []));
  field.innerHTML = [...labels].sort((a,b) => a.localeCompare(b,'ru')).map(label =>
    '<option value="' + esc(label) + '"' + (selected.includes(label) ? ' selected' : '') + '>' + esc(label) + '</option>').join('');
}

function selectedDomains() {
  return Array.from($('domains').selectedOptions || []).map(option => option.value);
}

function render() {
  const query = $('search').value.toLocaleLowerCase('ru'), tags = selectedDomains();
  const items = data.filter(card => {
    const model = card.classification, status = card.assessment_currency;
    const search = [card.name, card.description, card.use_case, card.limitations, card.license,
      card.section, card.url, model?.type_label, ...(model?.domain_labels || []),
      usage[card.name.toLowerCase()]?.label, card.practical_priority?.scope,
      card.practical_priority?.task, card.practical_priority?.rationale].join(' ').toLocaleLowerCase('ru');
    return (!$('section').value || card.section === $('section').value) &&
      (!$('priority').value || WatchUI.priorityValue(card) === $('priority').value) &&
      (!$('editorial-priority').value || WatchUI.editorialPriority(card) === $('editorial-priority').value) &&
      (!$('project-type').value || (model?.type_label || 'Не определено') === $('project-type').value) &&
      (!$('currency').value || (status?.label || 'Недостаточно данных') === $('currency').value) &&
      tags.every(tag => (model?.domain_labels || []).includes(tag)) &&
      (!$('origin').value || card.origin === $('origin').value) &&
      (!$('russia').value || WatchUI.rating(card) === $('russia').value) &&
      (!query || search.includes(query));
  });
  $('metrics').innerHTML = [
    [data.length, 'Карточек'],
    [data.filter(card => card.practical_priority?.review_status === 'approved').length, 'Утверждённых практических оценок'],
    [data.filter(card => card.assessment_currency?.status === 'reassess').length, 'Требуют переоценки'],
    [data.filter(card => card.assessment_currency?.status === 'insufficient').length, 'Актуальность требует проверки'],
  ].map(([number,label]) => '<div class="metric"><strong>' + number + '</strong><span>' + esc(label) + '</span></div>').join('');
  $('shown').textContent = 'Показано ' + items.length + ' из ' + data.length;
  $('cards').innerHTML = items.map(card => {
    const known = knownProject(card), model = card.classification, status = card.assessment_currency;
    const projectLink = 'project.html?repo=' + encodeURIComponent(card.name);
    const priorityLink = 'priorities.html?q=' + encodeURIComponent(card.name);
    const level = card.practical_priority?.evidence_level || card.evaluation?.evidence_level || 'НД';
    const type = model?.type_label || 'Не определено';
    const assessmentStatus = {
      current:'Оценка актуальна',
      reassess:'Оценка требует пересмотра',
      insufficient:card.practical_priority?.review_status === 'approved' ?
        'Актуальность оценки требует проверки' : 'Практическая оценка не проведена',
      proposed:'Оценка ожидает утверждения'
    }[status?.status];
    const checkedAt = new Date(status?.last_substantive_source_check || NaN);
    const sourceDate = Number.isNaN(checkedAt.getTime()) ? '' : checkedAt.toLocaleDateString(
      'ru-RU', {day:'numeric', month:'long', year:'numeric', timeZone:'UTC'});

    const priority = WatchUI.priorityValue(card);
    const priorityLabel = priority === 'Проверить ссылку' ? priority : 'Практический · ' + priority;
    const priorityBadge = priority === 'Не оценён' ? '' :
      '<a class="card-priority" href="' + priorityLink + '">' + esc(priorityLabel) + '</a>';
    return '<article class="card catalog-card-v2"><div class="card-head"><div class="card-ident"><h2>' +
      (known ? '<a href="' + projectLink + '">' + esc(card.name) + '</a>' : esc(card.name)) +
      '</h2><div class="card-section">' + esc(type) + '</div></div>' +
      priorityBadge + '</div>' +
      '<p class="card-summary">' + esc(card.description || 'Назначение не описано') + '</p>' +
      (model?.domain_labels?.length ? '<div class="card-domains">' +
        model.domain_labels.map(tag => '<span class="pill">' + esc(tag) + '</span>').join('') + '</div>' : '') +
      WatchUI.usage(usage[card.name.toLowerCase()]) +
      '<details class="card-details"><summary>Сведения об оценке и лицензии</summary>' +
      '<p class="meta">Редакционный · ' + esc(WatchUI.editorialPriority(card)) +
      (card.preliminary_priority ? ' · Предварительный приоритет · ' + esc(card.preliminary_priority) : '') + '</p>' +
      (assessmentStatus ? '<p class="meta">' + esc(assessmentStatus) + '</p>' : '') +
      (WatchUI.meaningful(status?.reason) ? '<p class="meta">' + esc(status.reason) + '</p>' : '') +
      (sourceDate ? '<p class="meta">Источники проверены ' + esc(sourceDate) + '</p>' : '') +
      '<div class="card-meta"><span class="card-testing">Для России · ' + esc(WatchUI.rating(card)) + '</span>' +
      (known ? '<a class="card-testing" href="' + projectLink + '#evidence">Основания · ' + esc(level) + '</a>' :
        '<span class="card-testing">Основания · ' + esc(level) + '</span>') +
      '<span class="card-license">' + esc(card.license || 'Лицензия не установлена') + '</span></div></details>' +
      '<div class="card-links">' + (known ? '<a href="' + projectLink + '">Исследование →</a>' : '<span>Локальная запись</span>') +
      WatchUI.link(card.url, 'Репозиторий ↗') + '</div></article>';
  }).join('') || '<p class="empty">Ничего не найдено. Измените запрос или сбросьте фильтры.</p>';
}

CatalogIO.bind({getData:() => data, setData:rows => {data=rows; options(); render();}, published:seed});
options();
const filterIds = ['search','section','priority','editorial-priority','origin','russia','project-type','domains','currency'];
if (!WatchUI.bindFilterState(filterIds, render, 'reset-catalog')) {
  filterIds.forEach(id => $(id).addEventListener(id === 'search' ? 'input' : 'change', render));
  render();
}
