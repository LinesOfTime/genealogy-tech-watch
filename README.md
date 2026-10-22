# Genealogy Tech Watch

Публичный каталог GitHub-проектов для цифровой генеалогии и архивных исследований.

## Структура

- `docs/index.html` — каталог проектов.
- `docs/digest.html` — датированный исследовательский дайджест.
- `catalog.json` и `digest.json` — исходные данные.
- `tools/sync_data.py` — синхронизация данных с HTML.

## Безопасная публикация

1. Распаковать подготовленный архив `genealogy-tech-watch-static.zip`.
2. Загрузить содержимое папки `genealogy-tech-watch/` в корень репозитория, сохранив структуру каталогов (в том числе `docs/` и `tools/`). При загрузке заменить этот README полной версией из архива.
3. В GitHub открыть **Settings → Pages → Build and deployment**.
4. Выбрать **Deploy from a branch**, ветку **main**, папку **/docs**, нажать **Save**.
5. Проверить адрес https://linesoftime.github.io/genealogy-tech-watch/

**Ограничения:** не создавать собственных `.github/workflows`, не использовать Actions cache и artifacts. GitHub Pages при публикации из ветки может использовать служебный механизм Actions; это не то же самое, что собственный ежедневный workflow.

Исследовательские утверждения и лицензии требуют проверки по первичным источникам перед заимствованием кода.
