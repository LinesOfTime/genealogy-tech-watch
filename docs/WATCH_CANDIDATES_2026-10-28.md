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
