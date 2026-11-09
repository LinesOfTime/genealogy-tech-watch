# GitHub Watch: проверка и применение 9 ноября 2026

База: `43b4d412dd1dc46d66a40b8ffcae567b0ac98f07`. Пакет: `watch-package.json`, четыре события, 15 снимков с SHA-256. Применение: локальные `watch_updater.prepare` → просмотр diff → `watch_updater.authorize` → `write_plan`, затем штатный `watch.py check`. Дополнительный запуск Watch Updater в Actions не нужен: пакет уже применён, повтор блокируется. Публикация подтверждается отдельно после push и успешного GitHub Pages.

| Репозиторий | Результат | Границы проверки |
| --- | --- | --- |
| thodel/agentic_historian | Новая карточка и исследовательский профиль | Швейцарские и немецкие административные рукописи XIV–XIX веков; инфраструктура/VPN Бернского университета. В pyproject.toml заявлена MIT, отдельного текста нет. Alpha, версия 0.1.0, GitHub-релизов нет. |
| rodoslovje/ged-merge | Новая карточка и профиль | Ручное согласование GEDCOM в браузере; английский/словенский интерфейс, словенские интеграции. MIT. Сетевые запросы дополнительных справочников и карт отмечены отдельно. Версия package.json 0.0.0, GitHub-релизов нет. |
| kjiwa/geneanet-drift | Новая карточка и профиль | Ручное сохранение просмотренных страниц Geneanet, локальное сравнение, отдельные права чтения/записи Gramps, preview/backup/undo по документации автора. MIT, Python 3.13+, версия 0.1.0, GitHub-релизов нет. |
| gramps-project/gramps-web | Обновлена история: 26.11.0–26.11.2 | Material Web, медиа, поиск, фильтры, задачи; исправление карты и возраста. Требование WebGL 2 и удаление семантического поиска сохранены. AGPLv3. P1 → P1 с отдельным обоснованием и пилотом. |

Последние проверенные коммиты:

- [thodel/agentic_historian](https://github.com/thodel/agentic_historian): https://raw.githubusercontent.com/thodel/agentic_historian/607a10015429d53934036f18ebaab772329adb2e/README.md

- [rodoslovje/ged-merge](https://github.com/rodoslovje/ged-merge): https://raw.githubusercontent.com/rodoslovje/ged-merge/3cb85c0f33cf4cb82ed0d77e6fbded7739ba0b72/README.md

- [kjiwa/geneanet-drift](https://github.com/kjiwa/geneanet-drift): https://raw.githubusercontent.com/kjiwa/geneanet-drift/4654e042f594390c45ec9eba7bd3f52247160757/README.md

- [gramps-project/gramps-web](https://github.com/gramps-project/gramps-web): https://raw.githubusercontent.com/gramps-project/gramps-web/385d68397f6c2d5890907e0b21f903479d13e589/LICENSE

Независимые испытания этих проектов не заявляются. Новым проектам не присвоена подтверждённая практическая оценка: требуется пилот на своих материалах. Сходные названия не считались алиасами. Все 188 прежних карточек сохранены; для Gramps Web добавлена история и обновлены метаданные оценки с сохранением P1.

Проверки до публикации:

- 177 Python-тестов: успешно.
- Валидация: 0 ошибок, 178 прежних предупреждений (включая два известных GitHub 404 и редакционные поля старого реестра).
- JSON import/export, отклонение опасных URL, согласованность root/docs/HTML seeds: успешно.
- Браузер Chrome: четыре проекта, поиск, карточки, фильтры, возврат/перезагрузка, импорт/экспорт, мобильная раскладка и шесть страниц навигации; ошибок JavaScript/console нет.
- 191 уникальная карточка, 170 расширенных исследований, 67 событий дайджеста.
- Все 15 снимков и хеши проверены; повторное применение пакета отклонено.

Исправление конвейера: повторная практическая оценка воспроизводится из утверждённого журнала с проверкой ledger и снимков; оценка синхронизируется с исследованием. Тесты блокируют удаление первоначального утверждения, журнала, ledger, подмену снимков, истории и текущего приоритета. Тип новых проектов и направления отдельно внесены в существующие решения классификации. GitHub Actions не добавлены и не изменены.

Изменены: catalog.json и docs/catalog.json; docs/research.json; digest.json и docs/digest.json; HTML seeds docs/index.html и docs/digest.html; docs/task-matches.json и docs/priority-review.json; data/discoveries.jsonl, data/applied-events.json, data/classification-decisions.json; watch-package.json и 15 файлов data/evidence/updater/watch-2026-11-09/; tools/apply_changes.py и tools/practical_priorities.py; три тестовых файла, UPDATER.md и этот отчёт.
