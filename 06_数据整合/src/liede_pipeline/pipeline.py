from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from .analysis import build_analysis
from .common import Context, digest, write_csv, write_json
from .entities import build_entities
from .imports import FACT_FIELDS, integrate_feeds
from .policies import build_policies
from .sources import Sources
from .transport import build_transport
from .validation import check_protected, input_checks, validate

EMPTY_COLUMNS = {
    "import_quarantine":["id","fact_id","input_file","input_row","reason","original_record"],
    "verified_facts":["id",*FACT_FIELDS,"input_file","input_sha256","input_row","resolved_source_id","integration_status","local_verification","duplicate_copies_ignored"],
    "admission_evidence":["id","subject_id","subject_type","stage","reference_period","claim","source_id","source_locator","verification_status","note"],
}


def assemble(root: Path,module: Path,inbox: Path | None=None) -> Context:
    checks = input_checks(root,module)+[check_protected(root,module)]
    if any(not c["passed"] for c in checks):
        raise RuntimeError("Input/protected file changed: "+str([r["id"] for r in checks if not r["passed"]]))
    ctx = Context(root,module)
    sources = Sources(ctx)
    archived = sources.verify_archives()
    if any(not c["passed"] for c in archived):
        raise RuntimeError("Registered original archive hash mismatch")
    build_entities(ctx)
    build_policies(ctx)
    build_transport(ctx)
    integrate_feeds(ctx,inbox or module/"inbox")
    build_analysis(ctx)
    ctx.tables["research_gaps"] = sorted(ctx.gaps,key=lambda r:(r["priority"],r["id"]))
    sources.export()
    for name in EMPTY_COLUMNS:
        ctx.table(name)
    return ctx


def version_hash(root,module,inbox):
    paths = [(root/name) for name in json.loads((module/"config/input_manifest.json").read_text())]
    paths += list((module/"config").glob("*"))+list((module/"src").rglob("*.py"))+list(inbox.glob("*.csv"))
    items = [(str(p.relative_to(root)) if p.is_relative_to(root) else p.name,digest(p)) for p in paths if p.is_file()]
    return hashlib.sha256(json.dumps(sorted(set(items)),ensure_ascii=False).encode()).hexdigest()


def write_package(ctx, destination, version,report):
    schemas = {}
    for name,rows in sorted(ctx.tables.items()):
        fields = list(dict.fromkeys(key for row in rows for key in row)) or EMPTY_COLUMNS.get(name,["id"])
        schemas[name] = dict(primary_key="id",row_count=len(rows),fields=[dict(name=field,
            value_types=sorted({type(r[field]).__name__ for r in rows if r.get(field) is not None}),
            nullable=any(r.get(field) is None or r.get(field)=="" for r in rows)) for field in fields])
        write_csv(destination/"data"/(name+".csv"),sorted(rows,key=lambda r:r["id"]),fields)
    write_json(destination/"schemas.json",schemas)
    write_json(destination/"quality_report.json",report)
    write_json(destination/"run_manifest.json",dict(pipeline_version="1.0.0",research_year=2026,
        data_version=version,row_counts={k:len(v) for k,v in sorted(ctx.tables.items())},
        data_scope=["primary","kindergarten"],inputs=json.loads((ctx.module/"config/input_manifest.json").read_text()),
        generated_files_semantics="Deterministic snapshots; no current-time value is substituted for historical dates"))
    evidence = ctx.tables["evidence_matrix"]
    lines = ["# Table C - Cross-domain evidence matrix","",f"Data version: `{version}`.","",
        "Each data reference uses `table:id` and resolves to a row in `data/<table>.csv`.",""]
    for r in evidence:
        lines += [f"## {r['id']} - {r['finding']}","",
            "- Evidence kind: "+r["evidence_kind"],
            "- Supporting data: "+", ".join("`"+ref+"`" for ref in r["supporting_data"]),
            "- Sources: "+", ".join("`"+s+"`" for s in r["source_ids"]),
            "- Interpretation boundary: "+r["interpretation_boundary"],
            "- Limitation: "+r["limitation"],""]
    (destination/"table_C_evidence_matrix.md").write_text("\n".join(lines)+"\n")


def build(root,module,output=None,inbox=None,figures=False):
    root,module = root.resolve(),module.resolve()
    output = (output or module/"outputs").resolve()
    inbox = (inbox or module/"inbox").resolve()
    if output.is_relative_to(root) and not output.is_relative_to(module):
        raise ValueError("Output cannot target an existing research/teammate directory")
    if output.exists() and any(output.iterdir()) and not (output/"run_manifest.json").is_file():
        raise ValueError("Refusing to replace a directory without a pipeline run manifest")
    ctx = assemble(root,module,inbox)
    report = validate(ctx)
    if not report["passed"]:
        raise RuntimeError("Validation failed: "+str([r for r in report["checks"] if not r["passed"]]))
    version = version_hash(root,module,inbox)
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".staging-",dir=output.parent) as directory:
        stage = Path(directory)
        write_package(ctx,stage,version,report)
        if figures:
            from .figures import render_figures
            render_figures(ctx,stage,version)
        # Staging is validated before the module-owned prior snapshot is replaced.
        if output.exists():
            shutil.rmtree(output)
        shutil.copytree(stage,output)
    return ctx,report,version
