"""Offline, read-only integrity checks. No network or publication operations."""
import argparse
from collections import Counter
from datetime import date
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import urlsplit


def canonical_url(value):
    if not isinstance(value, str):
        return None
    try:
        p = urlsplit(value.strip())
    except ValueError:
        return None
    if p.scheme not in ('http', 'https') or not p.hostname:
        return None
    path = p.path.rstrip('/')
    if p.hostname.lower() in ('github.com', 'www.github.com'):
        path = re.sub(r'\.git$', '', path, flags=re.I).lower()
        return 'https://github.com' + path
    return p.scheme.lower() + '://' + p.netloc.lower() + path


class SeedParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.seeds = []
        self.active = False

    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('id') == 'seed':
            self.seeds.append('')
            self.active = True

    def handle_endtag(self, tag):
        if tag == 'script':
            self.active = False

    def handle_data(self, data):
        if self.active:
            self.seeds[-1] += data


def validate(root, baseline=None):
    root = Path(root)
    issues, loaded = [], {}

    def issue(level, code, location, message):
        issues.append(dict(level=level, code=code, location=location, message=message))

    for name, kind in [('catalog.json', list), ('digest.json', list),
                       ('docs/catalog.json', list), ('docs/digest.json', list),
                       ('docs/research.json', dict)]:
        try:
            value = json.loads((root / name).read_text(encoding='utf-8'))
            if not isinstance(value, kind):
                raise ValueError('Expected ' + kind.__name__)
            loaded[name] = value
        except (OSError, ValueError) as exc:
            issue('error', 'json', name, str(exc))

    for source, page in [('catalog', 'index'), ('digest', 'digest')]:
        data = loaded.get(source + '.json')
        if data is not None and loaded.get('docs/' + source + '.json') != data:
            issue('error', 'copy_mismatch', source, 'Root and published JSON differ')
        try:
            html = (root / 'docs' / (page + '.html')).read_text(encoding='utf-8')
            parser = SeedParser()
            parser.feed(html)
            if len(parser.seeds) != 1:
                raise ValueError('Expected exactly one seed')
            if json.loads(parser.seeds[0]) != data:
                issue('error', 'seed_mismatch', page, 'Embedded data differs from root JSON')
            if re.search(r'localStorage\.getItem\(', html):
                issue('warning', 'cache_override', page, 'Inspect browser cache path: stored data may override publication')
        except (OSError, ValueError) as exc:
            issue('error', 'html_seed', page, str(exc))

    catalog = loaded.get('catalog.json', [])
    research = loaded.get('docs/research.json', {})
    from repository_integrity import rejection_issues
    issues.extend(rejection_issues(root,catalog,research,loaded.get('digest.json',[])))
    # Also reject standalone outbound links outside the JSON seeds.
    for path in (root/'docs').glob('*.html'):
        links=re.findall(r'https?://[^\s<>"\x27]+',path.read_text(encoding='utf-8'),re.I)
        for finding in rejection_issues(root,[dict(url=link) for link in links],{},[]):
            finding['location']=str(path.relative_to(root))+':'+finding['location']
            issues.append(finding)
    existence_path=root/'reports/repository-existence.json'
    if existence_path.exists():
        try:
            from repository_integrity import repository_url
            checked=json.loads(existence_path.read_text(encoding='utf-8'))
            active={repository_url(c.get('url')) for c in catalog if isinstance(c,dict)}
            for entry in checked['records']:
                if entry['url'] in active and entry['result']=='not_found' and entry['http_status']==404:
                    issue('warning','repository_not_found',entry['url'],'Public GitHub HTTP 404; repository-reference review is separate from feature research. Checked '+entry['checked_at'])
        except (OSError,KeyError,TypeError,ValueError) as exc:
            issue('error','repository_audit','reports/repository-existence.json',str(exc))
    from editorial_hygiene import split_service
    for origin,entries,fields in [('catalog',enumerate(catalog),('description','use_case','limitations')),
                                  ('research',research.items(),('editorial_summary','editorial_use_case','editorial_limitations'))]:
        for key,card in entries:
            if not isinstance(card,dict):continue
            for field in fields:
                if split_service(card.get(field))[1]:
                    issue('error','service_note_in_content',f'{origin}.{key}.{field}','Move housekeeping notes into editorial_service_notes')
    urls, names = set(), set()
    for i, card in enumerate(catalog):
        loc = f'catalog[{i}]'
        if not isinstance(card, dict):
            issue('error', 'card_type', loc, 'Expected object')
            continue
        for field in ('name', 'url', 'section', 'description', 'priority'):
            if not isinstance(card.get(field), str) or not card[field].strip():
                issue('error', 'catalog_field', loc + '.' + field, 'Expected nonempty string')
        for field in ('use_case', 'limitations', 'license', 'license_status', 'verification',
                      'verified_at', 'test_status', 'source', 'status', 'origin'):
            if field in card and not isinstance(card[field], str):
                issue('error', 'catalog_field', loc + '.' + field, 'Expected string')
        url = canonical_url(card.get('url'))
        if not url:
            issue('error', 'url', loc, 'Invalid absolute HTTP(S) URL')
        elif url in urls:
            issue('error', 'duplicate_url', loc, url)
        urls.add(url)
        name = card.get('name')
        if isinstance(name, str):
            key = name.lower()
            if key in names:
                issue('error', 'duplicate_name', loc, key)
            names.add(key)
        if card.get('priority') not in ('P1', 'P2', 'P3', 'Не оценён'):
            issue('error', 'priority', loc, 'Unknown priority')
        history = card.get('history', [])
        if not isinstance(history, list) or any(not isinstance(x, dict) for x in history):
            issue('error', 'history', loc, 'Expected array of objects')
        if 'components' in card and (not isinstance(card['components'], list) or
                any(not isinstance(x, str) for x in card['components'])):
            issue('error', 'components', loc, 'Expected string array')

    # Evaluation evidence gates: do not present triage as an independently tested result.
    allowed_evidence = {'E0', 'E1', 'E2', 'E3', 'E4'}
    allowed_status = {'triaged', 'proposed', 'approved'}
    for i, card in enumerate(catalog):
        if not isinstance(card, dict) or 'evaluation' not in card:
            continue
        loc = f'catalog[{i}].evaluation'
        ev = card['evaluation']
        if not isinstance(ev, dict):
            issue('error', 'evaluation_type', loc, 'Expected object')
            continue
        level = ev.get('evidence_level')
        status = ev.get('review_status')
        if level not in allowed_evidence:
            issue('error', 'evaluation_evidence', loc, 'Unknown evidence level')
        if status not in allowed_status:
            issue('error', 'evaluation_status', loc, 'Unknown review status')
        if status == 'triaged' and level != 'E0':
            issue('error', 'evaluation_triadge_evidence', loc, 'Triage without upstream check must be E0')
        for field in ('component_fit', 'russia_fit', 'maturity'):
            val = ev.get(field)
            if val is not None and (type(val) is not int or not 0 <= val <= 4):
                issue('error', 'evaluation_score', loc + '.' + field, 'Expected 0..4 or null')
        effort = ev.get('integration_effort')
        if effort is not None and (type(effort) is not int or not 0 <= effort <= 3):
            issue('error', 'evaluation_score', loc + '.integration_effort', 'Expected 0..3 or null')
        risk = ev.get('license_risk')
        if risk is not None and risk not in ('L0', 'L1', 'L2', 'L3'):
            issue('error', 'evaluation_license', loc, 'Unknown license risk')
        if level in ('E3', 'E4') and not ev.get('test_report_url'):
            issue('error', 'evaluation_test_evidence', loc, 'E3/E4 requires a reproducible test report URL')
        if status == 'triaged' and any(ev.get(f) is not None for f in
                ('component_fit', 'russia_fit', 'maturity', 'integration_effort', 'license_risk')):
            issue('error', 'evaluation_triadge_scores', loc, 'Catalog-only triage must not fabricate numerical ratings')
        if not isinstance(ev.get('source_urls'), list) or not ev['source_urls']:
            issue('warning', 'evaluation_sources', loc, 'Assessment has no source URLs')
        if not isinstance(ev.get('next_action'), str) or not ev['next_action'].strip():
            issue('warning', 'evaluation_action', loc, 'Assessment has no next action')

    russia = Counter()
    # Structured editorial assessments must reproduce the retained source exactly.
    if any(isinstance(c, dict) and 'russia_applicability' in c for c in catalog) or any(
            isinstance(c, dict) and 'russia_applicability' in c for c in research.values()):
        from russia_applicability import derive
        for key, card in research.items():
            if isinstance(card, dict) and 'russia_applicability' in card:
                try:
                    if card['russia_applicability'] != derive(key, card):
                        issue('error', 'russia_source', key, 'Structured assessment differs from guide_excerpt')
                except (TypeError, ValueError, AttributeError) as exc:
                    issue('error', 'russia_source', key, str(exc))
        for i, card in enumerate(catalog):
            if isinstance(card, dict) and 'russia_applicability' in card:
                key = str(card.get('name', '')).lower()
                try:
                    if card['russia_applicability'] != derive(key, research.get(key)):
                        issue('error', 'russia_source', f'catalog[{i}]', 'Structured assessment differs from research source')
                except (TypeError, ValueError, AttributeError) as exc:
                    issue('error', 'russia_source', f'catalog[{i}]', str(exc))
    for key, card in research.items():
        if key != key.lower():
            issue('error', 'research_key', key, 'Research key must be lowercase')
        if not isinstance(card, dict):
            issue('error', 'research_type', key, 'Expected object')
            continue
        excerpt = card.get('guide_excerpt', '')
        if not isinstance(excerpt, str):
            issue('error', 'guide_type', key, 'Expected string')
            excerpt = ''
        match = re.search(r'^Для России:\s*([^\r\n]+)', excerpt, re.M)
        russia[match.group(1).strip() if match else 'Отсутствует'] += 1
        if key not in names:
            issue('warning', 'research_lookup', key, 'project.html looks up research by catalogue name; verify mapping')
        for field, value in card.items():
            if isinstance(value, str) and re.search(r'Часть 51|Не установлен|не установлена', value, re.I):
                issue('warning', 'editorial_review', key + '.' + field, 'Manual contextual review; text retained')

    seen = set()
    for i, day in enumerate(loaded.get('digest.json', [])):
        loc = f'digest[{i}]'
        if not isinstance(day, dict):
            issue('error', 'digest_type', loc, 'Expected object')
            continue
        try:
            date.fromisoformat(day.get('date', ''))
        except (TypeError, ValueError):
            issue('error', 'date', loc, 'Invalid ISO date')
        for field in ('title', 'summary'):
            if not isinstance(day.get(field), str):
                issue('error', 'digest_field', loc + '.' + field, 'Expected string')
        items = day.get('items')
        if not isinstance(items, list):
            issue('error', 'digest_items', loc, 'Expected array')
            continue
        if not items:
            issue('error', 'empty_digest', loc, 'Empty editions must not be published')
        for j, item in enumerate(items):
            at = loc + f'.items[{j}]'
            if not isinstance(item, dict):
                issue('error', 'item_type', at, 'Expected object')
                continue
            for field in ('repo', 'priority', 'change', 'link', 'components', 'action'):
                if not isinstance(item.get(field), str) or not item[field].strip():
                    issue('error', 'item_field', at + '.' + field, 'Expected nonempty string')
            link = canonical_url(item.get('link'))
            if not link:
                issue('error', 'event_url', at, 'Invalid source URL')
            fingerprint = (str(item.get('repo', '')).lower(), str(item.get('change', '')).strip().lower())
            if fingerprint in seen:
                issue('error', 'duplicate_event', at, 'Repeated project and delta')
            seen.add(fingerprint)
            missing = [f for f in ('event_date', 'significance_reason', 'review_status') if not item.get(f)]
            if missing:
                issue('warning', 'legacy_evidence', at, 'Missing metadata: ' + ', '.join(missing))
            if link and not re.search(r'/(commit|pull|releases|blob)/', link):
                issue('warning', 'broad_source', at, 'Source is not a specific commit/PR/release/document')

    if baseline:
        for name in loaded:
            try:
                old = json.loads((Path(baseline) / name).read_text(encoding='utf-8'))
                if old != loaded[name]:
                    issue('error', 'baseline_changed', name, 'Data changed since baseline; manual evidence review required')
            except (OSError, ValueError) as exc:
                issue('error', 'baseline', name, str(exc))
    from event_integrity import event_issues
    issues.extend(event_issues(root, catalog, research, loaded.get('digest.json', [])))
    from restore_descriptions import restore, VERSION
    for card in catalog:
        if isinstance(card, dict) and isinstance(card.get('description_provenance'), dict) and card['description_provenance'].get('migration') == VERSION:
            try:
                restore([card], research)
            except (ValueError, KeyError, TypeError, AttributeError) as exc:
                issue('error', 'description_provenance', str(card.get('name')), str(exc))
    workflows = root / '.github' / 'workflows'
    if workflows.exists() and any(workflows.iterdir()):
        issue('error', 'actions', '.github/workflows', 'GitHub Actions are prohibited')
    return dict(counts=dict(catalog=len(catalog), research=len(research),
                            editions=len(loaded.get('digest.json', []))),
                russia_ratings=dict(russia), issues=issues,
                errors=sum(x['level'] == 'error' for x in issues),
                warnings=sum(x['level'] == 'warning' for x in issues),
                limitations=['Offline structural checks do not verify source claims, browser behavior, '
                             'secrets, license conflicts or historical preservation without --baseline.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['validate', 'scan', 'review', 'apply'])
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--json', action='store_true', help='Print machine-readable report to stdout')
    parser.add_argument('--input', type=Path, help='Local JSONL candidates; default: data/discoveries.jsonl')
    parser.add_argument('--dry-run', action='store_true', help='Explicit read-only mode (also the default)')
    parser.add_argument('--report', action='store_true', help='Print candidate review report')
    parser.add_argument('--approved-only', action='store_true')
    parser.add_argument('--write', action='store_true', help='Write local plan; never push')
    parser.add_argument('--expect-plan')
    parser.add_argument('--edition-date', help='Explicit ISO publication date')
    args = parser.parse_args()
    if args.command == 'apply':
        if not args.approved_only or not args.edition_date:
            parser.error('apply requires --approved-only and --edition-date YYYY-MM-DD')
        if args.write and (args.dry_run or not args.expect_plan):
            parser.error('--write requires --expect-plan and cannot be combined with --dry-run')
        from discoveries import read_jsonl
        from apply_changes import build_plan, write_plan
        try:
            plan = build_plan(args.root, read_jsonl(args.input or args.root / 'data/discoveries.jsonl'), args.edition_date)
            if args.write:
                write_plan(args.root, plan, args.expect_plan)
        except (OSError, ValueError) as exc:
            parser.exit(1, str(exc) + '\n')
        print(json.dumps(dict(mode='local write' if args.write else 'dry-run', events=plan['events'],
                              skipped=plan['skipped'], files=list(plan['files']), plan_hash=plan['plan_hash']),
                         ensure_ascii=False, indent=2))
        if plan['diff']:
            print(plan['diff'])
        return 0
    if args.command in ('scan', 'review'):
        from discoveries import compare, read_jsonl
        try:
            report = compare(args.root, read_jsonl(args.input or args.root / 'data/discoveries.jsonl'))
        except (OSError, ValueError) as exc:
            parser.exit(1, str(exc) + '\n')
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1 if report['errors'] else 0
    report = validate(args.root, args.baseline)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Errors: {report['errors']}; warnings: {report['warnings']}; counts: {report['counts']}")
        for item in report['issues']:
            print('{level}: {code}: {location}: {message}'.format(**item))
        print('Limitations: ' + ' '.join(report['limitations']))
    return 1 if report['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
