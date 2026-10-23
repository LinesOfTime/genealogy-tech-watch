"""Reviewed one-repository exclusion and reversible housekeeping migration; dry by default."""
import argparse
import copy
import json
from pathlib import Path
from datetime import datetime,timezone
from apply_changes import encoded,sync_payloads,write_plan,digest_bytes
from build_task_matches import build
from editorial_hygiene import split_service
from repository_integrity import repository_url
from restore_descriptions import restore,markdown

KEY='linesoftime/yarchive-downloader'
URL='https://github.com/'+KEY
MIGRATION='exclude-invalid-and-separate-service-notes-2026-10-23'


def transform(catalog,research,digest,journal,evidence):
    catalog,research,digest,journal=copy.deepcopy((catalog,research,digest,journal))
    if any(x.get('id')==MIGRATION for x in journal):return catalog,research,digest,journal
    if evidence.get('http_status')!=404 or evidence.get('request_url')!='https://api.github.com/repos/'+KEY:
        raise ValueError('Expected explicit GitHub API 404 evidence for exact repository')
    removed=[c for c in catalog if c['name'].lower()==KEY or repository_url(c.get('url'))==URL]
    if len(removed)!=1:raise ValueError('Expected exactly one rejected catalog record')
    catalog=[c for c in catalog if c not in removed]
    archived=research.pop(KEY,None)
    removed_events=[]
    for edition in digest:
        keep=[]
        for event in edition['items']:
            if event.get('repo','').lower()==KEY or repository_url(event.get('link'))==URL:
                removed_events.append(dict(edition_date=edition['date'],event=event))
            else:keep.append(event)
        edition['items']=keep
    digest=[d for d in digest if d['items']]
    journal.append(dict(id='reject-'+KEY+'-2026-10-23',reason='invalid_repository_reference',
        url=URL,project=KEY,checked_at=evidence['checked_at'],github_http_status=404,
        evidence=evidence,archived_catalog=removed[0],archived_research=archived,archived_digest_events=removed_events,
        interpretation='Not publicly found by GitHub API; no replacement URL inferred.'))
    changed=[]
    for origin,entries,fields in [('catalog',[(x['name'].lower(),x) for x in catalog],('description','use_case','limitations')),
                                  ('research',list(research.items()),('editorial_summary','editorial_use_case','editorial_limitations','audit_notes'))]:
        for key,record in entries:
            for field in fields:
                old=record.get(field)
                clean,notes=split_service(old)
                if not notes:continue
                change=dict(project=key,origin=origin,field=field,original_text=old,cleaned_text=clean,notes=notes)
                record.setdefault('editorial_service_notes',[]).append(copy.deepcopy(change))
                record[field]=clean;changed.append(change)
    journal.append(dict(id=MIGRATION,reason='move_editorial_housekeeping',checked_at=evidence['checked_at'],changes=changed))
    return catalog,research,digest,journal


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--write',action='store_true');args=p.parse_args()
    root=Path(__file__).resolve().parents[1];read=lambda n:json.loads((root/n).read_text(encoding='utf-8'))
    checks=read('data/repository-rechecks.json')
    proof=next(x for x in reversed(checks) if x['url']==URL and x['http_status']==404)
    evidence=read(proof['evidence_file'])
    if digest_bytes((root/proof['evidence_file']).read_bytes())!=proof['sha256']:raise ValueError('Evidence hash mismatch')
    journal_path=root/'data/editorial-corrections.json'
    c,r,d,j=transform(read('catalog.json'),read('docs/research.json'),read('digest.json'),
        read('data/editorial-corrections.json') if journal_path.exists() else [],evidence)
    files=sync_payloads(root,catalog=c,digest=d)
    files.update({'docs/research.json':encoded(r),'docs/task-matches.json':encoded(build(c,r)),
        'data/editorial-corrections.json':encoded(j)})
    _,report=restore(c,r)
    files['reports/description-restoration.json']=encoded(report)
    files['reports/description-restoration.md']=markdown(report).encode('utf-8')
    unrated=[dict(project=x['name'],basis=x['russia_applicability']['basis']) for x in c if x['russia_applicability']['rating']=='Не оценено']
    summary=dict(catalog=len(c),research=len(r),digest_events=sum(len(x['items']) for x in d),unrated=unrated,
        excluded=KEY,removal_reason='invalid_repository_reference',http_status=404,
        moved_catalog_cards=len({x['project'] for entry in j if entry.get('id')==MIGRATION for x in entry['changes'] if x['origin']=='catalog'}),
        moved_research_cards=len({x['project'] for entry in j if entry.get('id')==MIGRATION for x in entry['changes'] if x['origin']=='research'}))
    files['reports/editorial-cleanup.json']=encoded(summary)
    before={key:(root/key).read_bytes() if (root/key).exists() else None for key in files}
    files={key:value for key,value in files.items() if value!=before[key]}
    plan=dict(files=files,before=before,plan_hash=digest_bytes(encoded({k:digest_bytes(v) for k,v in files.items()})))
    if args.write:write_plan(root,plan,plan['plan_hash'])
    print(json.dumps(dict(files=list(files),summary=summary),ensure_ascii=True))


if __name__=='__main__':main()
