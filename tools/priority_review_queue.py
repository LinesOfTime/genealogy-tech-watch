#!/usr/bin/env python3
"""Produce a reproducible, non-mutating priority reassessment queue."""
import argparse
from datetime import date
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALID = {'P1', 'P2', 'P3', 'Не оценён'}

def queue(cards, as_of, max_age=90):
    result = []
    for card in cards:
        practical = card.get('practical_priority')
        priority = (practical.get('priority', 'Не оценён') if isinstance(practical, dict)
                    else practical if isinstance(practical, str)
                    else card.get('priority', 'Не оценён'))
        history = card.get('practical_priority_history') or []
        latest = history[-1] if isinstance(history, list) and history and isinstance(history[-1], dict) else {}
        stamp = (latest.get('reviewed_at') or
                 (practical.get('reviewed_on') or practical.get('approved_at')
                  if isinstance(practical, dict) else None) or
                 card.get('practical_priority_reviewed_at'))
        age = None
        if isinstance(stamp, str):
            try:
                age = (as_of - date.fromisoformat(stamp[:10])).days
            except ValueError:
                pass
        reasons = []
        if priority not in VALID or priority == 'Не оценён':
            reasons.append('unrated')
        if not stamp:
            reasons.append('no_dated_review')
        elif age is None:
            reasons.append('invalid_review_date')
        elif age >= max_age:
            reasons.append('stale_review')
        if reasons:
            rationale = practical.get('rationale', '') if isinstance(practical, dict) else ''
            if 'unrated' in reasons:
                if not stamp:
                    review_group = 'initial_review'
                elif 'лиценз' in rationale.lower() or 'прав' in rationale.lower():
                    review_group = 'rights_or_license_check'
                else:
                    review_group = 'evidence_or_pilot_check'
            elif 'no_dated_review' in reasons or 'invalid_review_date' in reasons:
                review_group = 'document_review_date'
            else:
                review_group = 'scheduled_reassessment'
            result.append(dict(name=card.get('name'), url=card.get('url'),
                               priority=priority, reviewed_at=stamp,
                               age_days=age, reasons=reasons, review_group=review_group,
                               evidence_level=(practical.get('evidence_level') if isinstance(practical, dict) else None),
                               rationale=rationale,
                               next_action=latest.get('next_action') or (practical.get('pilot') if isinstance(practical, dict) else None) or card.get('practical_priority_next_action')))
    return sorted(result, key=lambda x: (0 if 'unrated' in x['reasons'] else 1,
                                        0 if 'no_dated_review' in x['reasons'] else 1,
                                        -(x['age_days'] or 0), str(x['name'])))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', default=date.today().isoformat())
    parser.add_argument('--max-age', type=int, default=90)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.max_age < 1:
        parser.error('--max-age must be positive')
    day = date.fromisoformat(args.date)
    cards = json.loads((ROOT / 'catalog.json').read_text(encoding='utf-8'))
    entries = queue(cards, day, args.max_age)
    report = dict(as_of=day.isoformat(), max_age_days=args.max_age,
                  catalog_count=len(cards), queue_count=len(entries), items=entries)
    payload = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.write_text(payload, encoding='utf-8')
    else:
        print(payload, end='')

if __name__ == '__main__':
    main()
