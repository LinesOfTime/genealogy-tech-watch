#!/usr/bin/env python3
"""Publish an already-approved Watch plan as a single GitHub pull request.

Requires local git, gh auth, and an explicit, reviewed plan hash.
Does not approve findings, auto-merge, or invoke GitHub Actions.
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WATCH = ROOT / "tools" / "watch.py"
ALLOWED = (
    "catalog.json", "digest.json", "docs/catalog.json", "docs/digest.json",
    "docs/research.json", "docs/index.html", "docs/digest.html",
    "data/applied-events.json", "data/discoveries.jsonl",
)


def command(*args, capture=True):
    p = subprocess.run(args, cwd=ROOT, text=True, capture_output=capture)
    if p.returncode:
        raise RuntimeError(f"{' '.join(args)} failed: {p.stderr or p.stdout}")
    return p.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--expect-plan", required=True)
    parser.add_argument("--execute", action="store_true", help="Explicitly allow commit, push and PR creation")
    args = parser.parse_args()
    try:
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
        # A failed prior run may have committed/pushed successfully but
        # failed to open the PR. Recover that state instead of reapplying.
        try:
            existing_pr = command("gh", "pr", "view", branch, "--json", "url", "--jq", ".url")
        except RuntimeError:
            existing_pr = None
        command(sys.executable, str(WATCH), "publish", "--date", args.date, "--expect-plan", args.expect_plan)
        changed = command("git", "diff", "--name-only").splitlines()
        untracked = command("git", "ls-files", "--others", "--exclude-standard").splitlines()
        unexpected = sorted(set(changed + untracked) - set(ALLOWED))
        if unexpected:
            raise RuntimeError("Unexpected changed paths; inspect manually: " + ", ".join(unexpected))
        selected = [p for p in ALLOWED if p in set(changed + untracked)]
        if not selected:
            if existing_pr:
                print("Existing PR:", existing_pr)
                return 0
            # If a prior run pushed the branch, offer PR recovery without
            # making a new commit or claiming the apply was repeated.
            ahead = command("git", "rev-list", "--count", "origin/main..HEAD")
            if int(ahead) > 0:
                url = command("gh", "pr", "create", "--base", "main", "--head", branch,
                              "--title", "Watch: утверждённые находки " + args.date,
                              "--body", "Повторное создание PR после прерванной публикации; проверить diff.")
                print("Recovered PR:", url)
                return 0
            print("No data changes to publish")
            return 0
        command("git", "diff", "--check")
        command("git", "add", "--", *selected)
        command("git", "diff", "--cached", "--check")
        staged = command("git", "diff", "--cached", "--name-only").splitlines()
        if set(staged) != set(selected):
            raise RuntimeError("Staged paths differ from allowlist; abort before commit")
        command("git", "commit", "-m", "watch: publish approved findings for " + args.date)
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
    except (RuntimeError, OSError) as exc:
        print("ERROR:", exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
