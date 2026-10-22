"""Add reviewed source-backed editorial summaries, then restore purpose descriptions."""
import argparse
import copy
import json
from pathlib import Path
from apply_changes import encoded,sync_payloads,write_plan,digest_bytes
from build_task_matches import build
from restore_descriptions import restore,markdown


def enrich(catalog,research,fixes):
    catalog,research=copy.deepcopy(catalog),copy.deepcopy(research)
    for fix in fixes:
        key=fix['project'].lower()
        card=next(x for x in catalog if x['name'].lower()==key)
        record=research[key]
        identity='purpose-source-2026-10-22:'+key
        prior=[x for x in record.get('editorial_corrections',[]) if x.get('id')==identity]
        if prior:
            if record.get('editorial_summary')!=fix['summary'] or prior[0]['sources']!=fix['sources']:
                raise ValueError('Conflicting purpose correction: '+key)
            continue
        if 'не установлен' not in card.get('description','').lower():
            raise ValueError('Refusing to replace established purpose: '+key)
        if record.get('editorial_summary','').strip():
            raise ValueError('Refusing to replace existing summary: '+key)
        record.setdefault('editorial_corrections',[]).append(dict(
            id=identity,checked_at='2026-10-22',
            basis='Описание назначения сверено с официальными материалами; приложение не испытывалось.',
            sources=fix['sources'],previous_research={'editorial_summary':record.get('editorial_summary')},
            previous_catalog={'description':card.get('description')}))
        record['editorial_summary']=fix['summary']
    catalog,report=restore(catalog,research)
    return catalog,research,report


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    read=lambda p:json.loads((root/p).read_text(encoding='utf-8'))
    catalog,research,report=enrich(read('catalog.json'),read('docs/research.json'),read('data/purpose-corrections.json'))
    payload=sync_payloads(root,catalog=catalog)
    files={key:payload[key] for key in ('catalog.json','docs/catalog.json','docs/index.html')}
    files.update({'docs/research.json':encoded(research),'docs/task-matches.json':encoded(build(catalog,research)),
        'reports/description-restoration.json':encoded(report),'reports/description-restoration.md':markdown(report).encode('utf-8')})
    before={key:(root/key).read_bytes() for key in files}
    files={key:value for key,value in files.items() if value!=before[key]}
    proposal=dict(files=files,before=before,plan_hash=digest_bytes(encoded({key:digest_bytes(value) for key,value in files.items()})))
    if args.write:write_plan(root,proposal,proposal['plan_hash'])
    print(json.dumps({'changed':list(files),'summary':report['summary']},ensure_ascii=True))


if __name__=='__main__':main()
