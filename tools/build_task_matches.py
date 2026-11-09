"""Derive inspectable task suggestions from existing editorial fields, without ranking projects."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from usage_guidance import load_context, TASK_CHECKS

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


def build(catalog,research,usage=None):
    usage=usage or dict(version=1,projects={})
    tasks=[dict(id=key,title=title) for key,title,_ in TASKS]
    matches=[]
    for card in catalog:
        if card.get('repository_reference_issue',{}).get('result') in ('not_found','owner_profile'):continue
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
                practical_priority=card.get('practical_priority'),
                role=role_for(card,r),
                purpose=(card.get('description') if card.get('description_provenance') else r.get('editorial_summary') or card.get('description')) or 'Назначение не описано',
                use_case=r.get('editorial_use_case') or card.get('use_case') or 'Сценарий не описан',
                license=r.get('license') or card.get('license') or 'Лицензия не установлена',
                limitations=limitations,test_status=r.get('test_status') or card.get('test_status') or 'Испытания не подтверждены',
                russia_applicability=card.get('russia_applicability',{}).get('rating','Не оценено'),
                usage_context=usage['projects'].get(key),
                next_check=TASK_CHECKS[task]))
            if card.get('legal_notes'):
                matches[-1]['legal_notes'] = card['legal_notes']
    source_hash=hashlib.sha256(json.dumps([catalog,research,usage],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    return dict(version=1,method='Лексическое соответствие существующим редакционным полям; не испытание и не рейтинг качества',
                source_hash=source_hash,tasks=tasks,matches=matches)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    catalog=json.loads((root/'catalog.json').read_text(encoding='utf-8'))
    research=json.loads((root/'docs/research.json').read_text(encoding='utf-8'))
    from catalog_model import enrich
    catalog=enrich(root,catalog,research)
    usage=load_context(root,catalog,research)
    result=build(catalog,research,usage)
    data=(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode()
    from apply_changes import encoded,digest_bytes,write_plan
    html=(root/'docs/index.html').read_text(encoding='utf-8')
    payload=json.dumps(usage,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
    script='<script type="application/json" id="usage-seed">'+payload+'</script>'
    if 'id="usage-seed"' in html:
        html,count=re.subn(r'<script\b[^>]*\bid="usage-seed"[^>]*>.*?</script>',lambda _:script,html,flags=re.S)
        if count!=1:raise ValueError('Expected exactly one usage seed')
    else:
        marker='<script>\nconst $='
        if html.count(marker)!=1:raise ValueError('Cannot locate catalogue renderer for usage seed')
        html=html.replace(marker,script+'\n'+marker)
    files={'docs/task-matches.json':data,'docs/usage-context.json':encoded(usage),'docs/index.html':html.encode('utf-8')}
    from apply_changes import sync_payloads
    synced=sync_payloads(root,catalog=catalog)
    # Merge the usage seed into the page containing the synchronized catalog seed.
    synced['docs/index.html']=re.sub(r'<script\b[^>]*\bid="usage-seed"[^>]*>.*?</script>',
        lambda _:script,synced['docs/index.html'].decode('utf-8'),flags=re.S).encode('utf-8')
    files.update(synced)
    from catalog_model import schema
    if (root/'data/classification-decisions.json').exists():
        files['docs/catalog.schema.json']=encoded(schema())
    if (root/'docs/priorities-ui.js').exists():
        from priority_review import build as review_priorities
        audit=root/'reports/repository-existence.json'
        checks=json.loads(audit.read_text(encoding='utf-8')) if audit.exists() else {}
        from practical_priorities import load_proposals, merge_source_audit
        proposals=load_proposals(root,catalog)
        files['docs/priority-review.json']=encoded(review_priorities(catalog,research,merge_source_audit(root,checks),proposals))
    before={name:(root/name).read_bytes() if (root/name).exists() else None for name in files}
    files={name:raw for name,raw in files.items() if before[name]!=raw}
    changed=bool(files)
    if args.write and files:
        plan_hash=digest_bytes(encoded({name:digest_bytes(raw) for name,raw in files.items()}))
        write_plan(root,dict(files=files,before=before,plan_hash=plan_hash),plan_hash)
    print(json.dumps(dict(projects=len({x['project'] for x in result['matches']}),matches=len(result['matches']),changed=changed,write=args.write)))


if __name__=='__main__': main()
