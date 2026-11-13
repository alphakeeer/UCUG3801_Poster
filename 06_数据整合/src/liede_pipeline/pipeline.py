from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from collections import Counter
from pathlib import Path

from .analysis import build_analysis
from .common import Context, digest, write_csv, write_json
from .entities import build_entities
from .imports import FACT_FIELDS, integrate_feeds
from .policies import build_policies
from .sources import Sources
from .transport import build_transport
from .validation import check_protected, input_checks, validate
from .work_evidence import prepare_work, integrate_work
from .finalization import finalize_semantics

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
    prepare_work(ctx)
    archived = sources.verify_archives()
    if any(not c["passed"] for c in archived):
        raise RuntimeError("Registered original archive hash mismatch")
    build_entities(ctx)
    build_policies(ctx)
    build_transport(ctx)
    integrate_work(ctx)
    integrate_feeds(ctx,inbox or module/"inbox")
    finalize_semantics(ctx)
    build_analysis(ctx)
    ctx.tables["research_gaps"] = sorted(ctx.gaps,key=lambda r:(r["priority"],r["id"]))
    sources.export()
    for name in EMPTY_COLUMNS:
        ctx.table(name)
    return ctx


def version_hash(root,module,inbox):
    paths = [(root/name) for name in json.loads((module/"config/input_manifest.json").read_text())]
    paths += list((module/"config").glob("*"))+list((module/"src").rglob("*.py"))+list(inbox.glob("*.csv"))+[module/"run.py",module/"requirements.txt"]
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
    write_json(destination/"run_manifest.json",dict(pipeline_version="1.2.0",research_year=2026,
        data_version=version,row_counts={k:len(v) for k,v in sorted(ctx.tables.items())},
        data_scope=["primary","kindergarten"],inputs=json.loads((ctx.module/"config/input_manifest.json").read_text()),
        generated_files_semantics="确定性快照；不以运行日期替换历史证据日期"))
    evidence = ctx.tables["evidence_matrix"]
    lines = ["# 表 C：跨领域证据矩阵","",f"数据版本： `{version}`.","",
        "数据引用使用 `table:id`，可定位到 `data/<table>.csv` 的对应行；来源ID见 `data/source_registry.csv`。",""]
    for r in evidence:
        lines += [f"## {r['id']} - {r['finding']}","",
            "- 证据类型："+{"record_coverage":"记录覆盖","archived_quotations":"存档报价","derived_case_comparison":"案例派生比较","policy_extract":"政策摘录","collection_status_and_policy":"采集状态与政策","constructed_sensitivity":"构造情境敏感性","aggregation_boundary":"聚合口径","quality_control":"质量控制","supplement_provenance":"补证溯源","individual_listings":"个案挂牌","targeted_route_extension":"定向补查路线","policy_conditions":"制度条件"}.get(r["evidence_kind"],r["evidence_kind"]),
            "- 支持数据："+", ".join("`"+ref+"`" for ref in r["supporting_data"]),
            "- 来源ID："+", ".join("`"+s+"`" for s in r["source_ids"]),
            "- 解释边界："+r["interpretation_boundary"],
            "- 局限："+r["limitation"],""]
    (destination/"table_C_evidence_matrix.md").write_text("\n".join(lines).rstrip()+"\n")
    _handoff(ctx,destination,version,report)


def _handoff(ctx,destination,version,report):
    from .handoff import write_handoff
    write_handoff(ctx,destination,version,report)
    t = ctx.tables
    lines = ["# 2026-11-13 GPT Work补证整合报告","",f"数据版本：`{version}`。","",
        "远端提交 `a3dc7c6` 的8份材料已保留原路径。下列45条记录由显式适配器接入；原CSV没有改写为通用接口的 verified 状态。报告中的“官方确认”等为GPT Work的原核验标签，本流水线未重复外部研究。","",
        "关键变化及下一步见[研究交接](HANDOFF.md)；完整来源及文件哈希见[来源登记](data/source_registry.csv)。","",
        "|原记录|对象与字段|适用时期|原核验标签|采用方式及限制|","|---|---|---|---|---|"]
    for r in t['work_evidence']:
        values=[r['original_evidence_id'],r['object_name']+'：'+r['fact_field'],r['applicable_year_or_period'],r['verification_status'],r['integration_action']+'；'+r['notes']]
        lines.append('|'+ '|'.join(v.replace('|','；').replace('\n',' ') for v in values)+'|')
    lines += ["","## 仍需补证","","核心园区2026配套楼栋和实际小班收费未取得；K7实际门点与异常路线未修复；D3同口径价格和真实合同缺失。历史材料、预算、政策推定和平台索引均不填入当期实际值。","",
        "## 原件与可复现性","","所有8份输入均登记SHA-256。45条原记录保留原行号、网址、定位、核验日期、对象对应和采用方式。新住房观察、路线和细分规则携带 `work_evidence_id`；通用导入保持原校验机制。","",
        "`config/upstream_sync_2026-11-13.json`记录合并提交及保护基线的授权更新。除索引增加远端入口外，原有未提交文件字节未变。",""]
    (destination/"补证整合报告.md").write_text("\n".join(lines))


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
        manifest_path = stage/"run_manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["artifact_sha256"] = {str(p.relative_to(stage)):digest(p) for p in sorted(stage.rglob("*")) if p.is_file() and p!=manifest_path}
        write_json(manifest_path,manifest)
        # Staging is validated before the module-owned prior snapshot is replaced.
        if output.exists():
            shutil.rmtree(output)
        shutil.copytree(stage,output)
    return ctx,report,version


def validate_package(output: Path) -> list[dict]:
    manifest = json.loads((output/"run_manifest.json").read_text())
    return [dict(id="output:"+name,passed=(output/name).is_file() and digest(output/name)==expected,
                 detail=name) for name,expected in manifest["artifact_sha256"].items()]
