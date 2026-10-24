# Проверка обновления каталога — 24 октября 2026

Связано с #1. **Это рабочий список кандидатов, не опубликованный выпуск.** Публикация через `tools/watch_pipeline.py` после проверки источников, лицензий, существующих записей и approval/hash gate.

| Проект / изменение | Компоненты | Действие | Статус |
|---|---|---|---|
| [b21-agency/gramps-ui](https://github.com/b21-agency/gramps-ui) | UI, API, Research Workspace | Проверить существование, дату релиза 0.1.0, AGPL и совместимость с Gramps Web | Не подтверждено независимо |
| [dsblank/gramps-connect-stories](https://github.com/dsblank/gramps-connect-stories) | Research Workspace, экспорт историй | Проверить спецификацию, JSON Schema, лицензию и реальную переносимость | Не подтверждено независимо |
| [device25/gedview](https://github.com/device25/gedview) | GEDCOM, даты, источники | Проверить код обработки календарей, не смешивать планы README с реализацией | Не подтверждено независимо |
| [stanford-oval/sheldon](https://github.com/stanford-oval/sheldon) | Research Workspace, evidence, агенты | Проверить публикацию, лицензию, benchmark, применимость гипотез | Не подтверждено независимо |
| [AI-Riksarkivet/rask](https://github.com/AI-Riksarkivet/rask/commit/da7b293644b08e767271744be63775491cd553ba) | provenance, Indexer | Проверить дельту относительно существующей карточки, не дублировать UUID-обновление | Не подтверждено независимо |
| [gramps-project/gramps-web-api](https://github.com/gramps-project/gramps-web-api/commit/187ac6445c9d50ad296058c3552823eb886fb743) | транзакции, provenance | Проверить исправление undo-history и добавить историю к существующей записи | Не подтверждено независимо |

## Контроль перед выпуском

1. Сверить `data/discoveries.jsonl`, `docs/catalog.json`, `docs/digest.json` и текущие карточки; записи 23 октября уже встречаются в журнале.
2. Подтвердить первоисточники и лицензии по конкретным ревизиям; сохранить evidence и отделить заявления авторов от независимых испытаний.
3. Утвердить только действительно значимые изменения; заполнить review metadata.
4. Выполнить `scan --dry-run`, `review --report`, `apply --approved-only --edition-date 2026-10-24 --dry-run`, затем `--write --expect-plan HASH` с фактическим hash.
5. Выполнить `validate`, unittest, UI smoke; проверить карточки, фильтр «Для России», лицензии, офлайн-режим и дайджест.
6. Только после этого объединить изменения в `main` и проверить GitHub Pages.

**Никакие утверждения предыдущего чата не считаются сами по себе независимой проверкой.**
