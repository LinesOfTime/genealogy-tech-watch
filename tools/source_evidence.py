"""Verify saved primary-source bytes and bind them to the reviewed candidate."""
from datetime import datetime,timezone,timedelta
import hashlib
import json
from pathlib import Path

# Historical approved event: pin its existing static verification artifact without
# rewriting the original review. New candidates must use per-source snapshots.
LEGACY = {'github:ai-riksarkivet/htrflow-batch:d087c1ec02417c73e4061b8a54fc44627424d876':
    ('01d8bf9efaf1c5f32fd9ced34c91d8348f627786dea9f1bcf13565bbbc90957c',
     'data/evidence/htrflow-reading-order-2026-10-21.json',
     '7f9c5cfede221ca6faca9ef8e5eb4d5795c3e6b1b0ee10e6742290ac94418c57')}


def evidence_errors(root,record):
    root=Path(root).resolve();errors=[]
    def saved(name,expected):
        path=(root/name).resolve()
        if not path.is_relative_to(root/'data/evidence'):raise ValueError('Evidence must be inside data/evidence')
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('Evidence bytes/hash differ')
        return raw
    try:
        legacy=LEGACY.get(record.get('discovery_id'))
        if legacy and record.get('reviewed_content_hash')==legacy[0]:
            saved(legacy[1],legacy[2]);return []
        claims=record.get('claims_vs_verified')
        if not isinstance(claims,dict) or any(not isinstance(claims.get(k),str) or not claims[k].strip()
            for k in ('verified','author_claims','independent_testing')):
            raise ValueError('Separate verified facts, author claims and independent testing explicitly')
        checks=record.get('source_checks')
        if not isinstance(checks,list) or not checks:raise ValueError('Approved candidate requires saved source_checks')
        reviewed=datetime.fromisoformat(record['reviewed_at'].replace('Z','+00:00'))
        detected=datetime.fromisoformat(record['detected_at'].replace('Z','+00:00'))
        if reviewed.tzinfo is None or detected.tzinfo is None or reviewed<detected:raise ValueError('Review precedes detection')
        if reviewed>datetime.now(timezone.utc)+timedelta(minutes=5):raise ValueError('Review timestamp is in the future')
        expected={s['url'] for s in record['source_urls']}
        actual=[]
        for check in checks:
            if not isinstance(check,dict):raise ValueError('Invalid source check')
            url=check['url'];actual.append(url)
            stamp=datetime.fromisoformat(check['checked_at'].replace('Z','+00:00'))
            if stamp.tzinfo is None or not detected<=stamp<=reviewed:raise ValueError('Source must be checked between detection and approval')
            raw=saved(check['evidence_file'],check['sha256'])
            snapshot=json.loads(raw)
            if snapshot['url']!=url or snapshot['checked_at']!=check['checked_at'] or snapshot['http_status']!=200:
                raise ValueError('Source snapshot metadata mismatch or unsuccessful fetch')
            if not isinstance(snapshot.get('content'),str) or not snapshot['content'].strip():raise ValueError('Empty saved source content')
            if not isinstance(check.get('verified_scope'),str) or not check['verified_scope'].strip():raise ValueError('Missing verified scope')
        if len(actual)!=len(set(actual)) or set(actual)!=expected:raise ValueError('Saved checks must cover each source URL exactly once')
    except (OSError,ValueError,TypeError,KeyError,AttributeError) as exc:errors.append('source_evidence: '+str(exc))
    return errors
