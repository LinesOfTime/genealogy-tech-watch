"""Offline rejection gate backed by explicit GitHub existence-check evidence."""
from datetime import datetime,timezone,timedelta
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit,unquote
import re


def repository_url(value):
    if not isinstance(value,str):return None
    try:p=urlsplit(value.strip())
    except ValueError:return None
    if p.hostname not in ('github.com','www.github.com'):return None
    parts=[unquote(x) for x in p.path.split('/') if x]
    if len(parts)<2:return None
    owner,repo=parts[:2];repo=re.sub(r'\.git$','',repo,flags=re.I)
    return ('https://github.com/'+owner+'/'+repo).lower()


def read_journal(root):
    p=Path(root)/'data/editorial-corrections.json'
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else []


def verified_recheck(root,rejection,check):
    try:
        if check.get('url')!=rejection['url'] or check.get('http_status')!=200:return False
        checked=datetime.fromisoformat(check['checked_at'].replace('Z','+00:00'))
        rejected=datetime.fromisoformat(rejection['checked_at'].replace('Z','+00:00'))
        if checked<=rejected:return False
        if checked.tzinfo is None or rejected.tzinfo is None or checked>datetime.now(timezone.utc)+timedelta(minutes=5):return False
        path=(Path(root)/check['evidence_file']).resolve()
        if not path.is_relative_to(Path(root).resolve()):return False
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=check['sha256']:return False
        evidence=json.loads(raw)
        body=evidence['response']
        return (evidence['http_status']==200 and evidence['checked_at']==check['checked_at']
                and evidence['request_url']=='https://api.github.com/repos/'+rejection['url'].split('github.com/')[1]
                and isinstance(body.get('id'),int) and body['id']>0
                and 'https://github.com/'+body['full_name'].lower()==rejection['url'])
    except (KeyError,TypeError,ValueError,OSError,AttributeError):return False


def rejection_issues(root,catalog,research,digest):
    issues=[]
    try:
        from history_integrity import history_errors,git_baseline
        for message in history_errors(root,git_baseline(root)):
            issues.append(dict(level='error',code='protected_history',location='data',message=message))
        journal=read_journal(root)
        checks_path=Path(root)/'data/repository-rechecks.json'
        checks=json.loads(checks_path.read_text(encoding='utf-8')) if checks_path.exists() else []
        if not isinstance(journal,list) or not isinstance(checks,list):raise ValueError('Expected arrays')
        rejected={}
        for entry in journal:
            if entry.get('reason')=='invalid_repository_reference':
                url=repository_url(entry['url'])
                if url!=entry['url']:raise ValueError('Noncanonical rejection URL')
                if url not in rejected or entry['checked_at']>rejected[url]['checked_at']:rejected[url]=entry
        blocked={url:r for url,r in rejected.items() if not any(verified_recheck(root,r,c) for c in checks)}
        def inspect(value,location):
            if isinstance(value,dict):
                for k,v in value.items():
                    if location=='research' and repository_url('https://github.com/'+str(k)) in blocked:
                        issues.append(dict(level='error',code='rejected_repository',location=location+'.'+str(k),message='Rejected repository remains in research'))
                    # Prior snapshots are history, never positive evidence of existence.
                    if k not in ('editorial_corrections','description_provenance','editorial_service_notes'):
                        inspect(v,location+'.'+k)
            elif isinstance(value,list):
                for i,v in enumerate(value):inspect(v,location+f'[{i}]')
            elif isinstance(value,str):
                urls=[repository_url(x) for x in re.findall(r'https?://[^\s<>"\x27]+',value,re.I)]
                named=repository_url('https://github.com/'+value) if re.fullmatch(r'[^/\s]+/[^/\s]+',value) else None
                if any(u in blocked for u in urls+[named] if u):
                    issues.append(dict(level='error',code='rejected_repository',location=location,
                        message='Previously rejected repository requires a newer successful GitHub API existence check'))
        inspect(catalog,'catalog');inspect(research,'research');inspect(digest,'digest')
    except (OSError,ValueError,TypeError,KeyError,AttributeError) as exc:
        issues.append(dict(level='error',code='rejection_registry',location='data/editorial-corrections.json',message=str(exc)))
    return issues
