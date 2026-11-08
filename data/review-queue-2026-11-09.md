# Выборочный аудит первоисточников — 9 ноября 2026

**Объём:** четыре проекта из [очереди 8 ноября](review-queue-2026-11-08.md). Проверены GitHub API, дерево файлов, README, лицензии и pyproject/package по доступным репозиториям. Никакой код индексируемых проектов не выполнялся; независимых испытаний нет. Выводы отражают доступное на дату среза, не будущие изменения.

## Результаты

| Проект | Результат проверки | Вывод для каталога | Следующая операция |
|---|---|---|---|
| `b21-agency/gramps-ui` | GitHub REST `GET /repos/b21-agency/gramps-ui` и `GET /contents/` возвращают **404** | Ранее сохранённые сведения о релизе 0.1.0/AGPL **не перепроверены**. Не объявлять удаление или закрытие: репозиторий может быть перемещён либо недоступен | Сохранить историческую карточку, отметить недоступность адреса, проверить перемещение/официальный адрес; не присваивать P без данных |
| `PioneerAIAcademy/cowork-genealogy` | На commit `97221bd3c721af05c012b539091decb6e8e10960` в корне есть полный текст **Apache License 2.0**; README обозначает проект **alpha**, требует FamilySearch и Claude Cowork; package.json содержит monorepo и Node >=22 | Лицензия в корне **подтверждена на указанной версии**. Поддержка других платформ и проверяемость заявлений README независимо не установлены | Обновить лицензионные и системные заметки в карточке через штатный механизм; пилот на синтетическом кейсе, не на персональных данных |
| `semanticmeaning/kinship-kit` | Commit `4d90a0621febc37479ac265f41649a357e7a2558` неизменен относительно очереди; LICENSE — MIT, pyproject — **0.5.2**, Python >=3.10, dependencies = []; README подтверждает CLI `kin`, навык Claude Code/Codex и отдельно хранимые семейные дела | Предыдущая проверка **остаётся актуальной по текущему GitHub main**; это подтверждает документацию, не работоспособность и не приватность на практике | Проверка создания дела, противоречивых гипотез, отрицательного поиска и экспорта на синтетических данных |
| `joaquimrcarvalho/personal-historical-archive` | GitHub main `247d4ce89fe7c22f492bb79bc9770f674ac4b28d`; `pyproject.toml` теперь **0.47.0**, ранее в очереди 0.46.7. README описывает извлечение с VLM, опциональное редактирование/кодирование и поиск через MCP; в корне `LICENSE` не обнаружен | **Зафиксировано изменение версии.** Отсутствие `LICENSE` в корне не доказывает отсутствие лицензии вообще. Не утверждать разрешение на перераспространение или интеграцию | Сверить изменения 0.46.7→0.47.0, найти юридические условия в других файлах/документах, затем протестировать provenance транскрипций |

## Проверяемые первоисточники

- [gramps-ui — GitHub](https://github.com/b21-agency/gramps-ui) — текущая попытка GitHub API: HTTP 404; исторические утверждения из старой карточки не перепроверены.
- [cowork-genealogy — конкретный commit](https://github.com/PioneerAIAcademy/cowork-genealogy/tree/97221bd3c721af05c012b539091decb6e8e10960) · [LICENSE](https://github.com/PioneerAIAcademy/cowork-genealogy/blob/97221bd3c721af05c012b539091decb6e8e10960/LICENSE) · [README](https://github.com/PioneerAIAcademy/cowork-genealogy/blob/97221bd3c721af05c012b539091decb6e8e10960/README.md) · [package.json](https://github.com/PioneerAIAcademy/cowork-genealogy/blob/97221bd3c721af05c012b539091decb6e8e10960/package.json).
- [kinship-kit — конкретный commit](https://github.com/semanticmeaning/kinship-kit/tree/4d90a0621febc37479ac265f41649a357e7a2558) · [LICENSE](https://github.com/semanticmeaning/kinship-kit/blob/4d90a0621febc37479ac265f41649a357e7a2558/LICENSE) · [pyproject](https://github.com/semanticmeaning/kinship-kit/blob/4d90a0621febc37479ac265f41649a357e7a2558/pyproject.toml).
- [personal-historical-archive — конкретный commit](https://github.com/joaquimrcarvalho/personal-historical-archive/tree/247d4ce89fe7c22f492bb79bc9770f674ac4b28d) · [pyproject](https://github.com/joaquimrcarvalho/personal-historical-archive/blob/247d4ce89fe7c22f492bb79bc9770f674ac4b28d/pyproject.toml) · [README](https://github.com/joaquimrcarvalho/personal-historical-archive/blob/247d4ce89fe7c22f492bb79bc9770f674ac4b28d/README.md).

## Итог

Ревизия не является независимым тестом. **Приоритеты, E-уровни и содержание карточек JSON автоматически не менялись.** Корректировки карточек следует проводить через действующий pipeline, который сохраняет историю, и проверять влияние на опубликованные данные. В частности, 404 — статус ссылки, а не оценка полезности.
