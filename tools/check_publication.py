"""Check the exact staged publication tree without publishing it."""
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TOKEN_PATTERNS = [rb'gh[pousr]_[A-Za-z0-9]{30,}', rb'github_pat_[A-Za-z0-9_]{40,}',
                  rb'sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{40,}',
                  rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']


def scan_blob(name, data):
    findings=[]
    if name.lower().startswith('.github/workflows/'):
        findings.append('GitHub Actions workflow')
    if len(data)>5*1024*1024:
        findings.append('File larger than 5 MiB')
    if b'\0' in data:
        findings.append('Binary content')
    if any(re.search(pattern,data) for pattern in TOKEN_PATTERNS):
        findings.append('Possible credential/private key (value redacted)')
    return findings


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT)


def main():
    manifest=json.loads((ROOT/'data/publication-files.json').read_text(encoding='utf-8'))
    expected=set(manifest)
    if len(expected)!=len(manifest):
        raise ValueError('Duplicate manifest entry')
    for name in manifest:
        p=PurePosixPath(name)
        if p.is_absolute() or '..' in p.parts or '\\' in name:
            raise ValueError('Unsafe manifest path')
    staged={n for n in git('diff','--cached','--name-only','-z').decode('utf-8').split('\0') if n}
    if staged!=expected:
        print(json.dumps(dict(error='Staged files differ from reviewed manifest',
                              missing=sorted(expected-staged),unexpected=sorted(staged-expected)),indent=2))
        return 1
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)
    tree={}
    for name in git('ls-files','-z').decode('utf-8').split('\0'):
        if name:
            tree[name]=git('show',':'+name)
    findings={name:result for name,data in tree.items() if (result:=scan_blob(name,data))}
    if findings:
        print(json.dumps(dict(error='Publication file checks failed',findings=findings),indent=2))
        return 1
    # Run the staged code/data, not the working-copy version.
    with tempfile.TemporaryDirectory(prefix='.watch-release-',dir=ROOT) as temporary:
        snapshot=Path(temporary)
        for name,data in tree.items():
            p=snapshot/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(data)
        checks=[[sys.executable,'tools/watch_pipeline.py','validate','--json'],
                [sys.executable,'-m','unittest','discover','-s','tests','-v'],
                ['node','tests/ui_smoke.cjs']]
        outputs=[]
        for command in checks:
            environment={**os.environ,'PYTHONIOENCODING':'utf-8','PYTHONUTF8':'1'}
            result=subprocess.run(command,cwd=snapshot,capture_output=True,text=True,encoding='utf-8',env=environment)
            if result.returncode:
                print(result.stdout); print(result.stderr); return result.returncode
            outputs.append(result.stdout)
        validation=json.loads(outputs[0])
    print(json.dumps(dict(staged_files=len(staged),tree_files=len(tree),
                          largest_file_bytes=max(map(len,tree.values())),
                          credential_pattern_matches=0,actions=0,binary_files=0,
                          validation_errors=validation['errors'],validation_warnings=validation['warnings'],
                          unit_tests='passed',ui_smoke=outputs[2].strip(),
                          limitation='Known credential patterns only; not an exhaustive secrets audit'),indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
