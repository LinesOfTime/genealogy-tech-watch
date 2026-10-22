# Аудит практических сценариев и ограничений

Проверены все 164 карточки. Проверка использует те же правила выбора полей, что и интерфейс. Новые исследовательские факты не выводятся.

- service_notes_preserved: 138
- missing_practical: 12
- duplicate_raw_notes: 78
- limitations_need_context_review: 3

Служебные заметки и исходные дубли сохраняются в данных; интерфейс не выводит их дважды в основном блоке. limitations_need_context_review — эвристический сигнал: содержание требует прочтения, а не автоматической правки.

## ai-historian/chronos

missing_practical, service_notes_preserved, duplicate_raw_notes

**Сценарий:** Не описан

**Ограничения:** Ограничено некоммерческим использованием; исходный код открыт для просмотра.

## ai-riksarkivet/htrflow

missing_practical, service_notes_preserved, duplicate_raw_notes

**Сценарий:** Не описан

**Ограничения:** Гибкие YAML-конвейеры, экспорт PAGE XML, ALTO XML, JSON, TXT. Лицензия моделей отдельно.

## ai-riksarkivet/htrflow_app

missing_practical, service_notes_preserved, duplicate_raw_notes

**Сценарий:** Не описан

**Ограничения:** Демо, не для production; поддерживаемые языки не включают русский в заявленном перечне.

## benwbrum/fromthepage

missing_practical, service_notes_preserved, duplicate_raw_notes

**Сценарий:** Не описан

**Ограничения:** README указывает Affero GPL; точный SPDX по LICENSE следует проверить отдельно.

## familysearch/gedcom

missing_practical, service_notes_preserved, duplicate_raw_notes

**Сценарий:** Не описан

**Ограничения:** Официальная спецификация GEDCOM 7, не готовая генеалогическая программа. Структуры SOUR, REPO, PAGE, QUAY, SCHMA; модель источников имеет признанные ограничения.

## genealogix/glx

missing_practical, service_notes_preserved, duplicate_raw_notes

**Сценарий:** Не описан

**Ограничения:** Evidence-first формат и CLI; не заменяет готовый GUI; статус beta

## gramps-project/gramps-web

missing_practical, service_notes_preserved, duplicate_raw_notes

**Сценарий:** Не описан

**Ограничения:** Frontend; package.json указывает AGPL без номера; не приписывать точный SPDX только по package.json

## linesoftime/yarchive-downloader

missing_practical, service_notes_preserved, duplicate_raw_notes

**Сценарий:** Не описан

**Ограничения:** Не считать наличие URL подтверждением функций или лицензии

## nikazzio/scriptoria

missing_practical, service_notes_preserved, duplicate_raw_notes

**Сценарий:** Не описан

**Ограничения:** Не считать наличие URL подтверждением функций или лицензии | IIIF библиотека, OCR/HTR, ручная проверка; работа не протестирована

## oh-kay-blanket/family-plot

service_notes_preserved, duplicate_raw_notes, limitations_need_context_review

**Сценарий:** Может помочь представить сложную структуру родства графически.

**Ограничения:** Нужны тесты на больших деревьях, браках между ветвями и кириллических именах.

## scripta/escriptorium

missing_practical, service_notes_preserved, duplicate_raw_notes

**Сценарий:** Не описан

**Ограничения:** Не считать наличие URL подтверждением функций или лицензии | GitHub-карточка может быть зеркалом; основной источник лицензии GitLab | Первичный источник лицензии — GitLab; проверить актуальность GitHub-зеркала отдельно

## worldhistoricalgazetteer/website

missing_practical, service_notes_preserved, duplicate_raw_notes

**Сценарий:** Не описан

**Ограничения:** Разные условия для программного кода, контента и внешних наборов; не смешивать.

## LinkedPasts/linked-places-format

missing_practical, service_notes_preserved, duplicate_raw_notes, limitations_need_context_review

**Сценарий:** Не описан

**Ограничения:** JSON-LD/GeoJSON-T для исторических топонимов

## recogito/recogito-js

service_notes_preserved, duplicate_raw_notes, limitations_need_context_review

**Сценарий:** Изучить принципы ручной разметки исторических документов.

**Ограничения:** Устаревшая библиотека: для новых проектов предпочтительно изучать поддерживаемых преемников.
