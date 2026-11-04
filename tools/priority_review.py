"""Audit retained priorities without manufacturing new scores or approvals."""
from collections import Counter
import re
from urllib.parse import urlsplit
from build_task_matches import role_for

STATES={
    'reference_issue':'Сначала проверить ссылку',
    'missing':'Оценка отсутствует',
    'changed':'Есть проверки после оценки',
    'triaged':'Только каталожный триаж',
    'proposed':'Предложение не утверждено',
    'approved':'Оценка утверждена',
}


def build(catalog,research,checks=None,proposals=None):
    proposals=proposals or {}
    missing={r['url'].lower().rstrip('/'):r for r in (checks or {}).get('records',[])
             if r.get('result')=='not_found' and r.get('http_status')==404}
    rows=[]
    for c in catalog:
        key=c['name'].lower();r=research.get(key,{})
        ev=c.get('evaluation') or {}
        date=str(ev.get('reviewed_at',''))[:10]
        events=[e for e in c.get('history',[])+r.get('watch_events',[]) if e.get('review_status')=='approved']
        latest=max((str(e.get('reviewed_at',e.get('date','')))[:10] for e in events),default='')
        url=c['url'].lower().rstrip('/')
        profile=bool(re.fullmatch(r'/[^/]+/?',urlsplit(url).path))
        reference=missing.get(url)
        state=('reference_issue' if reference or profile else 'missing' if not ev else
               'changed' if latest and date and latest>date else ev.get('review_status','missing'))
        if state not in STATES:state='missing'
        flags=[]
        if ev.get('evidence_level')=='E2' and not any(re.search(r'/(?:commit|commits)/[0-9a-fA-F]{40}(?:/|$)|/(?:blob|raw)/[0-9a-fA-F]{40}/|/releases/(?:tag|tags)/[^/]+',s) for s in ev.get('source_urls',[])):
            flags.append('Сохранённая E2-оценка не привязана к конкретной версии; проверить её основания отдельно от новых Watch-событий.')
        if ev and any(ev.get(f) is None for f in ('component_fit','russia_fit','maturity','license_risk','integration_effort')):
            flags.append('Не все оси оценены. Неизвестные значения не равны нулю; общий балл не рассчитывается.')
        if reference:action='В сохранённом аудите GitHub HTTP 404. Проверить существование и канонический адрес; не подбирать как рабочий инструмент до проверки.'
        elif profile:action='Это профиль владельца, не отдельный репозиторий. Разобрать семейство адаптеров и проверить нужный проект.'
        elif state=='changed':action='Сопоставить оценку с более поздними утверждёнными проверками; E-уровень и приоритет автоматически не повышать.'
        elif state=='missing':action='Выбрать задачу и роль проекта; проверить первоисточники и условия небольшой пробы до назначения приоритета.'
        elif state=='triaged':action='Проверить первоисточник, конкретный сценарий, вход и результат. Сохранённая метка не обоснована повторной оценкой.'
        else:action=ev.get('next_action') or 'Проверить условия небольшой практической пробы.'
        rows.append(dict(project=c['name'],url=c['url'],legacy_priority=c.get('priority','Не оценён'),
            priority_original=c.get('priority_original'),state=state,state_label=STATES[state],
            role=role_for(c,r),evidence_level=ev.get('evidence_level'),maturity=ev.get('maturity'),
            license_state=ev.get('license_risk'),integration_effort=ev.get('integration_effort'),
            reviewed_at=date or None,latest_source_review=latest or None,
            rationale=ev.get('priority_rationale') or 'Обоснование оценки отсутствует.',
            next_action=action,source_urls=ev.get('source_urls',[]),
            flags=flags,
            independent_report=ev.get('test_report_url'),evaluation_status=ev.get('review_status'),
            practical_proposal=proposals.get(key)))
    return dict(version=1,method='Практический выбор по задаче и роли; аудит сохранённых оценок, без новых баллов и утверждений',
        counts=dict(total=len(rows),priorities=dict(Counter(x['legacy_priority'] for x in rows)),
            states=dict(Counter(x['state'] for x in rows)),
            p1_e0=sum(x['legacy_priority']=='P1' and x['evidence_level']=='E0' for x in rows),
            missing_evaluations=sum(not c.get('evaluation') for c in catalog),
            independent_reports=sum(bool(x['independent_report']) for x in rows)),states=STATES,projects=rows)
