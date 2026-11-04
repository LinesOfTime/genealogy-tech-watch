# Упрощённая публикация Genealogy Tech Watch

Единая точка входа поверх действующего `tools/watch_pipeline.py`, без изменения правил утверждения, JSON-схемы и существующего механизма синхронизации.

```powershell
# 1. Получить от исследовательского агента JSONL с событиями review_status=pending
python tools/watch.py ingest candidates.jsonl

# 2. Проверить журнал и получить план и plan_hash
python tools/watch.py prepare --date 2026-11-04

# 3. После явного утверждения событий по DISCOVERY_WORKFLOW.md:
python tools/watch.py publish --date 2026-11-04 --expect-plan ПОЛУЧЕННЫЙ_PLAN_HASH

# 4. Просмотреть diff, выборочно добавить изменённые файлы, commit/push, merge
git diff --check
git diff --stat
```

**Ограничения:** `ingest` не принимает утверждённые события, не делает сетевой поиск и не подтверждает достоверность источников. `prepare` ничего не записывает. `publish` запускает локальный apply, validate и unit tests, но не делает git push и не публикует Pages. Предыдущие одобрения в основном журнале остаются в силе только при совпадении хеша содержимого. Обновление статусов на сайте и PR-автоматизация — отдельный следующий этап.

**Оператору:** не передавать плановый hash из чужого запуска; перед применением проверить diff и события. GitHub Actions не добавляются.
