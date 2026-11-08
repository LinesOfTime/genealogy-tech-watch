# G-MCP-01: первый фактический запуск на Windows

**Цель:** создать воспроизводимую изолированную среду Gramps Web для Gramps MCP и выполнить upstream-интеграционные тесты. Это подготовительный этап, **не** выполнение сценариев T1–T7 и не независимое E3/E4.

## Проверенная исходная версия (срез 2026-11-09)

- Зеркало: https://github.com/Genealogy-MCP/gramps-mcp
- Коммит: `9ce862da7543ce09ef7683330fce049b1c7ff24b` (из GitHub API; основной upstream — GitLab)
- `pyproject.toml`: версия 3.15.27
- `docker-compose.test.yml`: Gramps Web 26.10.2 (образ с SHA256), Redis, PostgreSQL, Celery и тестовые тома
- `tests/fixtures/seed.gramps`: опубликованная fixture upstream (418644 байта на момент сверки)
- Makefile поддерживает `docker-up`, `docker-seed`, `test-unit`, тестовую группу integration.

Не используем `docker-compose.yml` с `latest` для воспроизводимого эксперимента и не подключаем основное дерево.

## Предпосылки

Windows 11 с Docker Desktop (запущенным Linux Engine), Git и `uv` (Python package manager). Команды должны быть доступны из PowerShell. Docker Desktop должен иметь достаточный запас памяти и диска. При отсутствии любой зависимости скрипт завершится ошибкой, не маскируя её успешным результатом.

## Одно действие из корня репозитория

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\run_gramps_baseline.ps1
```

Скрипт создаёт отдельную папку `local-gramps-baseline`, загружает исходный код upstream, переключается на **проверенный SHA**, устанавливает зависимости по lock-файлу, поднимает тестовый Gramps Web в отдельном Docker Compose-проекте `gtw-gramps-baseline`, засевает fixture и запускает `pytest -m integration --no-cov -q`.

Результаты: `local-gramps-baseline/logs/baseline-*.txt` и `baseline-*-metadata.json`. Они не являются доказательством независимости испытания. **Никакая запись в `docs/trials.json` не добавляется автоматически.**

Для удаления только тестовых томов upstream после проверки:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\run_gramps_baseline.ps1 -CleanupTestVolumes
```

Внимание: `-CleanupTestVolumes` вызывает `docker compose ... down -v` и уничтожает данные **только Compose-проекта `gtw-gramps-baseline`**. Не используйте его, если переименовали проект Compose или разместили в этой группе нужные данные.

## Следующая стадия

После успешного baseline — выполнить собственный протокол [G-MCP-01](PILOT_GRAMPS_MCP_01.md) T1–T7: чтение записей/цитирований, негативные ID, сравнение с Web API, отдельная проверка прав записи и фиксация снимков до/после. Для фиксации наблюдений предусмотрен [анализатор](GRAMPS_MCP_CAPTURE_RUNNER.md).

**Ограничения:** этот PowerShell-скрипт подготовлен для запуска пользователем на Windows, здесь не выполнялся. В текущем исполняющем окружении Docker отсутствует. Совместимость upstream-тестов с вашим компьютером до их запуска не подтверждена.
