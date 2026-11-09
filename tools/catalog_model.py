"""Source-bound classification and practical assessment currency for the existing catalog."""
import copy
from datetime import date
import json
from pathlib import Path


TYPES = {
    'application': 'Готовое приложение',
    'library': 'Библиотека / SDK',
    'ocr_model': 'OCR/HTR-модель',
    'general_model': 'ИИ-модель общего назначения',
    'dataset': 'Набор данных',
    'standard': 'Стандарт / спецификация',
    'adapter': 'Сервер / API / MCP-адаптер',
    'service': 'Архивный / исследовательский сервис',
    'prototype': 'Исследовательский прототип',
    'developer_tool': 'Инструмент разработки',
    'reference': 'Методика / документация',
    'unknown': 'Не определено',
}
DOMAINS = {
    'ocr': 'OCR/HTR', 'annotation': 'Сегментация и разметка',
    'archives': 'Цифровые архивы', 'images': 'IIIF и просмотр изображений',
    'indexing': 'Индексация и извлечение сущностей', 'gedcom': 'GEDCOM и моделирование данных',
    'agents': 'Исследовательские агенты и поиск', 'evidence': 'Источники, цитирование и доказательства',
    'linkage': 'Сопоставление записей и родства', 'places': 'Историческая география',
    'trees': 'Визуализация родословных', 'genetics': 'Генетическая генеалогия',
    'evaluation': 'Оценка качества и тестирование',
}
ORIGINS = {'initial': 'Первоначальный реестр', 'watch': 'GitHub Watch',
           'manual': 'Ручное добавление', 'unknown': 'Не установлено'}
CURRENCY = {'current': 'Актуален', 'reassess': 'Требует переоценки',
            'insufficient': 'Недостаточно данных', 'proposed': 'Предложена новая оценка'}
MODEL_FILES = ('data/classification-decisions.json', 'data/assessment-currency-review.json',
               'data/priority-reassessment-proposals.json', 'docs/source-updates.json')


def read(root, name):
    return json.loads((Path(root) / name).read_text(encoding='utf-8'))

def field_value(entity, field):
    value=entity
    for part in field.split('.'):
        value=value.get(part) if isinstance(value,dict) else None
    return value


def practical_value(card):
    assessment = card.get('practical_priority')
    return assessment.get('priority', 'Не оценён') if isinstance(assessment, dict) else 'Не оценён'


def protected_values(card):
    fields = ('name', 'url', 'section', 'priority', 'priority_original', 'evaluation',
              'practical_priority', 'practical_priority_history', 'history')
    return {field: copy.deepcopy(card.get(field)) for field in fields}


def classification(card, decision):
    if not decision:
        return dict(version=1, primary_type='unknown', type_label=TYPES['unknown'],
                    domains=[], domain_labels=[], origin='unknown', origin_label=ORIGINS['unknown'],
                    original_section=card.get('section'), sources=[],
                    reason='Новая запись ожидает редакционной классификации.')
    return dict(version=1, primary_type=decision['primary_type'], type_label=TYPES[decision['primary_type']],
                domains=decision['domains'], domain_labels=[DOMAINS[tag] for tag in decision['domains']],
                origin_label=ORIGINS[decision['origin']],
                origin=decision['origin'], original_section=card.get('section'),
                sources=copy.deepcopy(decision['sources']), reason=decision['reason'])


def assessment_currency(card, research, updates, review, proposal):
    p = card.get('practical_priority')
    p = p if isinstance(p, dict) else {}
    approved = p.get('review_status') == 'approved'
    approved_at = p.get('approved_at') if approved else None
    sources = []
    if approved:
        sources.append(dict(checked_at=p.get('reviewed_on') or approved_at,
                            kind='assessment_basis', urls=p.get('source_urls', [])))
    for event in card.get('history', []) + research.get('watch_events', []):
        if event.get('review_status') == 'approved' and event.get('source_urls'):
            source = dict(checked_at=event.get('reviewed_at') or event.get('date'),
                          kind='watch_source_review', urls=[s['url'] for s in event['source_urls']])
            if source not in sources:
                sources.append(source)
    if updates:
        sources.append(dict(checked_at=updates['checked_at'], kind='source_update',
                            urls=updates['sources']))
    if review and review.get('checked_at') and review.get('sources') and review.get('substantive', True):
        sources.append(dict(checked_at=review['checked_at'], kind='currency_review', urls=review['sources']))
    last_check = max((s['checked_at'][:10] for s in sources if s['checked_at']), default=None)
    state, reason = 'insufficient', 'Текущие условия пилота и основания оценки полностью не сверены.'
    if not approved:
        reason = 'Утверждённая практическая оценка отсутствует.'
    if review and review['assessment_hash'] == assessment_hash(p):
        state, reason = review['status'], review['reason']
    elif review:
        reason = 'После редакционной проверки изменилось основание оценки; нужна новая сверка.'
    if proposal and proposal.get('review_status') == 'pending' and proposal.get('previous_priority') == practical_value(card) and not approved:
        state, reason = 'proposed', proposal['reason']
    else:
        proposal = None
    return dict(status=state, label=CURRENCY[state], reason=reason,
                assessment_approved_at=approved_at,
                assessment_reviewed_on=p.get('reviewed_on') if approved else None,
                last_substantive_source_check=last_check,
                reviewed_at=review.get('reviewed_at') if review else None,
                sources=sources, pending_proposal=copy.deepcopy(proposal),
                evidence_level=p.get('evidence_level') if approved else None,
                assessment_sources=p.get('source_urls', []) if approved else [])


def assessment_hash(value):
    from practical_priorities import package_hash
    return package_hash(value or {})


def enrich(root, catalog, research):
    root = Path(root)
    if not (root / MODEL_FILES[0]).exists():
        return catalog
    decisions = read(root, MODEL_FILES[0])['projects']
    reviews = read(root, MODEL_FILES[1])['projects']
    proposals = read(root, MODEL_FILES[2])['projects']
    updates = {row['project'].lower(): row for row in read(root, 'docs/source-updates.json')['items']}
    result = copy.deepcopy(catalog)
    for card in result:
        key = card['name'].lower()
        card['classification'] = classification(card, decisions.get(key))
        card['assessment_currency'] = assessment_currency(
            card, research.get(key, {}), updates.get(key), reviews.get(key), proposals.get(key))
    return result


def model_issues(root, catalog, research):
    root = Path(root)
    if not (root / MODEL_FILES[0]).exists():
        return ([dict(level='error',code='catalog_model',location='catalog',
                      message='Enriched catalog lost its classification decisions')]
                if any(c.get('classification') for c in catalog if isinstance(c,dict)) else [])
    issues = []
    def error(message):
        issues.append(dict(level='error', code='catalog_model', location='catalog', message=message))
    try:
        decisions = read(root, MODEL_FILES[0])['projects']
        review_data = read(root, MODEL_FILES[1])
        reviews = review_data['projects']
        proposals = read(root, MODEL_FILES[2])['projects']
        names = {c['name'].lower() for c in catalog}
        if set(decisions) - names or set(reviews) - names:
            raise ValueError('Classification or currency review has unknown projects')
        import hashlib
        for proof in review_data.get('evidence', []):
            path=(root/proof['file']).resolve()
            if (not path.is_relative_to((root/'data/evidence').resolve())
                    or hashlib.sha256(path.read_bytes()).hexdigest()!=proof['sha256']):
                raise ValueError('Currency review evidence changed')
        for key, row in decisions.items():
            if (row['primary_type'] not in TYPES or row['origin'] not in ORIGINS
                    or not isinstance(row['domains'], list) or len(row['domains']) != len(set(row['domains']))
                    or any(tag not in DOMAINS for tag in row['domains']) or not row['reason']):
                raise ValueError('Invalid classification: ' + key)
            for source in row['sources']:
                if source['file'].startswith('data/evidence/priority-2026-11-04/'):
                    path=(root/source['file']).resolve()
                    if (not path.is_relative_to((root/'data/evidence/priority-2026-11-04').resolve())
                            or hashlib.sha256(path.read_bytes()).hexdigest()!=source['sha256']
                            or source['value'] not in read(root,source['file'])['content']):
                        raise ValueError('Classification primary source changed')
                    continue
                if source['file'] not in ('catalog.json', 'docs/research.json'):
                    raise ValueError('Invalid classification source')
                entity = next(c for c in catalog if c['name'].lower() == key) if source['file'] == 'catalog.json' else research.get(key, {})
                if field_value(entity, source['field']) != source['value']:
                    raise ValueError('Classification source changed; reclassify ' + key)
        for key, row in reviews.items():
            if row['status'] not in CURRENCY or not row['reason'] or not row['assessment_hash']:
                raise ValueError('Invalid currency review: ' + key)
            date.fromisoformat(row['reviewed_at'])
            if row['status'] == 'current' and (
                    set(row.get('verified_facets', [])) != {'purpose', 'access', 'version', 'compatibility', 'license', 'input_output', 'evidence'}
                    or not row.get('sources') or not row.get('checked_at')):
                raise ValueError('Current requires all assessment facets and sources')
            if row['status'] == 'reassess' and not row.get('delta'):
                raise ValueError('Reassessment requires a substantive delta')
        for key, row in proposals.items():
            card = next(c for c in catalog if c['name'].lower() == key)
            if (row['review_status'] != 'pending' or row['previous_priority'] not in ('P1', 'P2', 'P3', 'Не оценён')
                    or row['proposed_priority'] not in ('P1', 'P2', 'P3', 'Не оценён')
                    or row['evidence_level'] not in ('E0', 'E1', 'E2') or row['independent_test'] is not False):
                raise ValueError('Invalid or stale pending priority proposal')
            for field in ('reason','role','scope','input_output','task','pilot','recheck_trigger','limitations','license'):
                if not isinstance(row.get(field),str) or not row[field].strip():
                    raise ValueError('Missing proposal field: ' + field)
            if not row.get('sources'):
                raise ValueError('Proposal needs primary sources')
        expected = enrich(root, catalog, research)
        for actual, target in zip(catalog, expected):
            for field in ('classification', 'assessment_currency'):
                if actual.get(field) != target.get(field):
                    error(actual['name'] + ': stale or altered ' + field)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, StopIteration) as exc:
        error(str(exc))
    return issues


def schema():
    return {
        '$schema': 'https://json-schema.org/draft/2020-12/schema', 'title': 'Genealogy Tech Watch catalog',
        'type': 'array', 'items': {'type': 'object', 'required': ['name', 'url'],
            'properties': {
                'name': {'type':'string','minLength':1}, 'url': {'type':'string','format':'uri'},
                'classification': {'type':'object','required':['primary_type','domains','origin','sources','reason'],
                    'properties': {
                        'primary_type': {'enum':list(TYPES)}, 'domains':{'type':'array','uniqueItems':True,'items':{'enum':list(DOMAINS)}},
                        'origin':{'enum':list(ORIGINS)}, 'sources':{'type':'array'}, 'reason':{'type':'string','minLength':1}}},
                'assessment_currency': {'type':'object','required':['status','reason','assessment_approved_at','last_substantive_source_check'],
                    'properties': {'status':{'enum':list(CURRENCY)},'reason':{'type':'string','minLength':1}}},
            }, 'additionalProperties':True}}
