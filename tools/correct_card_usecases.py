"""Apply a reviewed batch of sourced use-case corrections, preserving all prior fields."""
import argparse
import copy
import json
from pathlib import Path
from apply_changes import encoded,sync_payloads,write_plan,digest_bytes
from build_task_matches import build


def correct(catalog,research,corrections):
    catalog,research=copy.deepcopy(catalog),copy.deepcopy(research)
    for fix in corrections:
        key=fix['project'].lower()
        card=next(x for x in catalog if x['name'].lower()==key)
        r=research[key]
        previous=[x for x in r.get('editorial_corrections',[]) if x.get('id')==fix['id']]
        if previous:
            if (card.get('use_case')!=fix['use_case'] or card.get('limitations')!=fix['limitations'] or
                r.get('editorial_use_case')!=fix['use_case'] or r.get('editorial_limitations')!=fix['limitations']):
                raise ValueError('Existing correction differs: '+key)
            continue
        provenance=dict(id=fix['id'],checked_at='2026-10-22',
            basis=fix['verified_scope']+' Приложение не запускалось; независимое испытание не заявлено.',
            sources=[dict(type='README',url=url) for url in fix['sources']],
            previous_catalog={field:card.get(field) for field in ('use_case','limitations')},
            previous_research={field:r.get(field) for field in ('editorial_use_case','editorial_limitations')})
        card.update(use_case=fix['use_case'],limitations=fix['limitations'])
        r.update(editorial_use_case=fix['use_case'],editorial_limitations=fix['limitations'])
        card.setdefault('editorial_corrections',[]).append(copy.deepcopy(provenance))
        r.setdefault('editorial_corrections',[]).append(provenance)
    return catalog,research


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    catalog,research=correct(json.loads((root/'catalog.json').read_text(encoding='utf-8')),
        json.loads((root/'docs/research.json').read_text(encoding='utf-8')),
        json.loads((root/'data/card-usecase-corrections.json').read_text(encoding='utf-8')))
    payload=sync_payloads(root,catalog=catalog)
    files={key:payload[key] for key in ('catalog.json','docs/catalog.json','docs/index.html')}
    files['docs/research.json']=encoded(research);files['docs/task-matches.json']=encoded(build(catalog,research))
    before={key:(root/key).read_bytes() for key in files}
    files={key:value for key,value in files.items() if value!=before[key]}
    proposal=dict(files=files,before=before,plan_hash=digest_bytes(encoded({key:digest_bytes(value) for key,value in files.items()})))
    if args.write:write_plan(root,proposal,proposal['plan_hash'])
    print('Changed:',list(files))


if __name__=='__main__':main()
