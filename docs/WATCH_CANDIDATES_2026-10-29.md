# Пакет публикации: GitHub Watch, 29 октября 2026

Задача: #14. **Это проверочный пакет, не опубликованные карточки.**

| Проект | URL | Тип изменения | Применение | Ограничение |
|---|---|---|---|---|
| Gramps Web API | https://github.com/gramps-project/gramps-web-api | обновление существующего проекта | управление правами, отзыв токенов, массовые операции | проверить конкретные коммиты и лицензирование |
| Scormave gramps-web-mcp | https://github.com/Scormave/gramps-web-mcp | существенное обновление | безопасные транзакции и undo_change, MCP elicitation | AGPL-3.0-or-later; проверка только на копии дерева |
| gramps-web-mcp-rs | https://github.com/Alexey-N-Chernyshov/gramps-web-mcp-rs | обновление / новый кандидат | Rust MCP, SSO и токены | проверить дату релиза и Apache-2.0 |
| heritage-research-mcp | https://github.com/magicianmarty/heritage-research-mcp | новый кандидат | архивные адаптеры, TEI, SQLite FTS5 | проверить дату изменений и MIT; права на контент отдельно |

## Codex: довести до опубликованного сайта

Работай в ветке `watch-2026-10-29-gramps-mcp` и обновляй существующий PR, не создавай новый. Прочитай `DISCOVERY_WORKFLOW.md`, `APPLY_WORKFLOW.md`, `data/discoveries.jsonl`, `tools/watch_pipeline.py`. Проверь существующие карточки, алиасы, applied-events и ранее опубликованные события, чтобы не создать дубликаты. Сверь каждую заявленную дельту с первичными коммитами и релизами. Отдели факт от заявления автора и нашей оценки, зафиксируй evidence, license, maturity, Russia fit и компоненты.

Создай полноценные события для подтверждённых изменений и проведи через `review --report`, `apply --approved-only --edition-date 2026-10-29 --dry-run`, затем `apply --approved-only --edition-date 2026-10-29 --write --expect-plan HASH` с реальным хешем плана. Проверь `validate`, unit tests, UI smoke, синхронность `catalog.json`, `docs/catalog.json`, `docs/research.json`, `digest.json`, `docs/digest.json` и HTML seeds. Если pipeline требует отдельного review-хеша или решения человека, не подделывай их: подготовь пакет и укажи блокирующее действие.

Не запускай затратные GitHub Actions при исчерпанной квоте. Коммить только согласованные файлы. После merge проверь опубликованный GitHub Pages и зафиксируй результат в PR.

Проверенный первоисточник Scormave: https://github.com/Scormave/gramps-web-mcp/blob/main/README.md — описывает undo, подтверждения и AGPL; независимый функциональный тест не проводился.
