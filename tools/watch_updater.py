"""Review a small GitHub data package using the existing Watch apply plan."""
import argparse
from datetime import date, datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from apply_changes import build_plan, digest_bytes, encoded, write_plan
from discoveries import compare, content_hash, read_jsonl, repo_key
from history_integrity import read_git_objects
from watch_publish_pr import ALLOWED


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_PATH = 'watch-package.json'
MAX_BYTES = 1024 * 1024
REVIEW_FIELDS = {'reviewer', 'reviewed_at', 'reviewed_content_hash'}
EVIDENCE_PATH = re.compile(r'data/evidence/updater/[a-z0-9][a-z0-9-]{0,79}/[a-z0-9][a-z0-9.-]{0,99}\.json')


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key: ' + key)
        result[key] = value
    return result


def invalid_constant(value):
    raise ValueError('Invalid JSON constant: ' + value)


def load_package(raw):
    if not 0 < len(raw) <= MAX_BYTES:
        raise ValueError('Package must be at most 1 MiB')
    package = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_keys, parse_constant=invalid_constant)
    if (not isinstance(package, dict) or set(package) != {'version', 'edition_date', 'events', 'evidence'}
            or type(package['version']) is not int or package['version'] != 1):
        raise ValueError('Expected Updater v1 package')
    day = package['edition_date']
    if not isinstance(day, str) or date.fromisoformat(day).isoformat() != day:
        raise ValueError('Expected edition_date in YYYY-MM-DD format')
    events, evidence = package['events'], package['evidence']
    if not isinstance(events, list) or not 1 <= len(events) <= 5:
        raise ValueError('Package must contain 1–5 events')
    if not isinstance(evidence, dict) or not 1 <= len(evidence) <= 32:
        raise ValueError('Package must contain 1–32 evidence snapshots')
    required_paths = set()
    identities = set()
    for event in events:
        if (not isinstance(event, dict) or event.get('review_status') != 'pending'
                or REVIEW_FIELDS.intersection(event)):
            raise ValueError('Submit only pending events without approval fields')
        if event.get('decision') not in ('publish', 'research_only'):
            raise ValueError('Package events must be intended for publication or research')
        identity = repo_key(event.get('canonical_url'))
        if not identity or identity in identities:
            raise ValueError('Each package must contain distinct repository identities')
        identities.add(identity)
        checks = event.get('source_checks')
        if not isinstance(checks, list) or not checks:
            raise ValueError('Missing source_checks')
        for check in checks:
            path = check.get('evidence_file') if isinstance(check, dict) else None
            if not isinstance(path, str) or not EVIDENCE_PATH.fullmatch(path):
                raise ValueError('Invalid Updater evidence path')
            required_paths.add(path)
    if set(evidence) != required_paths or any(not isinstance(raw, str) for raw in evidence.values()):
        raise ValueError('Evidence must contain exactly the referenced UTF-8 snapshot texts')
    return package


def approved_events(events, reviewer, stamp):
    return [dict(event, review_status='approved', reviewer=reviewer, reviewed_at=stamp,
                 reviewed_content_hash=content_hash(event)) for event in events]


def complete_plan(root, package, records):
    report = compare(root, records)
    failed = [result for record, result in zip(records, report['results'])
              if not result['eligible_for_apply']
              or (record['event_type'] == 'new_project') != (result['novelty_status'] == 'new_project')]
    if failed:
        details = [(result['discovery_id'], result['novelty_status'], result['errors']) for result in failed]
        raise ValueError('Package contains invalid, duplicate or immaterial events: ' + str(details))
    # Every material update to an existing card must explicitly reconsider priority.
    # No score is invented: retaining the current value is a valid documented decision.
    for record, result in zip(records, report['results']):
        if result['novelty_status'] == 'material_update' and result['catalog_match']:
            if 'priority_review' not in record:
                raise ValueError('Existing project update requires priority_review: ' + record['discovery_id'])
    plan = build_plan(root, records, package['edition_date'])
    if plan['events'] != [record['discovery_id'] for record in records]:
        raise ValueError('The plan must apply every package event exactly once')
    if set(plan['files']) - set(ALLOWED):
        raise ValueError('Unexpected files in Watch apply plan')
    return plan


def prepare(root, raw, base):
    """Stage evidence inside a disposable snapshot and build an approval preview."""
    package = load_package(raw)
    existing_ids = {event['discovery_id'] for event in read_jsonl(root / 'data/discoveries.jsonl')}
    for event in package['events']:
        key = event.get('discovery_id')
        if not isinstance(key, str) or key in existing_ids:
            raise ValueError('Missing or already recorded discovery_id: ' + str(key))
    created = []
    try:
        for name, snapshot in package['evidence'].items():
            path = root / name
            if path.exists():
                raise ValueError('Evidence already exists: ' + name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(snapshot.encode('utf-8'))
            created.append(path)
        # Use a reproducible placeholder valid under the evidence rules. A real
        # reviewer and timestamp are recorded only during the publish dispatch.
        timestamps = [check['checked_at'] for event in package['events'] for check in event['source_checks']]
        stamp = max(datetime.fromisoformat(value.replace('Z', '+00:00')) for value in timestamps).isoformat()
        preview = complete_plan(root, package, approved_events(package['events'], 'Updater preview', stamp))
        approval_hash = digest_bytes(encoded({
            'base': base, 'package_sha256': digest_bytes(raw), 'plan_hash': preview['plan_hash'],
        }))
        return package, preview, approval_hash
    except Exception:
        for path in created:
            path.unlink(missing_ok=True)
        raise


def authorize(root, package, approval_hash, expected, actor, stamp):
    if expected != approval_hash:
        raise ValueError('Approval hash differs; review a fresh preview')
    if not re.fullmatch(r'[A-Za-z0-9-]{1,39}', actor or ''):
        raise ValueError('A GitHub reviewer login is required')
    return complete_plan(root, package, approved_events(package['events'], 'GitHub @' + actor, stamp))


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def snapshot_main(base, destination):
    entries = []
    for row in git('ls-tree', '-rz', base).split(b'\0'):
        if not row:
            continue
        metadata, name = row.split(b'\t', 1)
        mode, kind, sha = metadata.decode('ascii').split()
        if kind != 'blob' or mode not in ('100644', '100755'):
            raise ValueError('Updater requires a tree of regular files')
        entries.append((name.decode('utf-8'), sha))
    for name, blob in read_git_objects(ROOT, entries).items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob)


def package_blob(commit):
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('Expected immutable GitHub package commit SHA')
    subprocess.run(['git', 'fetch', '--no-tags', '--depth=1', 'origin', commit], cwd=ROOT, check=True)
    if git('cat-file', '-t', commit).strip() != b'commit':
        raise ValueError('Package SHA must identify a commit')
    entry = git('ls-tree', commit, '--', PACKAGE_PATH)
    if not entry.startswith((b'100644 blob ', b'100755 blob ')):
        raise ValueError('Package must be a regular watch-package.json file')
    spec = commit + ':' + PACKAGE_PATH
    if int(git('cat-file', '-s', spec)) > MAX_BYTES:
        raise ValueError('Package exceeds 1 MiB')
    return git('cat-file', 'blob', spec)


def run(args):
    base = git('rev-parse', 'HEAD').decode('ascii').strip()
    if args.publish and git('status', '--porcelain', '-z'):
        raise ValueError('Publication requires a clean checkout')
    raw = package_blob(args.package_commit)
    with tempfile.TemporaryDirectory(prefix='watch-updater-') as temp:
        scratch = Path(temp)
        snapshot_main(base, scratch)
        package, preview, approval_hash = prepare(scratch, raw, base)
        report = dict(base=base, package_commit=args.package_commit, approval_hash=approval_hash,
                      events=preview['events'], edition_date=package['edition_date'],
                      files=sorted(set(preview['files']) | set(package['evidence'])))
        if not args.publish:
            args.diff.write_text(preview['diff'], encoding='utf-8')
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return
        plan = authorize(scratch, package, approval_hash, args.expect, args.actor,
                         datetime.now(timezone.utc).isoformat())
        files = dict(plan['files'])
        files.update({name: value.encode('utf-8') for name, value in package['evidence'].items()})
        before = {name: plan['before'][name] for name in plan['files']}
        before.update(dict.fromkeys(package['evidence']))
        write_plan(ROOT, dict(files=files, before=before, plan_hash=approval_hash), approval_hash)
        from watch import refresh_and_check
        refresh_and_check()
        changed = set(git('diff', '--name-only', '-z').decode().split('\0'))
        changed.update(git('ls-files', '--others', '--exclude-standard', '-z').decode().split('\0'))
        changed.discard('')
        if not set(files) <= changed <= set(ALLOWED) | set(package['evidence']):
            raise ValueError('Unexpected or missing publication files')
        git('add', '--', *sorted(changed))
        subprocess.run([sys.executable, 'tools/check_publication.py', '--base', base], cwd=ROOT, check=True)
        print(json.dumps(report, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package-commit', required=True)
    parser.add_argument('--diff', type=Path, default=Path('watch-preview.diff'))
    parser.add_argument('--publish', action='store_true')
    parser.add_argument('--expect')
    parser.add_argument('--actor')
    args = parser.parse_args()
    try:
        run(args)
    except (ValueError, OSError, TypeError, KeyError, AttributeError, RuntimeError, subprocess.CalledProcessError) as exc:
        print('Updater:', exc, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
