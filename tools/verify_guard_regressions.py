"""Reproduce three correctness bypasses in a trusted old commit, in temporary fixtures."""
import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from test_apply_changes import ApplyTests
from discoveries import compare,content_hash
from event_integrity import event_issues
from repository_integrity import rejection_issues


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',required=True);p.add_argument('--write',action='store_true');args=p.parse_args()
    sha=subprocess.check_output(['git','rev-parse','--verify',args.base+'^{commit}'],cwd=ROOT).decode().strip()
    def previous(name):
        source=subprocess.check_output(['git','show',sha+':tools/'+name+'.py'],cwd=ROOT)
        namespace={'__name__':'trusted_regression_baseline'}
        exec(compile(source,sha+':'+name,'exec'),namespace)
        return namespace
    old_discoveries=previous('discoveries');old_events=previous('event_integrity');old_repositories=previous('repository_integrity')
    f=ApplyTests('test_apply_preserves_fields_and_is_idempotent');f.setUp()
    try:
        record=copy.deepcopy(f.record);record.pop('source_checks');record['reviewed_content_hash']=content_hash(record)
        cases=[dict(case='approved_URL_without_saved_content',
            baseline_allowed=old_discoveries['compare'](f.root,[record])['eligible']==1,
            now_blocked=compare(f.root,[record])['eligible']==0)]
        f.write('data/applied-events.json',{'lost':'hash'})
        cases.append(dict(case='all_event_projections_removed_but_ledger_remains',
            baseline_allowed=not old_events['event_issues'](f.root,[],{},[]),now_blocked=bool(event_issues(f.root,[],{},[]))))
        rejection=dict(reason='invalid_repository_reference',url='https://github.com/a/repo',checked_at='2026-10-22T00:00:00Z')
        baseline={'data/editorial-corrections.json':json.dumps([rejection]).encode()}
        # The live file is absent: the trusted old journal must still constrain publication.
        with patch('history_integrity.git_baseline',return_value=baseline):
            cases.append(dict(case='rejection_journal_deleted_then_repository_returns',
                baseline_allowed=not old_repositories['rejection_issues'](f.root,[dict(url=rejection['url'])],{},[]),
                now_blocked=bool(rejection_issues(f.root,[dict(url=rejection['url'])],{},[]))))
        result=dict(baseline_commit=sha,method='Synthetic fixtures only; no repository research or publication',cases=cases)
        if args.write:(ROOT/'reports/pipeline-guard-regressions.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(result,indent=2))
        return 0 if all(c['baseline_allowed'] and c['now_blocked'] for c in cases) else 1
    finally:f.doCleanups()


if __name__=='__main__':raise SystemExit(main())
