#!/usr/bin/env python3
"""Validate externally captured observations. This tool does not execute Gramps MCP."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

IDS={f"T{i}" for i in range(1,8)}
FIELDS={"project","project_version","project_commit","gramps_web_version","api_version",
        "environment","fixture_file","fixture_sha256","before_file","before_sha256",
        "after_file","after_sha256","executed_at_utc","cases"}

def evidence_path(root, name):
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Missing evidence path")
    rel=Path(name)
    if rel.is_absolute() or ".." in rel.parts or rel == Path("."):
        raise ValueError("Unsafe evidence path")
    target=(root/rel).resolve()
    if not target.is_relative_to(root) or not target.is_file():
        raise ValueError("Evidence missing: "+name)
    return target

def file_sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()

def check(data,root):
    missing=FIELDS-set(data)
    if missing: raise ValueError("Missing fields: "+", ".join(sorted(missing)))
    if data["project"]!="genealogy-mcp/gramps-mcp": raise ValueError("Wrong project")
    for key in ("project_version","project_commit","gramps_web_version","api_version","environment"):
        if not isinstance(data[key],str) or not data[key].strip():
            raise ValueError("Missing metadata: "+key)
    if not isinstance(data["executed_at_utc"],str):
        raise ValueError("Missing timestamp")
    try:
        dt=datetime.fromisoformat(data["executed_at_utc"].replace("Z","+00:00"))
        if dt.tzinfo is None or dt.utcoffset()!=timezone.utc.utcoffset(dt):
            raise ValueError("Timestamp must be UTC")
    except ValueError as exc:
        raise ValueError("Invalid UTC timestamp") from exc
    cases=data["cases"]
    if len(cases)!=7 or {x.get("id") for x in cases}!=IDS: raise ValueError("Expected exactly T1..T7")
    for key in ("fixture_sha256","before_sha256","after_sha256"):
        val=data[key]
        if not isinstance(val,str) or len(val)!=64 or any(c not in "0123456789abcdef" for c in val):
            raise ValueError("Invalid "+key)
    root=root.resolve()
    files={}
    for kind in ("fixture","before","after"):
        path=evidence_path(root,data[kind+"_file"])
        digest=file_sha256(path)
        if digest!=data[kind+"_sha256"]:
            raise ValueError("SHA-256 mismatch for "+kind+"_file")
        files[kind]={"path":data[kind+"_file"],"sha256":digest}
    if len({str((root/x["path"]).resolve()) for x in files.values()})!=3:
        raise ValueError("Fixture, before and after must be distinct files")
    evidence=[]
    for case in cases:
        for key in ("observed","expected","notes","evidence_file"):
            if not case.get(key): raise ValueError("Missing "+key+" in "+case["id"])
        if type(case.get("passed")) is not bool: raise ValueError("Non-boolean passed")
        target=evidence_path(root,case["evidence_file"])
        evidence.append({"test":case["id"],"passed":case["passed"],
                         "evidence":case["evidence_file"],"sha256":file_sha256(target)})
    all_pass=all(x["passed"] for x in evidence)
    unchanged=data["before_sha256"]==data["after_sha256"]
    return {"project":data["project"],"version":data["project_version"],
            "commit":data["project_commit"],"executed_at_utc":data["executed_at_utc"],
            "result":"operator_reported_pass" if all_pass and unchanged else "failed_or_changed",
            "passed":sum(x["passed"] for x in evidence),"total":7,
            "unchanged_export":unchanged,"snapshot_files":files,"evidence":evidence,
            "disclaimer":"Self-reported observations only; no E3/E4 promotion."}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture",type=Path)
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args()
    if args.capture.resolve()==args.output.resolve(): parser.error("Output must differ from input")
    try:
        data=json.loads(args.capture.read_text(encoding="utf-8"))
        report=check(data,args.capture.parent)
    except (ValueError,KeyError,TypeError,OSError) as exc:
        parser.error(str(exc))
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"{report['passed']}/7 observed checks; result={report['result']}")
    return 0 if report["result"]=="operator_reported_pass" else 2

if __name__=="__main__":
    raise SystemExit(main())
