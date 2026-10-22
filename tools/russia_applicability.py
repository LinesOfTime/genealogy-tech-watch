"""Derive editorial Russia applicability without changing original research text."""
import argparse
from collections import Counter
import copy
import json
from pathlib import Path
import re
from apply_changes import digest_bytes, encoded, sync_payloads, write_plan

RATINGS = {'Высокий', 'Специализированный / зависит от задачи'}


def derive(key, card):
    excerpt = card.get('guide_excerpt', '') if card else ''
    lines = [line for line in excerpt.splitlines() if line.startswith('Для России:')]
    if len(lines) > 1:
        raise ValueError('Multiple Russia ratings: ' + key)
    original = lines[0] if lines else None
    rating = original.split(':', 1)[1].strip() if original else 'Не оценено'
    if original and rating not in RATINGS:
        raise ValueError('Unknown existing Russia rating: ' + key)
    return dict(rating=rating, original_line=original,
                source=dict(file='docs/research.json', key=key, field='guide_excerpt') if original else None,
                basis='Редакционная оценка путеводителя; независимое тестирование не заявлено' if original
                else 'Нет оценки в путеводителе' if card is not None else 'Нет расширенной карточки')


def migrate(catalog, research):
    catalog, research = copy.deepcopy(catalog), copy.deepcopy(research)
    for key, card in research.items():
        value = derive(key, card)
        if 'russia_applicability' in card and card['russia_applicability'] != value:
            raise ValueError('Existing structured assessment differs: ' + key)
        card['russia_applicability'] = value
    for card in catalog:
        key = card['name'].lower()
        value = derive(key, research.get(key))
        if 'russia_applicability' in card and card['russia_applicability'] != value:
            raise ValueError('Existing catalogue assessment differs: ' + key)
        card['russia_applicability'] = value
    return catalog, research


def migration_plan(root):
    root = Path(root)
    catalog, research = migrate(json.loads((root / 'catalog.json').read_text(encoding='utf-8')),
                                json.loads((root / 'docs/research.json').read_text(encoding='utf-8')))
    files = sync_payloads(root, catalog=catalog)
    files['docs/research.json'] = encoded(research)
    before = {n: (root / n).read_bytes() for n in files}
    files = {n: b for n, b in files.items() if b != before[n]}
    manifest = {n: [digest_bytes(before[n]), digest_bytes(b)] for n, b in sorted(files.items())}
    return dict(files=files, before=before, plan_hash=digest_bytes(encoded(manifest))), Counter(
        c['russia_applicability']['rating'] for c in catalog)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--expect-plan')
    args = parser.parse_args()
    plan, counts = migration_plan(args.root)
    if args.write:
        write_plan(args.root, plan, args.expect_plan)
    print(json.dumps(dict(mode='write' if args.write else 'dry-run', ratings=counts,
                          files=list(plan['files']), plan_hash=plan['plan_hash']), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
