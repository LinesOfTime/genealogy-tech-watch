"""Apply the reviewed practical package after the user's publication instruction."""
import argparse
import copy
import json
from pathlib import Path
from datetime import datetime
from practical_priorities import load_proposals, package_hash, public_assessment
from apply_changes import encoded, digest_bytes, sync_payloads, write_plan


def build_plan(root, approval):
    catalog = json.loads((root / 'catalog.json').read_text(encoding='utf-8'))
    research = json.loads((root / 'docs/research.json').read_text(encoding='utf-8'))
    proposals = load_proposals(root, catalog)
    package = json.loads((root / 'data/practical-priority-proposals.json').read_text(encoding='utf-8'))
    if (approval.get('status') != 'approved' or approval.get('package_hash') != package_hash(package)
            or not approval.get('approved_by') or not approval.get('source_instruction')):
        raise ValueError('Publication needs the user-approved exact package')
    if datetime.fromisoformat(approval['approved_at'].replace('Z', '+00:00')).tzinfo is None:
        raise ValueError('Approval needs timezone')
    receipt = root / 'data/practical-priority-application.json'
    if receipt.exists():
        if json.loads(receipt.read_text(encoding='utf-8')) != approval:
            raise ValueError('Applied approval cannot be replaced')
        return dict(files={}, before={}, plan_hash=None)
    for c in catalog:
        p = proposals.get(c['name'].lower())
        if not p:
            continue
        value = public_assessment(p, approval)
        c['practical_priority'] = value
        if c['name'].lower() in research:
            research[c['name'].lower()]['practical_priority'] = copy.deepcopy(value)
    audit = json.loads((root / 'reports/priority-source-audit-2026-11-04.json').read_text(encoding='utf-8'))
    for c in catalog:
        row = next(r for r in audit if r['name'] == c['name'])
        if row['result'] != 'exists':
            c['repository_reference_issue'] = dict(result=row['result'], checked_on=row['checked_on'],
                                                  url=row['url'])
    files = {'catalog.json': encoded(catalog), 'docs/research.json': encoded(research),
             'data/practical-priority-application.json': encoded(approval)}
    files.update(sync_payloads(root, catalog=catalog))
    before = {name: (root / name).read_bytes() if (root / name).exists() else None for name in files}
    files = {name: raw for name, raw in files.items() if raw != before[name]}
    return dict(files=files, before=before,
                plan_hash=digest_bytes(encoded({k: digest_bytes(v) for k, v in files.items()})))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--approval', type=Path, required=True)
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--expect-plan')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    plan = build_plan(root, json.loads(args.approval.read_text(encoding='utf-8')))
    if args.write and plan['files']:
        if not args.expect_plan:
            parser.error('--write requires --expect-plan')
        write_plan(root, plan, args.expect_plan)
    print(json.dumps(dict(plan_hash=plan['plan_hash'], files=list(plan['files']), write=args.write)))


if __name__ == '__main__':
    main()
