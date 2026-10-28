# Аудит карточек каталога — 2026-10-28

**Охват:** все 175 карточек из `main/catalog.json`. Это автоматизированная инвентаризация полей и выявление рисков **без повторной проверки всех внешних репозиториев**. Порядок строк — очередь проверки, а не рейтинг полезности.

**Текущее распределение:** P1 — 62; P2 — 98; P3 — 3; не оценено — 12. У 136 карточек приоритет получен сопоставлением старых шкал и требует подтверждения.

## Системные проблемы

- P1 и P2 смешивают полезность, зрелость и качество свидетельств; это нужно развести по осям новой методики.
- Назначение разделов местами ошибочно: Gramps, Gramps Web API, GEDCOM X, webtrees и GeneWeb нуждаются в проверке классификации.
- Не все карточки содержат проверенные сведения о лицензиях, применимости в России и воспроизводимые результаты испытаний.
- Для новых находок нельзя считать дату включения в каталог датой релиза.
- Подробные исследования и история изменений должны ссылаться на конкретную проверенную версию, а не на недатированное описание.

## Ведомость по каждому проекту

Обозначения: «P: старая шкала» — существующий приоритет **не отменён**, но не подтверждён новыми критериями; «источники» — перепроверить актуальность; «раздел» — явный кандидат на перенос. Очередность определена количеством выявленных проблем данных, **не научной значимостью**.

| № | Проект | Текущий P | Необходимая проверка | Очередь |
|---:|---|:---:|---|---|
| 34 | [familysearch/gedcomx](https://github.com/familysearch/gedcomx) | P1 | P: старая шкала; Раздел: пересмотреть; Компоненты: уточнить | Высокая |
| 35 | [fisharebest/webtrees](https://github.com/fisharebest/webtrees) | P1 | P: старая шкала; Раздел: пересмотреть; Компоненты: уточнить | Высокая |
| 38 | [geneweb/geneweb](https://github.com/geneweb/geneweb) | P1 | P: старая шкала; Раздел: пересмотреть; Компоненты: уточнить | Высокая |
| 44 | [gramps-project/gramps](https://github.com/gramps-project/gramps) | P1 | P: старая шкала; Раздел: пересмотреть; Компоненты: уточнить | Высокая |
| 11 | [ajaskey/genealogy](https://github.com/ajaskey/genealogy) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 14 | [bhaskargautam/record-linkage](https://github.com/bhaskargautam/record-linkage) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 16 | [bruceyyu/ml-chinese-record-linkage](https://github.com/bruceyyu/ml-chinese-record-linkage) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 26 | [districtdatalabs/entity-resolution](https://github.com/districtdatalabs/entity-resolution) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 32 | [evelynkimm/ari](https://github.com/evelynkimm/ari) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 42 | [gramps-project/addons](https://github.com/gramps-project/addons) | P1 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 47 | [gramps-project/gramps-web-docs](https://github.com/gramps-project/gramps-web-docs) | P1 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 48 | [gsmitheidw/genealogytools](https://github.com/gsmitheidw/genealogytools) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 49 | [gusevlab/germline](https://github.com/gusevlab/germline) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 51 | [htrmopo/htrmopo](https://github.com/htrmopo/htrmopo) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 56 | [j535d165/data-matching-software](https://github.com/j535d165/data-matching-software) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 60 | [jameskane/decodingus-navigator](https://github.com/jameskane/decodingus-navigator) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 61 | [jasiek/genealogy-plugin](https://github.com/jasiek/genealogy-plugin) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 63 | [jitsi/jiwer](https://github.com/jitsi/jiwer) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 65 | [kanik0/rustenati](https://github.com/kanik0/rustenati) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 66 | [kasssandr/archilles](https://github.com/kasssandr/archilles) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 70 | [kkkamur07/nomikos](https://github.com/kkkamur07/nomikos) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 71 | [knuckles-team/gramps-mcp](https://github.com/knuckles-team/gramps-mcp) | P1 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 74 | [lieuwe89/genealogy-viz](https://github.com/lieuwe89/genealogy-viz) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 75 | [lovasoa/dezoomify-rs](https://github.com/lovasoa/dezoomify-rs) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 76 | [magne/vitni](https://github.com/magne/vitni) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 78 | [microsoft/graphrag](https://github.com/microsoft/graphrag) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 82 | [narasimhan-lab/repare](https://github.com/narasimhan-lab/repare) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 83 | [ngohung0704/rag-militai](https://github.com/ngohung0704/rag-militai) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 86 | [nikkoxgonzales/mcp-grampsweb](https://github.com/nikkoxgonzales/mcp-grampsweb) | P1 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 87 | [noahkiss/genealogy-mcp](https://github.com/noahkiss/genealogy-mcp) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 88 | [notakeith/handscribe](https://github.com/notakeith/handscribe) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 89 | [oh-kay-blanket/family-plot](https://github.com/oh-kay-blanket/family-plot) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 97 | [rue-a/provo](https://github.com/rue-a/provo) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 98 | [ruempel/nacarta](https://github.com/ruempel/nacarta) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 100 | [sandxlab/sandx-er](https://github.com/sandxlab/sandx-er) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 101 | [satvikgosai/genea-web](https://github.com/satvikgosai/genea-web) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 102 | [scheldt-llc/genealogy_ai](https://github.com/scheldt-llc/genealogy_ai) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 103 | [scormave/gramps-web-mcp](https://github.com/scormave/gramps-web-mcp) | P1 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 109 | [trungdong/prov](https://github.com/trungdong/prov) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 112 | [umb-oconnorgroup/ibdtools](https://github.com/umb-oconnorgroup/ibdtools) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 113 | [unstructured-io/unstructured-mlk-archive-public](https://github.com/unstructured-io/unstructured-mlk-archive-public) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 114 | [w3c/prov](https://github.com/w3c/prov) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 115 | [williamscole/haptic](https://github.com/williamscole/haptic) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 116 | [williamscole/ponderosa](https://github.com/williamscole/ponderosa) | P3 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 120 | [yingzhou001/ibdkin](https://github.com/yingzhou001/ibdkin) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 121 | [zal-analytics/zer](https://github.com/zal-analytics/zer) | P2 | P: старая шкала; Лицензия: уточнить; Источники: повторно проверить; Компоненты: уточнить | Высокая |
| 46 | [gramps-project/gramps-web-api](https://github.com/gramps-project/gramps-web-api) | P1 | Раздел: пересмотреть | Высокая |
| 140 | [recogito/pdf-annotator-js](https://github.com/recogito/pdf-annotator-js) | Не оценён | P: отсутствует; Компоненты: уточнить | Высокая |
| 141 | [recogito/recogito-js](https://github.com/recogito/recogito-js) | Не оценён | P: отсутствует; Компоненты: уточнить | Высокая |
| 164 | [geiserx/gramps-web-toolkit](https://github.com/GeiserX/gramps-web-toolkit) | Не оценён | P: отсутствует; Лицензия: уточнить; РФ: не оценено | Средняя |
| 165 | [kinprove/genealogy-research-recipes](https://github.com/Kinprove/genealogy-research-recipes) | Не оценён | P: отсутствует; Лицензия: уточнить; РФ: не оценено | Средняя |
| 166 | [b21-agency/gramps-ui](https://github.com/b21-agency/gramps-ui) | Не оценён | P: отсутствует; Лицензия: уточнить; РФ: не оценено | Средняя |
| 167 | [dsblank/gramps-connect-stories](https://github.com/dsblank/gramps-connect-stories) | Не оценён | P: отсутствует; Лицензия: уточнить; РФ: не оценено | Средняя |
| 168 | [device25/gedview](https://github.com/device25/gedview) | Не оценён | P: отсутствует; Лицензия: уточнить; РФ: не оценено | Средняя |
| 169 | [stanford-oval/sheldon](https://github.com/stanford-oval/sheldon) | Не оценён | P: отсутствует; Лицензия: уточнить; РФ: не оценено | Средняя |
| 171 | [archiveheritagegroup/ahg-archives-mcp](https://github.com/ArchiveHeritageGroup/ahg-archives-mcp) | Не оценён | P: отсутствует; Лицензия: уточнить; РФ: не оценено | Средняя |
| 172 | [archiveheritagegroup/heratio](https://github.com/ArchiveHeritageGroup/heratio) | Не оценён | P: отсутствует; Лицензия: уточнить; РФ: не оценено | Средняя |
| 173 | [yifenglu1999/ai-historian](https://github.com/YiFengLu1999/AI-Historian) | Не оценён | P: отсутствует; Лицензия: уточнить; РФ: не оценено | Средняя |
| 174 | [vaibhaav-tiwari/lineage](https://github.com/Vaibhaav-Tiwari/lineage) | Не оценён | P: отсутствует; Лицензия: уточнить; РФ: не оценено | Средняя |
| 1 | [23andme/bonsaitree](https://github.com/23andme/bonsaitree) | P3 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 2 | [abbyy/jfk-ocr](https://github.com/abbyy/jfk-ocr) | P2 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 3 | [abdash/roots-familytreevisualizer](https://github.com/abdash/roots-familytreevisualizer) | P2 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 4 | [aehrc/tribes](https://github.com/aehrc/tribes) | P2 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 5 | [ai-collaboratory/scribe](https://github.com/ai-collaboratory/scribe) | P2 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 6 | [ai-historian/chronos](https://github.com/ai-historian/chronos) | P1 | P: старая шкала; Компоненты: уточнить | Средняя |
| 7 | [ai-historian/chronos-benchmarks](https://github.com/ai-historian/chronos-benchmarks) | P1 | P: старая шкала; Компоненты: уточнить | Средняя |
| 8 | [ai-riksarkivet/htrflow](https://github.com/ai-riksarkivet/htrflow) | P2 | P: старая шкала; Компоненты: уточнить | Средняя |
| 9 | [ai-riksarkivet/htrflow-batch](https://github.com/ai-riksarkivet/htrflow-batch) | P2 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 10 | [ai-riksarkivet/htrflow_app](https://github.com/ai-riksarkivet/htrflow_app) | P2 | P: старая шкала; Компоненты: уточнить | Средняя |
| 12 | [archival-iiif/viewer](https://github.com/archival-iiif/viewer) | P1 | P: старая шкала; Компоненты: уточнить | Средняя |
| 13 | [benwbrum/fromthepage](https://github.com/benwbrum/fromthepage) | P2 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 15 | [browning-lab/hap-ibd](https://github.com/browning-lab/hap-ibd) | P3 | P: старая шкала; Компоненты: уточнить | Средняя |
| 17 | [cabout-me/gramps-mcp](https://github.com/cabout-me/gramps-mcp) | P1 | P: старая шкала; Компоненты: уточнить | Средняя |
| 19 | [cartwrightdj/gedcomtools](https://github.com/cartwrightdj/gedcomtools) | P1 | P: старая шкала; Компоненты: уточнить | Средняя |
| 20 | [cboulanger/tei-annotator](https://github.com/cboulanger/tei-annotator) | P2 | P: старая шкала; Компоненты: уточнить | Средняя |
| 21 | [clariah/burgerlinker](https://github.com/clariah/burgerlinker) | P1 | P: старая шкала; Компоненты: уточнить | Средняя |
| 22 | [claudiomartino/iiif-downloader](https://github.com/claudiomartino/iiif-downloader) | P1 | P: старая шкала; Компоненты: уточнить | Средняя |
| 23 | [dedupeio/dedupe](https://github.com/dedupeio/dedupe) | P2 | P: старая шкала; Компоненты: уточнить | Средняя |
| 24 | [digirati-co-uk/madoc-platform](https://github.com/digirati-co-uk/madoc-platform) | P2 | P: старая шкала; Компоненты: уточнить | Средняя |
| 25 | [digitalarchivst/open-genealogy](https://github.com/digitalarchivst/open-genealogy) | P2 | P: старая шкала; Компоненты: уточнить | Средняя |
| 27 | [dmarkey/irish-census-mcp](https://github.com/dmarkey/irish-census-mcp) | P2 | P: старая шкала; Компоненты: уточнить | Средняя |
| 28 | [dsblank/gramps-ez-mcp](https://github.com/dsblank/gramps-ez-mcp) | P1 | P: старая шкала; Компоненты: уточнить | Средняя |
| 29 | [dthaler/gedcom-citations](https://github.com/dthaler/gedcom-citations) | P1 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 30 | [ecoto/iiif_downloader](https://github.com/ecoto/iiif_downloader) | P1 | P: старая шкала; Компоненты: уточнить | Средняя |
| 31 | [erichare/kinresolve](https://github.com/erichare/kinresolve) | P2 | P: старая шкала; Компоненты: уточнить | Средняя |
| 33 | [familysearch/gedcom](https://github.com/familysearch/gedcom) | P1 | P: старая шкала; Компоненты: уточнить | Средняя |
| 36 | [freeukgen/myopicvicar](https://github.com/freeukgen/myopicvicar) | P2 | P: старая шкала; Компоненты: уточнить | Средняя |
| 39 | [glamberson/gedcom-evidence](https://github.com/glamberson/gedcom-evidence) | P1 | P: старая шкала; Компоненты: уточнить | Средняя |
| 40 | [glamberson/gedcom-occurrences](https://github.com/glamberson/gedcom-occurrences) | P1 | P: старая шкала; Компоненты: уточнить | Средняя |
| 41 | [google/family-tree](https://github.com/google/family-tree) | P2 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 43 | [gramps-project/addons-source](https://github.com/gramps-project/addons-source) | P1 | P: старая шкала; Компоненты: уточнить | Средняя |
| 45 | [gramps-project/gramps-web](https://github.com/gramps-project/gramps-web) | P1 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 50 | [hdlabconicet/recogito-tei](https://github.com/hdlabconicet/recogito-tei) | P2 | P: старая шкала; Компоненты: уточнить | Средняя |
| 52 | [iiif/api](https://github.com/iiif/api) | P1 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 53 | [iiif/awesome-iiif](https://github.com/iiif/awesome-iiif) | P1 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 54 | [iiif/website](https://github.com/iiif/website) | P1 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 55 | [ipums/hlink](https://github.com/ipums/hlink) | P1 | P: старая шкала; Компоненты: уточнить | Средняя |
| 57 | [j535d165/recordlinkage](https://github.com/j535d165/recordlinkage) | P2 | P: старая шкала; Компоненты: уточнить | Средняя |
| 58 | [j535d165/recordlinkage-annotator](https://github.com/j535d165/recordlinkage-annotator) | P2 | P: старая шкала; Компоненты: уточнить | Средняя |
| 59 | [j535d165/recordlinkage-review](https://github.com/j535d165/recordlinkage-review) | P2 | P: старая шкала; Компоненты: уточнить | Средняя |
| 62 | [jerged24/family-tree](https://github.com/jerged24/family-tree) | P2 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 64 | [jregimbal/iiif-downloader](https://github.com/jregimbal/iiif-downloader) | P1 | P: старая шкала; Компоненты: уточнить | Средняя |
| 67 | [keerthanamurugaraj/topic-rag-for-historical-newspapers](https://github.com/keerthanamurugaraj/topic-rag-for-historical-newspapers) | P2 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 68 | [kimon1230/gedcom_tools](https://github.com/kimon1230/gedcom_tools) | P1 | P: старая шкала; Компоненты: уточнить | Средняя |
| 69 | [kimon1230/gedgraph](https://github.com/kimon1230/gedgraph) | P2 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 72 | [komura-shoan/iiif-downloader](https://github.com/komura-shoan/iiif-downloader) | P1 | P: старая шкала; Компоненты: уточнить | Средняя |
| 73 | [libraryofcongress/gazetteer](https://github.com/libraryofcongress/gazetteer) | P2 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 77 | [meh313/htr-model-tester](https://github.com/meh313/htr-model-tester) | P2 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 79 | [mittagessen/kraken](https://github.com/mittagessen/kraken) | P2 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 80 | [moj-analytical-services/splink](https://github.com/moj-analytical-services/splink) | P2 | P: старая шкала; Компоненты: уточнить | Средняя |
| 81 | [n1kozor/tree-monk](https://github.com/n1kozor/tree-monk) | P2 | P: старая шкала; Компоненты: уточнить | Средняя |
| 84 | [nigelhorne/gedcom](https://github.com/nigelhorne/gedcom) | P1 | P: старая шкала; Компоненты: уточнить | Средняя |
| 85 | [nikazzio/scriptoria](https://github.com/nikazzio/scriptoria) | P2 | P: старая шкала; Компоненты: уточнить | Средняя |
| 90 | [omeka/omeka](https://github.com/omeka/omeka) | P2 | P: старая шкала; Компоненты: уточнить | Средняя |
| 91 | [omeka/omeka-s](https://github.com/omeka/omeka-s) | P2 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 92 | [openseadragon/openseadragon](https://github.com/openseadragon/openseadragon) | P2 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 93 | [projectmirador/mirador](https://github.com/projectmirador/mirador) | P2 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 94 | [qurator-spk/dinglehopper](https://github.com/qurator-spk/dinglehopper) | P2 | P: старая шкала; Компоненты: уточнить | Средняя |
| 95 | [recogito/text-annotator-js](https://github.com/recogito/text-annotator-js) | P2 | P: старая шкала; Компоненты: уточнить | Средняя |
| 96 | [rollybre/cthulhu](https://github.com/rollybre/cthulhu) | P2 | P: старая шкала; Компоненты: уточнить | Средняя |
| 99 | [ryanfb/iiif-dl](https://github.com/ryanfb/iiif-dl) | P1 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 104 | [scripta/escriptorium](https://github.com/scripta/escriptorium) | P1 | P: старая шкала; Компоненты: уточнить; РФ: не оценено | Средняя |
| 105 | [shelfgot/maatikshemua](https://github.com/shelfgot/maatikshemua) | P2 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 106 | [stefromlc/iiif-downloader](https://github.com/stefromlc/iiif-downloader) | P1 | P: старая шкала; Компоненты: уточнить | Средняя |
| 107 | [thisisankit27/f-tree](https://github.com/thisisankit27/f-tree) | P2 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 108 | [tropy/tropy](https://github.com/tropy/tropy) | P2 | P: старая шкала; Компоненты: уточнить | Средняя |
| 110 | [ub-mannheim/escriptorium](https://github.com/ub-mannheim/escriptorium) | P1 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 111 | [ub-mannheim/escriptorium_dokumentation](https://github.com/ub-mannheim/escriptorium_dokumentation) | P1 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 117 | [worldhistoricalgazetteer/documentation](https://github.com/worldhistoricalgazetteer/documentation) | P2 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 118 | [worldhistoricalgazetteer/website](https://github.com/worldhistoricalgazetteer/website) | P2 | P: старая шкала; Компоненты: уточнить | Средняя |
| 119 | [yfullteam/ytree](https://github.com/yfullteam/ytree) | P2 | P: старая шкала; Компоненты: уточнить | Средняя |
| 122 | [allmaps/allmaps](https://github.com/allmaps/allmaps) | P2 | P: старая шкала; Компоненты: уточнить | Средняя |
| 123 | [kartta-labs/mapwarper](https://github.com/kartta-labs/mapwarper) | P2 | P: старая шкала; Компоненты: уточнить | Средняя |
| 124 | [Segolene-Albouy/iiif-download](https://github.com/Segolene-Albouy/iiif-download) | P2 | P: старая шкала; Компоненты: уточнить | Средняя |
| 125 | [nypl-spacetime/nypl-warper](https://github.com/nypl-spacetime/nypl-warper) | P2 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 126 | [GeospatialCentroid/historic_map_explorer](https://github.com/GeospatialCentroid/historic_map_explorer) | P2 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 127 | [OpenRefine/OpenRefine](https://github.com/OpenRefine/OpenRefine) | P2 | P: старая шкала; Компоненты: уточнить | Средняя |
| 128 | [LinkedPasts/linked-places-format](https://github.com/LinkedPasts/linked-places-format) | P2 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 129 | [OpenRefine/FilesExtension](https://github.com/OpenRefine/FilesExtension) | P2 | P: старая шкала; Компоненты: уточнить | Средняя |
| 130 | [familysearch/gedcom-registries](https://github.com/FamilySearch/GEDCOM-registries) | P1 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 131 | [AleBeda/genechart](https://github.com/AleBeda/genechart) | P2 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 132 | [ADZirid/STEMMA](https://github.com/ADZirid/STEMMA) | P2 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 133 | [genea-app/genea-app](https://github.com/genea-app/genea-app) | P2 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 134 | [ryanturcotte/open-family-tree](https://github.com/ryanturcotte/open-family-tree) | P2 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 135 | [Mip555/root-free](https://github.com/Mip555/root-free) | P2 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 136 | [spacecat56/Ged2Reg](https://github.com/spacecat56/Ged2Reg) | P2 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 137 | [KeithPetro/Yggdrasil](https://github.com/KeithPetro/Yggdrasil) | P2 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 138 | [nigelhorne/ged2site](https://github.com/nigelhorne/ged2site) | P2 | P: старая шкала; Лицензия: уточнить; Компоненты: уточнить | Средняя |
| 139 | [glamberson/gedcom-tags](https://github.com/glamberson/gedcom-tags) | P2 | P: старая шкала; Компоненты: уточнить | Средняя |
| 142 | [Genealogy Research Workbench](https://github.com/glasgowm148/genealogy-research-workbench) | P1 | Лицензия: уточнить; Источники: повторно проверить; РФ: не оценено | Средняя |
| 143 | [IIIF Kasane](https://github.com/nakamura196/iiif-kasane) | P1 | Лицензия: уточнить; Источники: повторно проверить; РФ: не оценено | Средняя |
| 144 | [scan2gedcom](https://github.com/briancase1776/scan2gedcom) | P1 | Лицензия: уточнить; Источники: повторно проверить; РФ: не оценено | Средняя |
| 145 | [ZMO AI Pipelines](https://github.com/fmadore/zmo-ai-pipelines) | P2 | Лицензия: уточнить; Источники: повторно проверить; РФ: не оценено | Средняя |
| 146 | [genealogy-agent-skills](https://github.com/rfsbraz/genealogy-agent-skills) | P1 | Лицензия: уточнить; Источники: повторно проверить; РФ: не оценено | Средняя |
| 147 | [gramps-mcp-dotnet](https://github.com/zankul/gramps-mcp-dotnet) | P1 | Лицензия: уточнить; Источники: повторно проверить; РФ: не оценено | Средняя |
| 148 | [Rask](https://github.com/AI-Riksarkivet/rask) | P2 | Лицензия: уточнить; Источники: повторно проверить; РФ: не оценено | Средняя |
| 149 | [oxidged / OxidGene](https://github.com/trois-six/oxidged) | P1 | Лицензия: уточнить; Источники: повторно проверить; РФ: не оценено | Средняя |
| 150 | [Exscriptor](https://github.com/julioalonzom/exscriptor) | P1 | Лицензия: уточнить; Источники: повторно проверить; РФ: не оценено | Средняя |
| 151 | [Gramps Connect](https://github.com/dsblank/gramps-connect) | P1 | Лицензия: уточнить; Источники: повторно проверить; РФ: не оценено | Средняя |
| 152 | [GEDKeeper](https://github.com/Serg-Norseman/GEDKeeper) | P1 | Лицензия: уточнить; Источники: повторно проверить; РФ: не оценено | Средняя |
| 153 | [Bartelby](https://github.com/absaltfox/bartelby) | P1 | Лицензия: уточнить; Источники: повторно проверить; РФ: не оценено | Средняя |
| 154 | [Desembarque](https://github.com/allan-valin/ocr-gene-docs) | P1 | Лицензия: уточнить; Источники: повторно проверить; РФ: не оценено | Средняя |
| 155 | [Historic Records AI Reader](https://github.com/usulkies/historic-records-ai-reader) | P1 | Лицензия: уточнить; Источники: повторно проверить; РФ: не оценено | Средняя |
| 156 | [gedaudit](https://github.com/thobgg/gedaudit) | P1 | Лицензия: уточнить; Источники: повторно проверить; РФ: не оценено | Средняя |
| 157 | [open-ancestry](https://github.com/adamsilverstein/open-ancestry) | P1 | Лицензия: уточнить; Источники: повторно проверить; РФ: не оценено | Средняя |
| 158 | [NAFRec](https://github.com/Kansallisarkisto-AI/nafrec) | P1 | Лицензия: уточнить; Источники: повторно проверить; РФ: не оценено | Средняя |
| 159 | [Scribe](https://github.com/lehigh-university-libraries/scribe) | P1 | Лицензия: уточнить; Источники: повторно проверить; РФ: не оценено | Средняя |
| 160 | [gov-gazetteer-mcp](https://github.com/ianderso/gov-gazetteer-mcp) | P1 | Лицензия: уточнить; Источники: повторно проверить; РФ: не оценено | Средняя |
| 161 | [genealogy-mcp](https://github.com/igormel81/genealogy-mcp) | P1 | Лицензия: уточнить; Источники: повторно проверить; РФ: не оценено | Средняя |
| 162 | [Archive MCP adapters (ianderso)](https://github.com/ianderso) | P1 | Лицензия: уточнить; Источники: повторно проверить; РФ: не оценено | Средняя |
| 163 | [Gramps Evidence MCP](https://github.com/ianderso/gramps-evidence-mcp) | P1 | Лицензия: уточнить; Источники: повторно проверить; РФ: не оценено | Средняя |
| 18 | [cacack/my-family](https://github.com/cacack/my-family) | P1 | Базовые поля заполнены; требуется предметная проверка | Плановая |
| 37 | [genealogix/glx](https://github.com/genealogix/glx) | P1 | Базовые поля заполнены; требуется предметная проверка | Плановая |
| 170 | [denissergeevitch/ex-ussr-kinship-research](https://github.com/DenisSergeevitch/ex-ussr-kinship-research) | P1 | Лицензия: уточнить | Плановая |
| 175 | [mouchar/ftb-mcp](https://github.com/mouchar/ftb-mcp) | P2 | Лицензия: уточнить | Плановая |

## Правило внесения изменений

Эта ведомость не заменяет индивидуальную экспертную оценку. Нельзя массово переопределять P1–P3 по эвристике. По результатам следующего прохода для каждого проекта фиксируются доказательства, изменения с прошлого обзора и новая оценка по методике, затем обновляются данные сайта и проходят тесты.
