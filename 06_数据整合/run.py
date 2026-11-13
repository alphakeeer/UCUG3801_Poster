#!/usr/bin/env python3
"""Offline entrypoint; writes only the independent integration module outputs."""

import argparse
import json
import shutil
import sys
from pathlib import Path

MODULE = Path(__file__).resolve().parent
ROOT = MODULE.parent
sys.path.insert(0,str(MODULE/"src"))

from liede_pipeline.common import digest, write_json
from liede_pipeline.imports import read_feed
from liede_pipeline.pipeline import assemble, build, validate_package, version_hash
from liede_pipeline.validation import protected_snapshot, validate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command",required=True)
    for name in ["build","all"]:
        p = sub.add_parser(name)
        p.add_argument("--output",type=Path)
        p.add_argument("--inbox",type=Path)
    sub.add_parser("validate")
    p = sub.add_parser("import-csv")
    p.add_argument("csv",type=Path)
    sub.add_parser("protect")
    args = parser.parse_args()
    if args.command=="protect":
        target = MODULE/".state/protected_files.json"
        if target.exists():
            raise ValueError("Protected baseline already exists; it will not be overwritten")
        write_json(target,protected_snapshot(ROOT,MODULE))
        print("Saved local-only protection baseline; no existing research file changed")
    elif args.command=="import-csv":
        read_feed(args.csv)
        target = MODULE/"inbox"/("facts-"+digest(args.csv)+".csv")
        if not target.exists():
            shutil.copyfile(args.csv,target)
        print(f"Preserved {target.relative_to(MODULE)}; run all to append accepted facts and quarantine unresolved rows")
    elif args.command=="validate":
        ctx = assemble(ROOT,MODULE)
        report = validate(ctx)
        output = MODULE/"outputs"
        if (output/"run_manifest.json").exists():
            emitted = validate_package(output)
            manifest = json.loads((output/"run_manifest.json").read_text())
            emitted.append(dict(id="output:current_data_version",passed=manifest["data_version"]==version_hash(ROOT,MODULE,MODULE/"inbox"),detail="Rebuild after changing code, mapping or inbox evidence"))
            report["checks"] += emitted
            report["check_count"] = len(report["checks"])
            report["failure_count"] = sum(not r["passed"] for r in report["checks"])
            report["passed"] = report["failure_count"]==0
        print(json.dumps({k:v for k,v in report.items() if k!="checks"},ensure_ascii=False,indent=2))
        if not report["passed"]:
            raise RuntimeError(str([r for r in report["checks"] if not r["passed"]]))
    else:
        ctx,report,version = build(ROOT,MODULE,args.output,args.inbox,args.command=="all")
        print(json.dumps(dict(data_version=version,validation=report["passed"],checks=report["check_count"],
            row_counts={k:len(v) for k,v in sorted(ctx.tables.items())}),ensure_ascii=False,indent=2))


if __name__=="__main__":
    try:
        main()
    except (ValueError,RuntimeError) as error:
        print(str(error),file=sys.stderr)
        raise SystemExit(2)
