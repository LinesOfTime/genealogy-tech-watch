# Пакет находок 28 октября 2026

Статус: кандидаты для проверки и применения через штатный pipeline. **Этот файл сам по себе не публикует карточки на сайте.** Связанная задача: #12.

| Проект | Компоненты | Решение | Ограничения |
|---|---|---|---|
| [AI-Riksarkivet/ra-mcp](https://github.com/AI-Riksarkivet/ra-mcp) | Archive Adapter, OCR/HTR, API/MCP/agent layer | P1: изучить модульную архитектуру, прототип архивного адаптера | Apache-2.0; не все материалы архива транскрибированы; независимых тестов нет |
| [borisovodov/doru](https://github.com/borisovodov/doru) | GEDCOM/data model, provenance/evidence, API/MCP/agent layer | P2: изучить журнал и отмену действий агента | Ранняя стадия; подтвердить лицензию и работоспособность перед публикацией |
| [stanford-oval/CREDIT](https://github.com/stanford-oval/CREDIT) | provenance/evidence, Research Workspace | P2: исследовать проверку зависимости вывода от источников | Benchmark — утверждение авторов, не независимый тест; проверить лицензию кода и данных |
| [fmadore/iwac-mcp-server](https://github.com/fmadore/iwac-mcp-server) | Research Workspace, Archive Adapter, API/MCP/agent layer | P2: изучить инструменты корпуса и MCP skills | Проверить версии, даты, лицензию и практическую зрелость |

## Проверки перед публикацией

1. Подтвердить точную дельту каждого проекта по коммитам, тегам или релизам; не называть обновлением только по README.
2. Проверить наличие в текущем каталоге, исследованиях, дайджесте и журнале находок, включая алиасы.
3. Для каждого проекта записать evidence, author claims, independently tested, maturity, license и применимость для России. Для ra-mcp учитывать различия между каталогом метаданных, оцифрованными изображениями и HTR-корпусом.
4. Создать записи в data/discoveries.jsonl; запустить review и применить утверждённый пакет штатной командой apply с plan_hash.
5. Проверить JSON/HTML синхронизацию, поиск/фильтры, тесты и UI smoke. Не запускать затратные GitHub Actions при исчерпанной квоте.

Источники для ra-mcp: https://ai-riksarkivet.github.io/ra-mcp/ и https://ai-riksarkivet.github.io/ra-mcp/how-it-works/data-sources/.

## Инструкция для Codex: завершить PR #13

Работай в ветке `watch-2026-10-28-four-projects` репозитория `LinesOfTime/genealogy-tech-watch`. Цель — **не просто дополнить документацию**, а опубликовать четыре проекта в каталоге и дайджесте через штатный pipeline. Не создавай вторую ветку или дублирующий PR.

1. Прочитай `DISCOVERY_WORKFLOW.md`, `APPLY_WORKFLOW.md`, `tools/watch_pipeline.py`, существующие события в `data/discoveries.jsonl` и записи каталога. Проверь все четыре первоисточника, историю релизов и лицензии; не переносить недоказанные цифры как факты.
2. Добавь четыре полноценные записи с `decision=publish`, source URLs, previous/new state, claims_vs_verified, рисками и evidence. Пользователь поручил публикацию конкретно этих четырёх проектов, однако хеш утверждения должен быть рассчитан после финализации записей и проверки источников, а не выдуман.
3. Выполни `python tools/watch_pipeline.py review --report`, исправь ошибки, получи `plan_hash` из `python tools/watch_pipeline.py apply --approved-only --edition-date 2026-10-28 --dry-run`, затем `apply --approved-only --edition-date 2026-10-28 --write --expect-plan HASH`.
4. Запусти `python tools/watch_pipeline.py validate`, `python -m unittest discover -s tests -v`, `node tests/ui_smoke.cjs`, `git diff --check`. Убедись, что все четыре проекта появились в `catalog.json`, `docs/catalog.json`, `docs/research.json`, `digest.json`, `docs/digest.json` и HTML seeds. Сверь количество и URL без дублей.
5. Коммить только согласованные файлы в существующую ветку PR #13. Не включай тяжёлые GitHub Actions при исчерпанном лимите. В комментарии к PR укажи фактические тесты и ограничения; не заявляй о публикации до merge и проверки GitHub Pages.
