"""Compare protected records and evidence against a trusted Git snapshot."""
import json
from pathlib import Path
import subprocess

LISTS=('data/editorial-corrections.json','data/repository-rechecks.json')


def read_git_objects(root, entries):
    """Read exact blob bytes in one Git process, without archive transformations."""
    ids = list(dict.fromkeys(sha for _, sha in entries))
    if not ids:
        return {}
    raw = subprocess.check_output(['git', 'cat-file', '--batch'], cwd=root,
                                  input=('\n'.join(ids) + '\n').encode('ascii'))
    objects = {}
    offset = 0
    for sha in ids:
        end = raw.index(b'\n', offset)
        header = raw[offset:end].decode('ascii').split()
        if len(header) != 3 or header[:2] != [sha, 'blob']:
            raise ValueError('Expected Git blob: ' + sha)
        size = int(header[2])
        start = end + 1
        if raw[start + size:start + size + 1] != b'\n':
            raise ValueError('Incomplete Git blob: ' + sha)
        objects[sha] = raw[start:start + size]
        offset = start + size + 1
    if offset != len(raw):
        raise ValueError('Unexpected Git batch output')
    return {name: objects[sha] for name, sha in entries}


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
        if name == 'data/practical-priority-application.json':
            try:
                if json.loads((root/name).read_bytes()) != json.loads(raw):
                    errors.append(name+': practical publication approval changed')
            except (OSError, ValueError):
                errors.append(name+': practical publication approval missing or invalid')
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
        listing=subprocess.check_output(['git','ls-tree','-r','-z',ref,'--','data'],cwd=root)
        wanted=set(LISTS)|{'data/applied-events.json','data/discoveries.jsonl','data/practical-priority-application.json'}
        entries=[]
        for item in listing.split(b'\0'):
            if not item:continue
            metadata,name=item.split(b'\t',1)
            mode,kind,sha=metadata.decode('ascii').split()
            name=name.decode('utf-8')
            if kind=='blob' and (name in wanted or name.startswith('data/evidence/')):
                entries.append((name,sha))
        return read_git_objects(root,entries)
    except (OSError,subprocess.CalledProcessError):return {}
