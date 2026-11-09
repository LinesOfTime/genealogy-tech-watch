"""Report the current classification and assessment currency without assigning scores."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

from catalog_model import TYPES, DOMAINS, CURRENCY, enrich, practical_value

ROOT=Path(__file__).resolve().parents[1]


def build(root):
    catalog=json.loads((root/'catalog.json').read_text(encoding='utf-8'))
    research=json.loads((root/'docs/research.json').read_text(encoding='utf-8'))
    expected=enrich(root,catalog,research)
    if expected!=catalog:
        raise ValueError('Refresh the existing Watch pipeline before reporting')
    sections=defaultdict(list)
    for c in catalog:
        sections[c['section']].append(c)
    return dict(
        catalog_count=len(catalog),research_count=len(research),
        types={label:sum(c['classification']['primary_type']==key for c in catalog) for key,label in TYPES.items()},
        domains={label:sum(key in c['classification']['domains'] for c in catalog) for key,label in DOMAINS.items()},
        origins=dict(Counter(c['classification']['origin_label'] for c in catalog)),
        editorial_priorities=dict(Counter(c.get('priority','Не оценён') for c in catalog)),
        practical_priorities=dict(Counter(practical_value(c) for c in catalog)),
        currency={label:sum(c['assessment_currency']['status']==key for c in catalog) for key,label in CURRENCY.items()},
        sections={section:dict(count=len(cards),
            types=dict(Counter(c['classification']['type_label'] for c in cards)),
            domains=dict(Counter(tag for c in cards for tag in c['classification']['domain_labels'])))
            for section,cards in sorted(sections.items())},
        projects=[dict(project=c['name'],url=c['url'],section=c['section'],
            primary_type=c['classification']['primary_type'],domains=c['classification']['domains'],
            origin=c['classification']['origin'],classification_reason=c['classification']['reason'],
            currency_status=c['assessment_currency']['status'],
            currency_reason=c['assessment_currency']['reason'],
            assessment_approved_at=c['assessment_currency']['assessment_approved_at'],
            last_substantive_source_check=c['assessment_currency']['last_substantive_source_check'],
            editorial_priority=c.get('priority'),practical_priority=practical_value(c)) for c in catalog])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    payload=json.dumps(build(ROOT),ensure_ascii=False,indent=2)+'\n'
    if args.output:
        args.output.write_text(payload,encoding='utf-8')
    else:
        print(payload,end='')


if __name__=='__main__':
    main()
