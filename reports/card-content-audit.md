# Аудит практических сценариев и ограничений

Проверены все 164 карточки. Проверка использует те же правила выбора полей, что и интерфейс. Новые исследовательские факты не выводятся.

- service_notes_preserved: 138
- missing_practical: 20
- duplicate_raw_notes: 86
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

## dedupeio/dedupe

missing_practical, service_notes_preserved, duplicate_raw_notes

**Сценарий:** Не описан

**Ограничения:** Нужны обучение и ручная верификация совпадений; не генеалогическая программа.

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

## ipums/hlink

missing_practical, service_notes_preserved, duplicate_raw_notes

**Сценарий:** Не описан

**Ограничения:** Python; для Spark-сценариев требуется дополнительная среда.

## j535d165/recordlinkage

missing_practical, service_notes_preserved, duplicate_raw_notes

**Сценарий:** Не описан

**Ограничения:** Python-инструменты для сравнения, классификации и поиска дубликатов в табличных данных; могут формировать файлы для ручной разметки. Ограничения: Это программная библиотека, а не готовый генеалогический кабинет; нужны тестовые пары, оценка ошибок и сохранение исходных строк.

## linesoftime/yarchive-downloader

missing_practical, service_notes_preserved, duplicate_raw_notes

**Сценарий:** Не описан

**Ограничения:** Не считать наличие URL подтверждением функций или лицензии

## moj-analytical-services/splink

missing_practical, service_notes_preserved, duplicate_raw_notes

**Сценарий:** Не описан

**Ограничения:** Методы вероятностного связывания; не готовое генеалогическое приложение; версии API могут меняться.

## nikazzio/scriptoria

missing_practical, service_notes_preserved, duplicate_raw_notes

**Сценарий:** Не описан

**Ограничения:** Не считать наличие URL подтверждением функций или лицензии | IIIF библиотека, OCR/HTR, ручная проверка; работа не протестирована

## oh-kay-blanket/family-plot

service_notes_preserved, duplicate_raw_notes, limitations_need_context_review

**Сценарий:** Может помочь представить сложную структуру родства графически.

**Ограничения:** Нужны тесты на больших деревьях, браках между ветвями и кириллических именах.

## omeka/omeka-s

missing_practical, service_notes_preserved, duplicate_raw_notes

**Сценарий:** Не описан

**Ограничения:** Веб-платформа публикации связанных цифровых коллекций; требует серверного окружения LAMP.

## openseadragon/openseadragon

missing_practical, service_notes_preserved, duplicate_raw_notes

**Сценарий:** Не описан

**Ограничения:** Не считать наличие URL подтверждением функций или лицензии | Просмотрщик изображений высокого разрешения; не архив и не загрузчик

## projectmirador/mirador

missing_practical, service_notes_preserved, duplicate_raw_notes

**Сценарий:** Не описан

**Ограничения:** Не считать наличие URL подтверждением функций или лицензии | Просмотрщик IIIF, сравнение изображений и аннотации

## scripta/escriptorium

missing_practical, service_notes_preserved, duplicate_raw_notes

**Сценарий:** Не описан

**Ограничения:** Не считать наличие URL подтверждением функций или лицензии | GitHub-карточка может быть зеркалом; основной источник лицензии GitLab | Первичный источник лицензии — GitLab; проверить актуальность GitHub-зеркала отдельно

## worldhistoricalgazetteer/website

missing_practical, service_notes_preserved, duplicate_raw_notes

**Сценарий:** Не описан

**Ограничения:** Разные условия для программного кода, контента и внешних наборов; не смешивать.

## allmaps/allmaps

missing_practical, service_notes_preserved, duplicate_raw_notes

**Сценарий:** Не описан

**Ограничения:** Документация проекта; запуск не проверен

## LinkedPasts/linked-places-format

missing_practical, service_notes_preserved, duplicate_raw_notes, limitations_need_context_review

**Сценарий:** Не описан

**Ограничения:** JSON-LD/GeoJSON-T для исторических топонимов

## recogito/recogito-js

service_notes_preserved, duplicate_raw_notes, limitations_need_context_review

**Сценарий:** Изучить принципы ручной разметки исторических документов.

**Ограничения:** Устаревшая библиотека: для новых проектов предпочтительно изучать поддерживаемых преемников.
