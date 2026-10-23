"""Compare protected records and evidence against a trusted Git snapshot."""
import json
from pathlib import Path
import subprocess

LISTS=('data/editorial-corrections.json','data/repository-rechecks.json')


def history_errors(root,baseline):
    root=Path(root);errors=[]
    for name in LISTS:
        if name not in baseline:continue
        try:
            old=json.loads(baseline[name]);new=json.loads((root/name).read_bytes())
            if not isinstance(new,list) or new[:len(old)]!=old:raise ValueError('Existing journal entries must remain unchanged and ordered')
        except (OSError,ValueError,TypeError) as exc:errors.append(name+': '+str(exc))
    name='data/applied-events.json'
    if name in baseline:
        try:
            old=json.loads(baseline[name]);new=json.loads((root/name).read_bytes())
            if not isinstance(new,dict) or any(new.get(k)!=v for k,v in old.items()):raise ValueError('Applied ledger history changed')
        except (OSError,ValueError,TypeError) as exc:errors.append(name+': '+str(exc))
    name='data/discoveries.jsonl'
    if name in baseline:
        try:
            old=[json.loads(x) for x in baseline[name].decode().splitlines() if x.strip()]
            new=[json.loads(x) for x in (root/name).read_text(encoding='utf-8').splitlines() if x.strip()]
            approved={r['discovery_id']:r for r in old if r.get('review_status')=='approved'}
            for key,value in approved.items():
                if [r for r in new if r.get('discovery_id')==key]!=[value]:raise ValueError('Approved discovery history lost or changed: '+key)
        except (OSError,ValueError,TypeError,KeyError) as exc:errors.append(name+': '+str(exc))
    for name,raw in baseline.items():
        if name.startswith('data/evidence/'):
            try:
                if (root/name).read_bytes()!=raw:errors.append(name+': saved evidence lost or changed')
            except OSError:errors.append(name+': saved evidence missing')
    return errors


def git_baseline(root,ref='HEAD'):
    root=Path(root).resolve()
    try:
        top=subprocess.check_output(['git','rev-parse','--show-toplevel'],cwd=root,stderr=subprocess.DEVNULL).decode().strip()
        if Path(top).resolve()!=root:return {}
        paths=subprocess.check_output(['git','ls-tree','-r','--name-only',ref,'--','data'],cwd=root).decode().splitlines()
        wanted=set(LISTS)|{'data/applied-events.json','data/discoveries.jsonl'}
        return {n:subprocess.check_output(['git','show',ref+':'+n],cwd=root) for n in paths if n in wanted or n.startswith('data/evidence/')}
    except (OSError,subprocess.CalledProcessError):return {}
