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
