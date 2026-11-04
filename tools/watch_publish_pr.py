#!/usr/bin/env python3
"""Publish an already-approved Watch plan as a single GitHub pull request.

Requires local git, gh auth, and an explicit, reviewed plan hash.
Does not approve findings, auto-merge, or invoke GitHub Actions.
"""
import argparse
import subprocess
import sys
import json
import os
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WATCH = ROOT / "tools" / "watch.py"
ALLOWED = (
    "catalog.json", "digest.json", "docs/catalog.json", "docs/digest.json",
    "docs/research.json", "docs/index.html", "docs/digest.html",
    "data/applied-events.json", "data/discoveries.jsonl",
    "docs/task-matches.json", "docs/usage-context.json", "docs/priority-review.json",
)


def command(*args, capture=True):
    p = subprocess.run(args, cwd=ROOT, text=True, encoding='utf-8',env={**os.environ,'PYTHONUTF8':'1','PYTHONIOENCODING':'utf-8'}, capture_output=capture)
    if p.returncode:
        raise RuntimeError(f"{' '.join(args)} failed: {p.stderr or p.stdout}")
    return p.stdout.strip()


def allowed_paths(edition):
    paths=set(ALLOWED)
    paths.add('docs/WATCH_CANDIDATES_'+edition+'.md')
    journal=ROOT/'data/discoveries.jsonl'
    if journal.exists():
        for line in journal.read_text(encoding='utf-8-sig').splitlines():
            if not line.strip():continue
            row=json.loads(line)
            if row.get('review_status')!='approved':continue
            for check in row.get('source_checks',[]):
                name=check.get('evidence_file','')
                p=Path(name)
                if not name.startswith('data/evidence/') or p.is_absolute() or '..' in p.parts or '\\' in name:
                    raise RuntimeError('Unsafe source evidence path')
                paths.add(name)
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--expect-plan", required=True)
    parser.add_argument("--execute", action="store_true", help="Explicitly allow commit, push and PR creation")
    args = parser.parse_args()
    try:
        date.fromisoformat(args.date)
        branch = command("git", "branch", "--show-current")
        if not branch or branch in ("main", "master"):
            raise RuntimeError("Use a dedicated feature branch, not main")
        if command("git", "status", "--porcelain"):
            raise RuntimeError("Working tree must be clean before publication")
        if not args.execute:
            print("Preview only. Run tools/watch.py prepare --date", args.date)
            print("After review, rerun with --execute and the exact plan hash.")
            return 0
        command("gh", "auth", "status")
        base=command('git','merge-base','origin/main','HEAD')
        allowed=allowed_paths(args.date)
        branch_paths=command('git','diff','--name-only',base,'HEAD').splitlines()
        if set(branch_paths)-allowed:raise RuntimeError('Branch contains unrelated files; inspect before publication')
        # A failed prior run may have committed/pushed successfully but
        # failed to open the PR. Recover that state instead of reapplying.
        try:
            existing = command("gh", "pr", "view", branch, "--json", "url,state")
        except RuntimeError:
            existing_pr = None
        else:
            data=json.loads(existing)
            if data.get('state')!='OPEN':raise RuntimeError('This branch has a closed PR; use a new dedicated branch')
            existing_pr=data['url']
        message=command('git','log','-1','--format=%B')
        recovered=(f'Watch-Plan: {args.expect_plan}' in message.splitlines() and f'Watch-Date: {args.date}' in message.splitlines())
        if recovered:
            command(sys.executable,str(WATCH),'check')
        else:
            command(sys.executable, str(WATCH), "publish", "--date", args.date, "--expect-plan", args.expect_plan)
        changed = command("git", "diff", "--name-only").splitlines()
        untracked = command("git", "ls-files", "--others", "--exclude-standard").splitlines()
        unexpected = sorted(set(changed + untracked) - allowed)
        if unexpected:
            raise RuntimeError("Unexpected changed paths; inspect manually: " + ", ".join(unexpected))
        selected = sorted(set(changed + untracked))
        if not selected:
            # If a prior run pushed the branch, offer PR recovery without
            # making a new commit or claiming the apply was repeated.
            ahead = command("git", "rev-list", "--count", "origin/main..HEAD")
            if recovered and int(ahead) > 0:
                command(sys.executable,'tools/check_publication.py','--base',base)
                command('git','push','-u','origin',branch)
                if existing_pr:
                    print('Existing PR:',existing_pr)
                    return 0
                url = command("gh", "pr", "create", "--base", "main", "--head", branch,
                              "--title", "Watch: утверждённые находки " + args.date,
                              "--body", "Повторное создание PR после прерванной публикации; проверить diff.")
                print("Recovered PR:", url)
                return 0
            if int(ahead)>0:raise RuntimeError('No matching publication receipt; refusing to publish arbitrary existing commits')
            print("No data changes to publish")
            return 0
        command("git", "diff", "--check")
        command("git", "add", "--", *selected)
        command("git", "diff", "--cached", "--check")
        staged = command("git", "diff", "--cached", "--name-only").splitlines()
        if set(staged) != set(selected):
            raise RuntimeError("Staged paths differ from allowlist; abort before commit")
        command(sys.executable,'tools/check_publication.py','--base',base)
        receipt=f'Watch-Plan: {args.expect_plan}\nWatch-Date: {args.date}'
        command("git", "commit", "-m", "watch: publish approved findings for " + args.date+' [skip ci]', '-m',receipt)
        command("git", "push", "-u", "origin", branch)
        title = "Watch: утверждённые находки " + args.date
        body = ("Автоматически подготовленные изменения данных из утверждённых событий. "
                "Проверены штатный validate и unit tests. "
                "Перед merge проверить diff и лицензионные ограничения.")
        if existing_pr:
            url = existing_pr
        else:
            url = command("gh", "pr", "create", "--base", "main", "--head", branch,
                          "--title", title, "--body", body)
        print("PR ready for review:", url)
        print("Site is NOT published until the PR is merged and Pages is verified.")
        return 0
    except (RuntimeError, OSError, ValueError) as exc:
        print("ERROR:", exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
