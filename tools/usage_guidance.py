"""Source-bound presentation hints. Never infer coverage from owner, language or Russia rating."""
import json
from pathlib import Path
import re

TASK_CHECKS = {
    'transcribe': 'Возьмите страницу с известной расшифровкой. Сравните ошибки имён, дат и порядок строк; сохраните оригинал рядом с результатом.',
    'download': 'Проверьте один документ и диапазон страниц: полноту изображений, разрешение, ссылки на оригинал и права на дальнейшее использование.',
    'resolve': 'На копии данных проверьте известный дубль и двух разных однофамильцев. Сравните источники и убедитесь, что ошибочное объединение можно отменить.',
    'places': 'Проверьте историческое название, нужный год и административную принадлежность по источнику. Совпадение современного названия не подтверждает место события.',
    'research': 'Проследите одно утверждение до документа и страницы. Проверьте, что цитата, гипотеза, исправление и противоречащие сведения сохраняются раздельно.',
    'gedcom': 'Используйте копию GEDCOM. Сравните до и после количество людей, связи, даты, ссылки на источники и неподдержанные поля; сохраните исходный файл.',
    'agents': 'Начните с чтения одной записи на тестовых данных. Перед записью проверьте права, подтверждение изменения, резервную копию и способ восстановления.',
}


def build_context(catalog, research, profiles):
    by_repo={c['url'].lower().rstrip('/').removeprefix('https://github.com/'):c for c in catalog}
    result={}
    for p in profiles.get('projects',[]):
        repo=p['repository'].lower()
        if repo not in by_repo:raise ValueError('Unknown guidance repository: '+repo)
        card=by_repo[repo]; key=card['name'].lower(); source=p['source']
        if key in result:raise ValueError('Duplicate usage guidance: '+key)
        if source['file'] not in ('catalog.json','docs/research.json'):raise ValueError('Unsupported guidance source')
        if source['field'] not in ('description','editorial_summary','editorial_use_case'):raise ValueError('Coverage needs a descriptive source, not origin or Russia rating')
        record=card if source['file']=='catalog.json' else research.get(key,{})
        original=record.get(source['field'],'')
        if not source['excerpt'] or source['excerpt'] not in original:raise ValueError('Stale usage guidance evidence: '+key)
        for field in ('label','scenario','boundary'):
            if not isinstance(p.get(field),str) or not p[field].strip():raise ValueError('Missing guidance '+field)
        if not isinstance(p.get('regions'),list) or not p['regions'] or any(not isinstance(v,str) or not v.strip() for v in p['regions']):raise ValueError('Invalid geography labels')
        if p['scope'] not in ('archive','collection','mixed','editorial'):raise ValueError('Invalid geographic scope')
        result[key]={k:p[k] for k in ('label','regions','scope','scenario','boundary')}
        result[key]['evidence']={**source,'key':key,'original_text':original,'basis':'Редакционное уточнение по сохранённому описанию; не независимое испытание'}
    return dict(version=1,method=profiles.get('basis','Редакционные подсказки по сохранённым материалам'),projects=result)


def load_context(root,catalog,research):
    path=Path(root)/'data/usage-guidance.json'
    return build_context(catalog,research,json.loads(path.read_text(encoding='utf-8'))) if path.exists() else dict(version=1,projects={})


def usage_issues(root,catalog,research):
    root=Path(root)
    if not (root/'data/usage-guidance.json').exists():return []
    try:
        expected=load_context(root,catalog,research)
        actual=json.loads((root/'docs/usage-context.json').read_text(encoding='utf-8'))
        if expected!=actual:raise ValueError('usage-context.json differs from source-bound guidance')
        html=(root/'docs/index.html').read_text(encoding='utf-8')
        seeds=re.findall(r'<script\b[^>]*\bid="usage-seed"[^>]*>(.*?)</script>',html,re.S)
        if len(seeds)!=1 or json.loads(seeds[0])!=expected:raise ValueError('Usage HTML seed differs from source-bound guidance')
    except (OSError,ValueError,KeyError,TypeError) as exc:return [str(exc)]
    return []
