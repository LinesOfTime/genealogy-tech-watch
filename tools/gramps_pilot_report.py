#!/usr/bin/env python3
"""Validate externally captured observations. This tool does not execute Gramps MCP."""
import argparse
import hashlib
import json
from pathlib import Path

IDS={f"T{i}" for i in range(1,8)}
FIELDS={"project","project_version","project_commit","gramps_web_version","api_version",
        "environment","fixture_sha256","before_sha256","after_sha256","executed_at_utc","cases"}

def check(data,root):
    missing=FIELDS-set(data)
    if missing: raise ValueError("Missing fields: "+", ".join(sorted(missing)))
    if data["project"]!="genealogy-mcp/gramps-mcp": raise ValueError("Wrong project")
    cases=data["cases"]
    if len(cases)!=7 or {x.get("id") for x in cases}!=IDS: raise ValueError("Expected exactly T1..T7")
    for key in ("fixture_sha256","before_sha256","after_sha256"):
        val=data[key]
        if not isinstance(val,str) or len(val)!=64 or any(c not in "0123456789abcdef" for c in val):
            raise ValueError("Invalid "+key)
    root=root.resolve()
    evidence=[]
    for case in cases:
        for key in ("observed","expected","notes","evidence_file"):
            if not case.get(key): raise ValueError("Missing "+key+" in "+case["id"])
        if type(case.get("passed")) is not bool: raise ValueError("Non-boolean passed")
        rel=Path(case["evidence_file"])
        if rel.is_absolute() or ".." in rel.parts: raise ValueError("Unsafe evidence path")
        target=(root/rel).resolve()
        if not target.is_relative_to(root) or not target.is_file(): raise ValueError("Evidence missing: "+str(rel))
        evidence.append({"test":case["id"],"passed":case["passed"],
                         "evidence":str(rel),"sha256":hashlib.sha256(target.read_bytes()).hexdigest()})
    all_pass=all(x["passed"] for x in evidence)
    unchanged=data["before_sha256"]==data["after_sha256"]
    return {"project":data["project"],"version":data["project_version"],
            "commit":data["project_commit"],"executed_at_utc":data["executed_at_utc"],
            "result":"pass_reported" if all_pass and unchanged else "failed_or_changed",
            "passed":sum(x["passed"] for x in evidence),"total":7,
            "unchanged_export":unchanged,"evidence":evidence,
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
    return 0 if report["result"]=="pass_reported" else 2

if __name__=="__main__":
    raise SystemExit(main())
