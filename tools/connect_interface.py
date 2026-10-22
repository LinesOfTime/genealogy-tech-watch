"""One-time, guarded connection of the stage E static interface."""
from pathlib import Path
import re


def main():
    root = Path(__file__).resolve().parents[1]
    index = root / 'docs/index.html'
    html = index.read_text(encoding='utf-8')
    if 'id="russia"' not in html:
        anchor = '<select id="origin">'
        if html.count(anchor) != 1:
            raise ValueError('Unknown catalogue controls')
        html = html.replace(anchor, '<select id="russia" aria-label="Применимость для России"><option value="">Применимость для России: все</option><option>Высокий</option><option>Специализированный / зависит от задачи</option><option>Не оценено</option></select>' + anchor)
        html = html.replace("o=$('origin').value;", "o=$('origin').value,russia=$('russia').value;")
        html = html.replace("(!o||x.origin===o)&&", "(!o||x.origin===o)&&(!russia||WatchUI.rating(x)===russia)&&")
        html = html.replace("['search','section','priority','origin']", "['search','section','priority','origin','russia']")
        html = html.replace('<div class="card-meta">', '<div class="card-meta"><span class="card-testing" title="${esc(x.russia_applicability?.basis||\'Редакционная оценка не установлена\')}">Для России: ${esc(WatchUI.rating(x))}</span>')
        html = html.replace('<script id="seed"', '<script src="watch-ui.js"></script><script id="seed"', 1)
        html = html.replace('<p id="shown">', '<p id="shown" role="status" aria-live="polite">')
        html = html.replace('<input id="search"', '<input aria-label="Поиск проектов" id="search"')
        html = html.replace('<select id="section"', '<select aria-label="Направление" id="section"')
        html = html.replace('<select id="priority"', '<select aria-label="Редакционный приоритет" id="priority"')
        html = html.replace('<select id="origin"', '<select aria-label="Источник каталога" id="origin"')
        html = html.replace('</footer>', '<p>«Для России» — оценка из путеводителя, а не результат независимого тестирования. Доступность сервисов из РФ отдельно не проверена.</p></footer>', 1)
    project = root / 'docs/project.html'
    project_html = project.read_text(encoding='utf-8')
    if 'project-ui.js' not in project_html:
        project_html, count = re.subn(r'<script>.*?</script>', '<script src="watch-ui.js"></script><script src="project-ui.js"></script>', project_html, flags=re.S)
        if count != 1:
            raise ValueError('Unknown project scripts')
        project_html = project_html.replace('nav{display:flex;gap:20px}', 'nav{display:flex;gap:20px;flex-wrap:wrap}p,a{overflow-wrap:anywhere}')
    digest = root / 'docs/digest.html'
    digest_html = digest.read_text(encoding='utf-8')
    if 'digest-ui.js' not in digest_html:
        digest_html, count = re.subn(r'<script>.*?</script>', '<script src="watch-ui.js"></script><script src="digest-ui.js"></script>', digest_html, flags=re.S)
        if count != 1:
            raise ValueError('Unknown digest scripts')
        digest_html = re.sub(r'<button id="import">.*?<input id="upload"[^>]*>', '', digest_html)
        digest_html = re.sub(r'<footer>.*?</footer>', '<footer>Опубликованный дайджест. Экспорт сохраняет копию на вашем устройстве. Обновления проходят редакционную проверку.</footer>', digest_html, flags=re.S)
        digest_html = digest_html.replace('<input id="q"', '<input aria-label="Поиск событий" id="q"')
        digest_html = digest_html.replace('<select id="prio">', '<select aria-label="Редакционный приоритет" id="prio">')
        digest_html = digest_html.replace('<option>P2</option>', '<option>P2</option><option>P3</option><option>Не оценён</option>')
        digest_html = digest_html.replace('<div id="stats"', '<div role="status" aria-live="polite" id="stats"')
    for path, value in [(index, html), (project, project_html), (digest, digest_html)]:
        if path.read_text(encoding='utf-8') != value:
            path.write_text(value, encoding='utf-8')


if __name__ == '__main__':
    main()
