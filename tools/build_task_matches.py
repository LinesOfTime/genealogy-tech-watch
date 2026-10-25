"""Derive inspectable task suggestions from existing editorial fields, without ranking projects."""
import argparse
import hashlib
import json
from pathlib import Path
import re

TASKS = [
    ('transcribe','Распознать или расшифровать документы',r'OCR|HTR|распозна|транскри|расшифров'),
    ('download','Получить сканы из цифрового архива',r'загрузчик|скачив|загрузк.{0,30}(изображ|IIIF|скан)|получени.{0,25}(изображ|скан)'),
    ('resolve','Найти дубликаты людей и сопоставить записи',r'Person Resolver|сопоставлен.{0,25}(запис|сущност|персон)|дедуплика|повтор.{0,15}персон|record linkage'),
    ('places','Найти историческое место, название или приход',r'Place Resolver|газеттир|газетир|географ|приход|административн.{0,20}(делен|принадлеж)|АТД'),
    ('research','Вести исследование с источниками и гипотезами',r'Research Workspace|provenance|доказатель|гипотез|происхождени.{0,15}данных|исследовательск.{0,15}(кабинет|дел|пространств)'),
    ('gedcom','Проверить, преобразовать или показать GEDCOM',r'GEDCOM|родословн.{0,12}(дерев|данн)|визуализац.{0,20}(родослов|семейн)'),
    ('agents','Подключить ИИ к генеалогическим данным',r'API/MCP|\bMCP\b|ИИ.{0,12}(агент|помощник)|агентн.{0,12}(интерфейс|инструмент)'),
]
UNCERTAIN = re.compile(r'кандидат|возмож|может|могут|потенциаль|вероят|предполож',re.I)


ROLE_LABELS = dict(tool='Инструменты и библиотеки', data='Наборы данных и примеры',
                   reference='Спецификации и методики', unknown='Роль требует уточнения')


def role_for(card, research):
    # A presentation grouping, not a new claim of readiness or fitness for a task.
    options = [('docs/research.json','project_type',research.get('project_type')),
               ('catalog.json','project_type',card.get('project_type')),
               ('docs/research.json','editorial_summary',research.get('editorial_summary')),
               ('catalog.json','description',card.get('description'))]
    for file,field,text in options:
        if not isinstance(text,str) or not text.strip() or text.strip().lower().startswith('не установлен'):
            continue
        if UNCERTAIN.search(text):
            return dict(id='unknown',label=ROLE_LABELS['unknown'],source=dict(file=file,field=field,excerpt=text))
        groups = []
        if re.search(r'набор (данных|исторических документов|тестов)|корпус|датасет|benchmark',text,re.I):groups.append('data')
        if re.search(r'спецификац|стандарт|методик|документаци|справочник|каталог ссылок|рабочая группа',text,re.I):groups.append('reference')
        if re.search(r'программ|приложени|утилит|библиотек|движок|платформ|сервер|просмотрщик|загрузчик|frontend|CLI|REST API|веб-интерфейс|интерфейс проверки|HTR-систем|конвейер|инструмент',text,re.I):groups.append('tool')
        if len(groups)==1:
            return dict(id=groups[0],label=ROLE_LABELS[groups[0]],source=dict(file=file,field=field,excerpt=text))
        if len(groups)>1 or field=='project_type':
            return dict(id='unknown',label=ROLE_LABELS['unknown'],source=dict(file=file,field=field,excerpt=text))
    return dict(id='unknown',label=ROLE_LABELS['unknown'],source=None)


def build(catalog,research):
    tasks=[dict(id=key,title=title) for key,title,_ in TASKS]
    matches=[]
    for card in catalog:
        key=card['name'].lower(); r=research.get(key,{})
        fields=[]
        for field in ('description','use_case','limitations','components'):
            value=card.get(field)
            if isinstance(value,list): value=' · '.join(value)
            if isinstance(value,str) and value.strip(): fields.append(('catalog.json',field,value))
        for field in ('editorial_summary','editorial_use_case','guide_excerpt'):
            value=r.get(field)
            if isinstance(value,str) and value.strip():
                # Exclude license, URL, Russia rating and limitations from positive task matching.
                if field=='guide_excerpt':
                    value='\n'.join(line for line in value.splitlines() if line.startswith(('Назначение:','Возможности / сценарий:')))
                if value: fields.append(('docs/research.json',field,value))
        for task,_,pattern in TASKS:
            evidence=[]
            for file,field,text in fields:
                if field=='limitations': continue
                if re.search(pattern,text,re.I):
                    evidence.append(dict(file=file,key=key,field=field,excerpt=text,
                                         basis='Компонент каталога' if field=='components' else 'Редакционное описание/сценарий'))
            if not evidence: continue
            # Components alone suggest a direction but do not establish a usable scenario.
            candidate=all(e['field']=='components' for e in evidence) or any(UNCERTAIN.search(e['excerpt']) for e in evidence)
            limitations=r.get('editorial_limitations') or card.get('limitations') or 'Ограничения не установлены'
            matches.append(dict(task=task,project=card['name'],url=card['url'],
                status='candidate' if candidate else 'editorial',evidence=evidence,
                role=role_for(card,r),
                purpose=(card.get('description') if card.get('description_provenance') else r.get('editorial_summary') or card.get('description')) or 'Назначение не описано',
                use_case=r.get('editorial_use_case') or card.get('use_case') or 'Сценарий не описан',
                license=r.get('license') or card.get('license') or 'Лицензия не установлена',
                limitations=limitations,test_status=r.get('test_status') or card.get('test_status') or 'Испытания не подтверждены',
                russia_applicability=card.get('russia_applicability',{}).get('rating','Не оценено'),
                next_check='Проверить README, актуальность версии, лицензию и выполнить пробу на своих материалах.'))
    source_hash=hashlib.sha256(json.dumps([catalog,research],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    return dict(version=1,method='Лексическое соответствие существующим редакционным полям; не испытание и не рейтинг качества',
                source_hash=source_hash,tasks=tasks,matches=matches)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    result=build(json.loads((root/'catalog.json').read_text(encoding='utf-8')),
                 json.loads((root/'docs/research.json').read_text(encoding='utf-8')))
    data=(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode()
    target=root/'docs/task-matches.json'
    changed=not target.exists() or target.read_bytes()!=data
    if args.write and changed: target.write_bytes(data)
    print(json.dumps(dict(projects=len({x['project'] for x in result['matches']}),matches=len(result['matches']),changed=changed,write=args.write)))


if __name__=='__main__': main()
