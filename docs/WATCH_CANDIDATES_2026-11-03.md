# GitHub Watch 2026-11-03 — пакет для публикации

**Статус:** первичная проверка. Этот файл не заменяет штатную публикацию через pipeline.

## Обновления существующих карточек

- https://github.com/GeiserX/gramps-web-toolkit — проверить тег v1.0.0 и CHANGELOG; `gwt-run`, backup/preflight/apply/verify, GEDCOM import, IIIF, геокодирование и архивные маршруты. Сравнить именно с уже учтённой версией. Компоненты: Research Workspace, Archive Adapter, Indexer, Place Resolver/АТД, provenance/evidence. Проверить GPL-3.0-or-later.
- https://github.com/Scormave/gramps-web-mcp — проверить коммит https://github.com/Scormave/gramps-web-mcp/commit/0d5823465d5ce9add526b227e2f98eb8d70dc17c и новые `find_duplicates`/pre-create duplicate check, отличать от ранее учтённого `merge_objects`. Person Resolver, API/MCP/agent layer. AGPL-3.0-or-later; независимых precision/recall нет. Тестировать только на копии дерева.
- https://github.com/gramps-project/gramps-web-api — проверить коммит https://github.com/gramps-project/gramps-web-api/commit/4b3a266255fffc0b656e754a47359a6f9a8c3a48 и точную дельту защиты логирования. Research Workspace, API/MCP/agent layer; проверить AGPL-3.0-or-later. Не заявлять о полном устранении утечек.

## Новый кандидат

- https://github.com/Genealogy-MCP/gramps-mcp — проверить существование, источник GitLab, историю 3.13–3.15, количество операций, архитектуру `search`/`execute`, бэкапы и лицензию AGPL-3.0. В `catalog.json` на 2026-11-03 карточка не обнаружена. API/MCP/agent layer, GEDCOM/data model. Сокращение токенов — заявление автора, не независимый benchmark.

## Codex: завершить публикацию

Работай в ветке `watch-2026-11-03-release-and-resolver` и **существующем PR**, без новых веток/PR. Прочитай `DISCOVERY_WORKFLOW.md`, `APPLY_WORKFLOW.md`, `data/discoveries.jsonl` и applied-events. Проверь дубли и изменения, уже включённые в каталог, включая прежние PR #13, #15, #16, #17. Сверь коммиты, release notes, LICENSE, даты и конкретную дельту. Создай записи событий с evidence, previous/new state, claims_vs_verified, maturity и review metadata; не выдумывай утверждение и hash. Проведи review и apply с фактическим plan_hash. Синхронизируй catalog.json, docs/catalog.json, docs/research.json, digest.json, docs/digest.json и HTML seeds. Выполни validate, unit tests, UI smoke, diff check, проверь отсутствие дублей и сохранение старых данных. Не запускай затратные GitHub Actions при исчерпанной квоте. Обнови PR реальными файлами данных и результатами проверок. Только после merge и проверки GitHub Pages заявляй о публикации.
