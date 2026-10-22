"""Synchronize root JSON, published copies and embedded seeds locally."""
import argparse
from pathlib import Path
from apply_changes import digest_bytes, encoded, sync_payloads, write_plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    files = sync_payloads(args.root)
    before = {name: (args.root / name).read_bytes() if (args.root / name).exists() else None for name in files}
    files = {name: data for name, data in files.items() if before[name] != data}
    plan = dict(files=files, before=before, plan_hash=digest_bytes(encoded(
        {name: digest_bytes(data) for name, data in files.items()})))
    write_plan(args.root, plan, plan['plan_hash'])
    print('Synced: ' + (', '.join(files) if files else 'already consistent'))


if __name__ == '__main__':
    main()
