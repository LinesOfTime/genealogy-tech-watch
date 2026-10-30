# GitHub Watch: существенные обновления 30.10.2026

Проверить и опубликовать **изменения существующих карточек**, не дублировать проекты.

## Scormave/gramps-web-mcp
- URL: https://github.com/Scormave/gramps-web-mcp
- Источник заявленной дельты: https://github.com/Scormave/gramps-web-mcp/commit/864d4e593e1d301df5a4ac0d7d7a1c90f0476a67
- Новое: `create_records`, пакетная транзакционная запись связанных генеалогических объектов (по описанию автора, до 50 за вызов), откат группы.
- Компоненты: Indexer, GEDCOM/data model, provenance/evidence, API/MCP/agent layer.
- Решение: P1, экспериментировать **только на копии дерева**. Проверить наличие в unreleased, лимиты, ограничения и лицензию AGPL-3.0; не представлять тесты автора как независимые.

## fmadore/iwac-mcp-server
- URL: https://github.com/fmadore/iwac-mcp-server
- Источник заявленной дельты: https://github.com/fmadore/iwac-mcp-server/blob/main/docs/releases/v5.0.0.md
- Новое: релиз 5.0.0, поисковые контракты, строгая проверка параметров, экспорт, компактный provenance и профили инструментов — **сверить с release notes**.
- Компоненты: Research Workspace, Archive Adapter, provenance/evidence, API/MCP/agent layer.
- Решение: P1/P2 после оценки, изучить архитектуру; проверить MIT и права на данные отдельно.

## Задание Codex — фактическое обновление сайта

Работай в текущей ветке `watch-2026-10-30-batch-and-iwac5` и существующем PR. Прочитай `DISCOVERY_WORKFLOW.md`, `APPLY_WORKFLOW.md` и журнал `data/discoveries.jsonl`. Сверь исходные коммиты, релизы, LICENSE и наличие проектов/событий в каталоге. Подготовь **две записи существенных обновлений**, а не две новые карточки. Явно отдели проверенные факты, заявления авторов и выводы для генеалогического кабинета. Проведи события через штатный review/apply с реальным `plan_hash`; не подделывай `reviewer`, `reviewed_content_hash` или утверждение. Если нужно отдельное подтверждение, остановись и покажи готовый пакет. Синхронизируй catalog, research, digest, docs JSON и HTML seeds, затем `validate`, unit tests, UI smoke, `git diff --check`. Зафиксируй фактические результаты и обнови этот PR. Не запускай затратные GitHub Actions при исчерпанной квоте. Только после проверенного merge и GitHub Pages можно утверждать, что сайт обновлён.
