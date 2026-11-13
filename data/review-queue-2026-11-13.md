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
