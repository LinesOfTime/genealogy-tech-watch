"""Explicit online repository-existence audit; never infer 404 from missing metadata."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import urllib.request
import urllib.error
from repository_integrity import repository_url


def classify(status):
    return 'not_found' if status==404 else 'exists' if status==200 else 'check_inconclusive'


def check(url,api=False):
    request_url='https://api.github.com/repos/'+url.split('github.com/')[1] if api else url
    req=urllib.request.Request(request_url,headers={'User-Agent':'genealogy-tech-watch-editorial-audit','Accept':'application/vnd.github+json' if api else 'text/html'})
    now=datetime.now(timezone.utc).isoformat()
    try:
        with urllib.request.urlopen(req,timeout=20) as response:
            status=response.status;raw=response.read() if api else b'';final=response.url
    except urllib.error.HTTPError as exc:
        status=exc.code;raw=exc.read() if api else b'';final=exc.url
    except (OSError,ValueError) as exc:
        return dict(url=url,request_url=request_url,checked_at=now,http_status=None,result='check_inconclusive',error=str(exc))
    body=json.loads(raw) if api and raw else None
    return dict(url=url,request_url=request_url,final_url=final,checked_at=now,http_status=status,
        result=classify(status),response=body)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--url');p.add_argument('--all',action='store_true')
    p.add_argument('--write',action='store_true');args=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    if args.url:
        url=repository_url(args.url)
        if not url:p.error('Expected GitHub repository URL')
        result=check(url,api=True)
        if args.write:
            raw=(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode()
            name='data/evidence/repository-'+url.split('github.com/')[1].replace('/','-')+'-'+result['checked_at'].replace(':','').replace('+','_')+'.json'
            (root/name).write_bytes(raw)
            path=root/'data/repository-rechecks.json'
            checks=json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
            checks.append({k:result[k] for k in ('url','checked_at','http_status')}|dict(evidence_file=name,sha256=hashlib.sha256(raw).hexdigest()))
            path.write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(result,ensure_ascii=True));return
    if not args.all:p.error('Use --url or --all')
    catalog=json.loads((root/'catalog.json').read_text(encoding='utf-8'))
    urls=sorted({repository_url(x['url']) for x in catalog}-{None})
    rows=list(ThreadPoolExecutor(max_workers=6).map(check,urls))
    report=dict(method='Public GitHub HTTP existence audit; 404 means not publicly found, not proof of deletion. 403/429/network errors remain inconclusive.',
        catalog_records=len(catalog),github_urls_checked=len(rows),
        non_github=[dict(project=c['name'],url=c['url'],result='not_a_github_repository_url') for c in catalog if not repository_url(c['url'])],records=rows)
    if args.write:(root/'reports/repository-existence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({status:sum(r['result']==status for r in rows) for status in ('exists','not_found','check_inconclusive')}))


if __name__=='__main__':main()
