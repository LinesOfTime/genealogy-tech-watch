# Расширенные исследовательские карточки — Genealogy Tech Watch

Содержимое собрано из редакционного реестра от 08.10.2026 (142 записи) и путеводителя от 10.10.2026 (140 проектов). Это **не новый независимый аудит** репозиториев. Данные из двух источников сопоставляются по `owner/repo`.

## Установка в существующий репозиторий

1. Скопировать `docs/research.json`, `docs/project.html`, `tools/enable_research_pages.py` из архива в соответствующие папки репозитория `LinesOfTime/genealogy-tech-watch`.
2. В корне репозитория выполнить `python tools/enable_research_pages.py`.
3. Проверить `docs/index.html` и `docs/project.html?repo=...` через локальный HTTP-сервер (`python -m http.server 8000`) и открыть `http://localhost:8000/docs/project.html?repo=23andme%2Fbonsaitree`.
4. Закоммитить и отправить файлы в `main`. GitHub Pages публикует `/docs` автоматически.

Скрипт сам копирует корневые `catalog.json` и `digest.json` в `docs/`, чтобы страницы были доступны через GitHub Pages. При дальнейших обновлениях данных повторяйте копирование.

Никакие GitHub Actions не создаются.
