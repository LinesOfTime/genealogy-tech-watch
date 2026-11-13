# Кандидаты обновления — 13 ноября 2026

Статус: первичная проверка существования репозиториев через GitHub API; **не утверждено для публикации**. Не является доказательством конкретных релизов, дат, лицензий или benchmark.

| Репозиторий | Компонент | Что проверить перед публикацией |
|---|---|---|
| [igorkauf/raisa-mcp](https://github.com/igorkauf/raisa-mcp) | Archive Adapter, API/MCP | реальные адаптеры, хранение данных, лицензия, дата изменения |
| [semanticmeaning/kinship-kit](https://github.com/semanticmeaning/kinship-kit) | Research Workspace, provenance | отличие от ex-ussr-kinship, 0.8.0, лицензия |
| [paulfilkin/mycelia](https://github.com/paulfilkin/mycelia) | GEDCOM, Workspace | релиз 0.3.0, откат правок, лицензия |
| [cacack/gedcom-go](https://github.com/cacack/gedcom-go) | GEDCOM/data model | версия 3.6.0 и новые коммиты, тесты round-trip |
| [Kinprove/genealogy-research-recipes](https://github.com/Kinprove/genealogy-research-recipes) | Person Resolver, evidence | дата появления village-family-reconstitution, лицензия |
| [AI-Riksarkivet/htrflow](https://github.com/AI-Riksarkivet/htrflow) | OCR/HTR | коммит Kraken, реальный scope и лицензии моделей |
| [gramps-project/gramps-web-api](https://github.com/gramps-project/gramps-web-api) | API/MCP, GEDCOM | GQL→GOQL, релизная ветка и breaking changes |

Перед отправкой в `watch-inbox/*`: проверить дубли с каталогом и дайджестом, собрать точные снимки первоисточников и SHA-256, разделить пакеты по максимум 5 событий, проверить priority_review существующих карточек, пройти preview и убедиться в публикации main/docs.

## Проверка первоисточников — 13 ноября

Проверены непосредственно через GitHub connector файлы README и LICENSE, а также CHANGELOG, где он есть. Это **проверка содержимого файлов в текущей ветке**, не закреплённый исторический снимок по коммиту и не независимый запуск ПО. До включения в Watch Updater нужны снимки и хеши.

### Raisa MCP
- README (blob `775349183d74294c6abbebb4d7ac6eea2169749c`): MCP для генеалогии бывшего СССР и Российской империи, архивные запросы и сохранение древа; доступны размещённый и локальный режимы. В размещённом режиме семейные данные хранятся на сервере автора, локально — в `~/.raisa`.
- LICENSE (blob `721eae7c53d146eaba297a1f120722821167389a`): MIT.
- Статус: подтверждена документация; работоспособность адаптеров и дата появления функций не испытаны.

### kinship-kit
- README (blob `84c72bbaa59ffb87e5a5866a1ea8945547286db5`): CLI `kin`, навык и сайт-схема, приватная папка исследования, журнал гипотез и отрицательных поисков.
- CHANGELOG (blob `af4eb46d5126b14c77c776d5e28191f1ccd8a20d`): версия 0.8.0 датирована 10 ноября; изменения сайта-схемы, публичности рассказов и портретов; схема данных v2 без изменений.
- LICENSE (blob `6218e0e984a7bd0446617a99d4c1dd92fada1142`): MIT; упомянуто происхождение от ex-ussr-kinship-research.
- Статус: подтверждены сведения из документации; тесты не запускались.

### Mycelia
- README (blob `44e411a6d8861b921aaa27aa90e14a2ae8ede445`): Windows-приложение с GEDCOM 5.5.1 и агентом, работающим через MCP; автор обозначает версию 0.3.0 как находящуюся в разработке, предупреждает об изменении формата файлов.
- LICENSE (blob `f288702d2fa16d3cdf0035b15a9fcbc552cd88e7`): GPL-3.0.
- Статус: подтверждён README, но релиз и отдельные функции отката пока требуют проверки.

Эти сведения не являются разрешением автоматически публиковать события без остальных проверок и review.

## Дополнительная проверка четырёх проектов

GitHub connector, README и LICENSE из default branch; зафиксированы Git blob SHA. Эти значения **не заменяют** snapshot JSON и SHA-256, необходимые Watch Updater.

| Проект | README blob | LICENSE blob | Подтверждённая лицензия | Статус |
|---|---|---|---|---|
| gedcom-go | `23e01f8642df45d430f9efde98a8f8fe45665d85` | `5c67c5841de1bb0b2712440dac0a76cffc896c78` | MIT | Библиотека существует; дельту 3.6.0 проверить по тегу |
| Kinprove recipes | `28573238ab7c0bdf78d9bef313bc68508a41fbb0` | `c94d31c1fecb2e4fe230476dac4572f08290c3df` | FSL-1.1-MIT | Методика и provenance описаны в README; дату конкретного рецепта проверить по коммиту |
| HTRflow | `2ab5b7aa9203df25af79946e782662fa7dc972d2` | `4153cd377537ff81e00f8a6453dc278600f4ef2b` | EUPL-1.2 | Интеграцию Kraken и независимые показатели проверить отдельно |
| Gramps Web API | `925d962b79329a521524485017d8bbab149ae399` | `be3f7b28e564e7dd05eaf59d64adba1a4065ac0e` | AGPL-3.0 | REST API подтверждён; breaking change и релизную версию проверить отдельно |

**Дополнительный кандидат соседнего контура:** [AI-Riksarkivet/ra-mcp](https://github.com/AI-Riksarkivet/ra-mcp) — по публичной документации объединяет IIIF, ALTO, поиск и MCP; ещё не оценён на новизну и не входит в утверждённый пакет. См. [CLAUDE.md](https://github.com/AI-Riksarkivet/ra-mcp/blob/main/CLAUDE.md).

**Не запускать публикацию автоматически из этой очереди:** необходимо определить точные дельты по коммитам/релизам, сравнить с опубликованным каталогом и сохранить валидные доказательства.

## Подтверждение точных изменений по Git-коммитам

Проверено GitHub Commit API, включая перечень изменённых файлов и diff. Это более сильное свидетельство дельты, чем README; не подменяет обязательный evidence snapshot для автоматического публикационного конвейера.

1. **Raisa MCP:** [6f1d1aa](https://github.com/igorkauf/raisa-mcp/commit/6f1d1aadbc83c7f331a9d31fc82ca5a67588b5bc) — первоначальное добавление файлов MCP, архивных адаптеров, README и MIT LICENSE. Тип события: `new_project`, если отсутствует в каталоге.
2. **Kinprove:** [11a493d](https://github.com/Kinprove/genealogy-research-recipes/commit/11a493d8197c42066e2fb7a8716f3bbb175a0354) — добавление provenance-файла `russian-village-family-reconstitution.yml` и обновление рецептов. По diff `PROVENANCE.md` количество sidecars выросло со 140 до 141, записей источников — с 4982 до 5042; это **заявленные числа в файле проекта**, не проверка качества источников.
3. **Gramps Web API:** [12f5e73](https://github.com/gramps-project/gramps-web-api/commit/12f5e73ed0e00158a6b84c32470cba5b3c103ee2) — ROADMAP переносит удаление `gql` на планируемую версию **3.26.0**, ожидаемую в конце ноября 2026. `gql` будет возвращать 422; предложен `MatchesQuery` с GOQL. **Это изменение в коде/плане разработки, а не подтверждение выхода релиза 3.26.0.**

Для остальных проектов ещё нужно сверить точную дельту с опубликованной карточкой, иначе событие может оказаться повтором.
