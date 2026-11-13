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
    (destination/"table_C_evidence_matrix.md").write_text("\n".join(lines).rstrip()+"\n")
    _handoff(ctx,destination,version,report)


def _handoff(ctx,destination,version,report):
    t = ctx.tables
    mapped_home = sum(bool(r["preferred_position_id"]) for r in t["residences"])
    mapped_school = sum(bool(r["preferred_position_id"]) for r in t["education_campuses"])
    usable = sum(r["analytical_eligible"] for r in t["transport_routes"])
    linked = [r for r in t["entity_crosswalk"] if r["match_status"]=="unresolved"]
    charges = sum(r["actual_charge"] for r in t["education_fees"])
    facts = len([r for r in t["verified_facts"] if r["local_verification"]=="external_declared_verified"])
    handoff = f"""# Research Evidence Package - 研究交接

数据版本：`{version}`。研究范围仅含幼儿园与小学。本包为独立离线派生结果，没有修改原报告、交互地图或Poster。

## 给理论组与报告组的最短阅读顺序

1. [Table C：八项发现及证据链](table_C_evidence_matrix.md)。每项均包含数据主键、来源、解释边界和局限。
2. [综合图 A](figures/figure_A_housing_education.png)：住房参照位置、平台报价/独立租金例证及园校分布。
3. [综合图 B](figures/figure_B_admission_accessibility.png)：住宅条件背景、申请渠道与潜在步行时间。
4. [图注与数据出处](FIGURE_LEGENDS.md)，插入论文或Poster时须同时保留；SVG/PDF在figures目录。
5. [质量摘要](QUALITY_SUMMARY.md)与[研究缺口](data/research_gaps.csv)，决定哪些内容仍需GPT Work补证。

`build`只生成数据；图件及图注需要运行 `all`。本README中的图件链接以完整 `all`交付为准。

## 当前数据覆盖

| 对象 | 数量与限制 |
|---|---|
| 住宅 | {len(t['residences'])}个；{mapped_home}个有默认地图参照；不是住户样本 |
| 园校 | {len(t['education_campuses'])}条园区/小学校区记录；{mapped_school}条有可采用位置，转换POI仍非已核校门 |
| 路线 | {len(t['transport_routes'])}条保留记录，{usable}条进入综合连接 |
| 住房观察 | {len(t['housing_observations'])}条不同指标/来源记录，不能直接混合统计 |
| 申请渠道比较 | {len(t['accessibility_comparisons'])}条；全部实际录取未观察 |
| 园校当期收费记录 | {charges}条公示/缴费类型记录；政策基准及批复另列 |
| 外部补证 | {facts}条已接受；{len(t['import_quarantine'])}条待核导入行 |

## 可以直接使用的分析出口

- [住宅与园校连接表](data/housing_education_links.csv)：一行一条合格案例路线，带住房指标、规则ID及费用ID；不要展开一对多规则后重复合计。
- [渠道可达性比较](data/accessibility_comparisons.csv)：Figure B的九条比较，保留基准路线、政策来源及未观察结果。
- [住宅](data/residences.csv)、[园校](data/education_campuses.csv)、[来源](data/source_registry.csv)、[实体对应](data/entity_crosswalk.csv)为进一步连接入口。
- 需要逐条费用、计划和住房原值时，读取 `education_fees`、`admission_plans`、`housing_observations`；完整粒度见[数据字典](../DATA_DICTIONARY.md)。

## 必须保留的解释边界

- 冼村小学仅为一个积分计划志愿例，不是实际分配或最近可申请学校。
- 租住与业主的资格、统筹去向、具体配套园名单仍需材料核验。未观察真实家庭、收入、预算或净缴费用。
- 房价不是家庭收入；混合月份的平台参考值不是同质成交价格。猎德花园异常出售与商住产品不混入普通住宅参考价图例。
- 5区位置、住宅交通POI、校园中心和校门角色不同；所有既有路线都未实测园校门。K7保持未确认，相关路线不能用于综合结论。
- 机构计划只计一次，班数、人数与派位组成分列。43条候选和当前有坐标的子集都不代表全猎德完整覆盖。
- 缺失和冲突不填0，不自动选择“最新”或取平均；实际录取与通学始终标为未观察。

## GPT Work下一批证据

优先补：现有住宅/园校准确身份与位置角色、核心园区2026收费、配套住宅名单和具体门牌规则、南国花园住房成本、K7旧名与入口对应。

接口与模板见[Verified Facts导入说明](../IMPORT_VERIFIED_FACTS.md)。使用规范ID，每条事实带来源和定位；未知对象留待核，不自动模糊关联。

## 复现与维护

入口为 `../run.py all`；检查为 `../run.py validate`。原始输入由175个固定哈希及来源原件哈希保护，整合输出另有逐文件哈希。

如其他组员修改了既有材料，应先辨认是否为新的研究版本，再维护输入登记/本机保护基线；不通过reset、stash或覆盖把他们的工作恢复成旧版。

当前未确认实体对应数：{len(linked)}。原始文件、旧报告和提交物继续由各自负责人维护；整合模块只发布证据包。
"""
    (destination/"HANDOFF.md").write_text(handoff)
    by_priority = Counter(r["priority"] for r in ctx.gaps if r["status"]=="open")
    by_status = Counter(r["status"] for r in ctx.gaps)
    summary = ["# Data quality summary","",f"Data version: `{version}`.","",
        f"Automated checks: {report['check_count']}; failures: {report['failure_count']}.",
        f"Open gaps by priority: {dict(sorted(by_priority.items()))}.",
        f"All gap statuses: {dict(sorted(by_status.items()))}.","",
        "## Deliberately retained limitations","",
        "- Unknown coordinates and fees remain missing; transformed coordinates are estimates, not surveyed gates.",
        "- Three K7 route records remain archived and excluded; no unresolved candidate becomes an accepted entity.",
        "- Historical G12 is retired after the teacher erratum; no two-community comparison is enforced.",
        "- Housing CSV historical hash difference is explained by LF/CRLF bytes; originals were not rewritten.",
        "- Source availability is separate from fact validity: reference-only and failed historical downloads remain visible.",
        "- The original traffic script reproduces its four derived CSVs byte-for-byte in a disposable directory.",
        "- Imported verified facts describe external declarations; review quarantine and original source availability.","",
        "## Review files","",
        "- `data/research_gaps.csv`: priority, entity, original evidence, needed information and task status.",
        "- `data/import_quarantine.csv`: retained original incoming rows and rejection reasons.",
        "- `quality_report.json`: every automated check and its result.",
        "- `run_manifest.json`: pinned inputs, code/data version and generated artifact hashes.",""]
    (destination/"QUALITY_SUMMARY.md").write_text("\n".join(summary))


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
