#!/usr/bin/env python3
"""One entry point for the existing, approval-gated offline Watch pipeline.

No network calls, Git pushes, approval fabrication or GitHub Actions.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "tools" / "watch_pipeline.py"
JOURNAL = ROOT / "data" / "discoveries.jsonl"


def run(*args, capture=False):
    cmd = [sys.executable, str(PIPELINE), *map(str, args)]
    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=capture, check=False)
    if capture:
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout)
        return result.stdout
    if result.returncode:
        raise RuntimeError("Command failed: " + " ".join(cmd))
    return ""


def ingest(source):
    """Append only unique, valid JSON objects; review remains pending."""
    from tempfile import NamedTemporaryFile
    sys.path.insert(0, str(ROOT / "tools"))
    from discoveries import read_jsonl, compare
    existing = read_jsonl(JOURNAL)
    incoming = read_jsonl(source)
    ids = {e["discovery_id"] for e in existing}
    accepted = []
    for event in incoming:
        if event.get("review_status") != "pending":
            raise ValueError("Incoming events must be pending; never import approvals")
        if event.get("reviewer") or event.get("reviewed_at") or event.get("reviewed_content_hash"):
            raise ValueError("Incoming events must not contain review signatures")
        if event.get("discovery_id") in ids:
            if any(e == event for e in existing):
                continue
            raise ValueError("Conflicting discovery_id: " + str(event.get("discovery_id")))
        ids.add(event["discovery_id"])
        accepted.append(event)
    if not accepted:
        print("No new events")
        return
    # Validate the entire proposed journal before touching the original.
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        staged = Path(tmp) / "discoveries.jsonl"
        staged.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in existing + accepted), encoding="utf-8")
        report = compare(ROOT, read_jsonl(staged))
        if report["errors"]:
            raise ValueError("Review rejected staged journal: " + json.dumps(report, ensure_ascii=False)[:2000])
    with JOURNAL.open("a", encoding="utf-8") as out:
        for event in accepted:
            out.write(json.dumps(event, ensure_ascii=False) + "\n")
    print(f"Appended {len(accepted)} pending events")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="Review current journal")
    add = sub.add_parser("ingest", help="Import pending events from local JSONL")
    add.add_argument("file", type=Path)
    prepare = sub.add_parser("prepare", help="Review and preview approved events; never writes")
    prepare.add_argument("--date", required=True, help="YYYY-MM-DD")
    publish = sub.add_parser("publish", help="Apply previously approved events with explicit plan hash")
    publish.add_argument("--date", required=True)
    publish.add_argument("--expect-plan", required=True)
    args = parser.parse_args()
    try:
        if args.command == "status":
            run("review", "--report")
        elif args.command == "ingest":
            ingest(args.file.resolve())
        elif args.command == "prepare":
            run("review", "--report")
            run("apply", "--approved-only", "--edition-date", args.date, "--dry-run")
        else:
            run("review", "--report")
            run("apply", "--approved-only", "--edition-date", args.date, "--write", "--expect-plan", args.expect_plan)
            run("validate")
            tests = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT)
            if tests.returncode:
                raise RuntimeError("Unit tests failed; inspect local diff before commit")
            print("Local data updated and tests passed. Review diff, commit and merge separately.")
        return 0
    except (ValueError, OSError, RuntimeError) as exc:
        print("ERROR:", exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
