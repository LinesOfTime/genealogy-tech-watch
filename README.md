# Genealogy Tech Watch — Линии времени

Каталог проектов цифровой генеалогии и датированный исследовательский дайджест.

## Безопасный режим публикации

- **GitHub Actions не используются**: в репозитории отсутствует `.github/workflows/`.
- Статический GitHub Pages публикуется из `main` / `docs`.
- Никаких сборок, Docker, артефактов или Actions cache.
- `docs/index.html` — каталог; `docs/digest.html` — дайджест.
- `catalog.json`, `digest.json` — исходные экспортные снимки данных. Страницы содержат встроенные копии данных и работают офлайн.

## Первая публикация

1. Создайте **публичный** пустой репозиторий `LinesOfTime/genealogy-tech-watch` без автоматически создаваемых файлов.
2. Из распакованной папки выполните в PowerShell (требуется Git):

   ```powershell
   git init -b main
   git add .
   git commit -m "Initial static genealogy watch catalog and digest"
   git remote add origin https://github.com/LinesOfTime/genealogy-tech-watch.git
   git push -u origin main
   ```
3. В GitHub откройте **Settings → Pages → Build and deployment → Source: Deploy from a branch → Branch: main → Folder: /docs → Save**.
4. Откройте `https://linesoftime.github.io/genealogy-tech-watch/` и перейдите в дайджест.

**Примечание:** GitHub Pages может использовать внутренний механизм развёртывания GitHub. Выбор «Deploy from a branch» не создаёт нашего собственного workflow, но не гарантирует абсолютно нулевых внутренних записей о публикации. Проверяйте Billing → Actions.

## Как обновлять

1. Редактируйте `catalog.json` / `digest.json`.
2. Важно: HTML-страницы работают на **встроенных** данных. После правки JSON обновите содержимое `<script id="seed" type="application/json">` в соответствующей HTML-странице (или используйте `python tools/sync_data.py`).
3. Проверьте локально HTML, затем `git add .`, `git commit`, `git push`.
4. Изменения должны быть проверены до публикации; обнаружение нового коммита не равнозначно значимому обновлению.

## Источники и ограничения

Содержимое основано на прежних исследовательских обзорах; не является независимым повторным аудитом всех репозиториев. Лицензии и заявления о возможностях требуют проверки по первоисточникам. Локальный импорт JSON в интерфейсе сохраняет данные только в браузере и **не отправляет** их в GitHub.
