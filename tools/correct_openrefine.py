"""Source-backed, narrow editorial correction. Original fields retained in provenance."""
import copy
import argparse
import json
from pathlib import Path
from apply_changes import encoded, sync_payloads, write_plan, digest_bytes
from build_task_matches import build


def correction(catalog,research):
    catalog,research=copy.deepcopy(catalog),copy.deepcopy(research)
    key='openrefine/openrefine'; r=research[key]
    card=next(x for x in catalog if x['name'].lower()==key)
    correction_id='openrefine-purpose-and-limits-2026-10-22'
    if any(x.get('id')==correction_id for x in r.get('editorial_corrections',[])):
        return catalog,research
    description='Очистка и преобразование табличных данных, группировка похожих значений и согласование с внешними базами через reconciliation-сервисы.'
    use_case='Редакционный генеалогический сценарий: подготовить таблицу архивных выписок, убрать лишние пробелы и привести написания к единому виду; просмотреть группы похожих значений и вручную утвердить исправления. При наличии подходящего внешнего сервиса — сопоставить значения со справочником. Сценарий на генеалогических данных независимо не испытывался.'
    limitations='Кластеризация ищет похожие значения и требует подтверждения предлагаемых правок пользователем; это не доказательство тождества людей. Для согласования с внешней базой нужен подходящий reconciliation-сервис. Качество на русских архивных данных и доступность внешних сервисов из РФ отдельно не проверены.'
    evidence=dict(id=correction_id,checked_at='2026-10-22',
      basis='Проверено по официальному описанию и руководству OpenRefine; приложение не запускалось. Генеалогический сценарий — редакционное предложение, не испытанная возможность.',
      sources=[dict(type='README',url='https://openrefine.org/'),dict(type='README',url='https://openrefine.org/docs/manual/cellediting#cluster-and-edit'),dict(type='README',url='https://openrefine.org/docs/manual/reconciling')],
      previous_catalog={k:card.get(k) for k in ('description','use_case','limitations')},
      previous_research={k:r.get(k) for k in ('editorial_summary','editorial_use_case','editorial_limitations','audit_notes')})
    card.update(description=description,use_case=use_case,limitations=limitations)
    card.setdefault('editorial_corrections',[]).append(copy.deepcopy(evidence))
    r.update(editorial_summary=description,editorial_use_case=use_case,editorial_limitations=limitations)
    r.setdefault('editorial_corrections',[]).append(evidence)
    return catalog,research


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    c=json.loads((root/'catalog.json').read_text(encoding='utf-8'))
    r=json.loads((root/'docs/research.json').read_text(encoding='utf-8'))
    c,r=correction(c,r)
    all_files=sync_payloads(root,catalog=c)
    files={k:all_files[k] for k in ('catalog.json','docs/catalog.json','docs/index.html')}
    files['docs/research.json']=encoded(r)
    files['docs/task-matches.json']=encoded(build(c,r))
    before={k:(root/k).read_bytes() for k in files}
    files={k:v for k,v in files.items() if v!=before[k]}
    plan=dict(files=files,before=before,plan_hash=digest_bytes(encoded({k:digest_bytes(v) for k,v in files.items()})))
    if args.write:
        write_plan(root,plan,plan['plan_hash'])
    print('Changed:',list(files))


if __name__=='__main__':main()
