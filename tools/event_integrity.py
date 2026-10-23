"""Validate reviewed pipeline events across published stores and the local ledger."""
from datetime import date, datetime
import json
from pathlib import Path

from discoveries import SOURCE_TYPES, content_hash, http_url, read_jsonl


def event_issues(root, catalog, research, digest):
    issues = []
    def error(location, message):
        issues.append(dict(level='error',code='reviewed_event',location=location,message=message))
    items = [(f'digest[{i}].items[{j}]', item) for i,day in enumerate(digest)
             if isinstance(day,dict) and isinstance(day.get('items'),list)
             for j,item in enumerate(day['items']) if isinstance(item,dict) and 'discovery_id' in item]
    history = [(card,event) for card in catalog if isinstance(card,dict) and isinstance(card.get('history'),list)
               for event in card['history'] if isinstance(event,dict) and 'discovery_id' in event]
    extended = [(key,event) for key,card in research.items() if isinstance(card,dict) and isinstance(card.get('watch_events'),list)
                for event in card['watch_events'] if isinstance(event,dict) and 'discovery_id' in event]
    if not (items or history or extended) and not (Path(root)/'data/applied-events.json').exists():
        return issues
    root=Path(root)
    try:
        ledger=json.loads((root/'data/applied-events.json').read_text(encoding='utf-8'))
        if not isinstance(ledger,dict):
            raise ValueError('Expected object')
    except (OSError,ValueError) as exc:
        error('data/applied-events.json',str(exc)); ledger={}
    journal={}
    if (root/'data/discoveries.jsonl').exists():
        try:
            for record in read_jsonl(root/'data/discoveries.jsonl'):
                key=record.get('discovery_id')
                if not isinstance(key,str) or not key or key in journal:
                    raise ValueError('Missing or duplicate journal discovery_id')
                journal[key]=record
        except (OSError,ValueError) as exc:
            error('data/discoveries.jsonl',str(exc))
    else:
        error('data/discoveries.jsonl','Applied events require their reviewed discovery journal')
    ids=[event.get('discovery_id') for _,event in items+[(None,e) for _,e in history+extended]]
    for key in sorted({x for x in ids if isinstance(x,str) and x} | set(ledger)):
        loc='event:'+key
        h=[(c,e) for c,e in history if e.get('discovery_id')==key]
        r=[(k,e) for k,e in extended if e.get('discovery_id')==key]
        d=[(at,e) for at,e in items if e.get('discovery_id')==key]
        if len(h)!=1 or len(r)!=1 or len(d)>1:
            error(loc,'Expected one catalogue history event, one research event, and at most one digest event')
            continue
        card,event=h[0]
        if r[0][0]!=str(card.get('name','')).lower() or r[0][1]!=event:
            error(loc,'Catalogue and research event differ or identity mismatch')
        if not isinstance(ledger.get(key),str) or ledger[key]!=event.get('reviewed_content_hash'):
            error(loc,'Ledger hash differs from reviewed history event')
        records=[event]+[item for _,item in d]
        for value in records:
            if value.get('review_status')!='approved':
                error(loc,'New event must have review_status=approved')
            for field in ('reviewer','significance_reason','previous_state','new_state','change'):
                if not isinstance(value.get(field),str) or not value[field].strip():
                    error(loc,'Missing nonempty text: '+field)
            try:
                date.fromisoformat(value['date' if value is event else 'event_date'])
            except (KeyError,TypeError,ValueError):
                error(loc,'Invalid event date')
            try:
                timestamp=datetime.fromisoformat(value['reviewed_at'].replace('Z','+00:00'))
                if timestamp.tzinfo is None:
                    raise ValueError('timezone required')
            except (KeyError,TypeError,ValueError,AttributeError):
                error(loc,'Invalid review timestamp')
            sources=value.get('source_urls')
            if not isinstance(sources,list) or not sources or any(
                    not isinstance(s,dict) or not isinstance(s.get('type'),str) or s['type'] not in SOURCE_TYPES or
                    not http_url(s.get('url')) for s in sources):
                error(loc,'Invalid typed HTTPS sources')
            elif value.get('url' if value is event else 'link') not in [s['url'] for s in sources]:
                error(loc,'Main source link is missing from source_urls')
        for _,item in d:
            if item.get('repo')!=card.get('name'):
                error(loc,'Digest project identity differs from catalogue')
            for field in ('change','previous_state','new_state','significance_reason','source_urls',
                          'review_status','reviewer','reviewed_at'):
                if item.get(field)!=event.get(field):
                    error(loc,'Digest and history differ: '+field)
            if item.get('event_date')!=event.get('date'):
                error(loc,'Digest event date differs from history')
        if key in journal:
            record=journal[key]
            from source_evidence import evidence_errors
            for message in evidence_errors(root,record):error(loc,message)
            if record.get('review_status')!='approved' or content_hash(record)!=ledger.get(key) or record.get('reviewed_content_hash')!=ledger.get(key):
                error(loc,'Journal approval/hash differs from applied event')
            if record.get('decision')=='publish' and len(d)!=1:
                error(loc,'Published journal event is absent from digest')
            if record.get('decision')=='research_only' and d:
                error(loc,'Research-only event must not be in digest')
            expected=dict(change=record.get('change_summary'),date=record.get('event_date'),
                          previous_state=record.get('previous_state'),new_state=record.get('new_state'),
                          significance_reason=record.get('significance_reason'),source_urls=record.get('source_urls'),
                          reviewer=record.get('reviewer'),reviewed_at=record.get('reviewed_at'),
                          claims_vs_verified=record.get('claims_vs_verified'),risks=record.get('risks'),
                          license=record.get('license'),license_evidence=record.get('license_evidence'))
            for field,value in expected.items():
                if event.get(field)!=value:
                    error(loc,'Applied content differs from reviewed journal: '+field)
        else:
            error(loc,'Applied event is absent from discovery journal')
    if any(not isinstance(x,str) or not x for x in ids):
        error('events','Invalid discovery_id')
    return issues
