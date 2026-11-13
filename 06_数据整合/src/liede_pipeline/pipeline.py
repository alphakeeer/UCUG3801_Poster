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
    write_json(destination/"run_manifest.json",dict(pipeline_version="1.1.0",research_year=2026,
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
    t = ctx.tables
    mapped_home = sum(bool(r["preferred_position_id"]) for r in t["residences"])
    mapped_school = sum(bool(r["preferred_position_id"]) for r in t["education_campuses"])
    usable = sum(r["analytical_eligible"] for r in t["transport_routes"])
    charges = sum(r["actual_charge"] for r in t["education_fees"])
    handoff = f"""# 研究交接与证据包

数据版本：`{version}`。仅研究猎德及相关周边的幼儿园与小学，不要求两个社区比较。本模块没有修改旧报告、交互地图或海报。

## 阅读入口

1. [本轮补证整合报告](补证整合报告.md)：45条原始证据的处理结果、来源、年份与保留缺口。
2. [表 C：跨领域证据矩阵](table_C_evidence_matrix.md)：{len(t['evidence_matrix'])}项发现及数据、来源、解释边界。
3. [图 A：住房与园校分布](figures/figure_A_housing_education.png) · [图 B：住房、招生与可达性](figures/figure_B_admission_accessibility.png)。
4. [中文图注及出处](FIGURE_LEGENDS.md)：插入报告或海报时须保留；同目录有可编辑SVG及PDF。
5. [质量摘要](QUALITY_SUMMARY.md) · [缺口表](data/research_gaps.csv) · [字段字典](../DATA_DICTIONARY.md)。

图件和图注通过 `all`生成；仅运行 `build`时尚无图件。

## 本轮新增及采用边界

- 完整接入GPT Work的45条补证，逐条保留原核验标签、适用年份、来源定位和文件哈希，未整批提升为“已核实事实”。未重复互联网研究。
- K7由官方同址和新旧名称同一高德POI支持，关联至第二实验幼儿园珠江新城园区。仅确认物理园区；当年配套范围及接送门仍未知。D3→K7的18米异常路线继续排除。
- 华文、海滨是既有43条候选中的两园，新增坐标，不增加或合并园区实体。华文属国企办，海滨属普惠性民办，招生渠道分别处理。
- 新增三条定向步行路线。南国花园至海滨298米、238秒（约4.0分钟），只改变扩展已测候选的最近值。原六园敏感性仍按原分母解释；未补齐住宅×园区全矩阵。
- 南国花园新增两条整租（7500元/108.58平方米、5800元/80平方米）和一条出售挂牌（582万元/107.44平方米，标示单价54170元/平方米）。不平均，不替代合同、成交或小区参考价；参考价冲突线索不进主价格指标。
- 新增7条细分招生条件，明确安置户属于优先统筹、租户两组备案期限及幼儿园业主顺序。旧家庭情境未被改写为真实家庭资格或结果。
- 核心四园区2026新小班实价仍缺失。995元政策推定、2024历史转载及机构预算不能当作当期园区实收费或家庭实付。

## 当前数据覆盖

| 对象 | 数量与限制 |
|---|---|
| 住宅 | {len(t['residences'])}个项目，{mapped_home}个有地图参照；不是家庭样本 |
| 园校 | {len(t['education_campuses'])}条独立园区/小学校区，{mapped_school}条有可采用位置；不是全量普查 |
| 路线 | {len(t['transport_routes'])}条保留记录，{usable}条可关联分析；门点未经实走 |
| 住房观察 | {len(t['housing_observations'])}条，指标和日期不得直接混排 |
| 招生渠道比较 | {len(t['accessibility_comparisons'])}条，全部实际录取未观察 |
| 本轮原格式补证 | {len(t['work_evidence'])}条；另有通用导入接口，不能把两表相加当独立来源数 |
| 细分招生条件 | {len(t['admission_conditions'])}条；不是7类真实家庭 |
| 当期园校公示/缴费类型记录 | {charges}条；政策、批复、历史和推定另列 |

## 分析连接与交付

- [住宅—园校连接表](data/housing_education_links.csv)：一行一条合格案例路线，带住房指标和规则/费用ID。展开一对多规则后不要重复合计。
- [渠道可达性](data/accessibility_comparisons.csv)：图B的九条比较；冼村小学只是一个积分志愿例，并非实际分配或已证明的最近可申请校。
- [补证原标签表](data/work_evidence.csv)和[细分招生条件](data/admission_conditions.csv)用于补充解释。`subject_ids`为明确关联，机构级未确认记录保持未确认，不下分K7。
- [住宅](data/residences.csv)、[园校](data/education_campuses.csv)、[来源](data/source_registry.csv)、[实体对应](data/entity_crosswalk.csv)为关联入口。逐条数值读取住房观察、招生计划、费用表。
- 字段名、ID和枚举代码保留稳定英文机器接口；本模块报告、图件及主要解释文字使用中文。

## 必须保留的解释边界

房价不代表家庭收入；地理邻近、具有条件性申请渠道和实际录取分开。未观察收入、预算、净缴费、实际家庭录取与接送。猎德花园五区点、平台门牌与海文路交通点不作为同一栋或同一户；中海31/33号只确认项目层对应。机构总计划不在校区间重复，班数、人数、业主及剩余派位量不混加。

缺失和冲突不填0，不自动选最新或取平均。部分来源只有外部网址及补证摘录，来源可用性与事实可信度分别记录。

## 下一步补证优先级

P0：K1/K6/K7的2026配套楼栋、产权材料及简章；核心四园当年收费牌、餐费、必要项目及减免票据；猎德花园逐栋权属；南国花园同月同平台参考价和可复核交易/租金汇总。

P1：D3→K7常用人行门到接送门实走，核对门禁、开放时段与等待；仅补可能改变结论的候选。家庭申请、录取、实付和接送若无资料须继续保留未观察。

## 复现和后续导入

运行 `../run.py all`及 `../run.py validate`。本轮固定输入{len(json.loads((ctx.module/'config/input_manifest.json').read_text()))}份，含远端8份补证；旧175份输入哈希不变。现有工作文件以本机保护基线校验，输出另有逐文件哈希。

[GPT Work导入说明](../IMPORT_VERIFIED_FACTS.md)区分本轮原格式适配器与通用模板。新证据按新文件、新ID追加，不覆盖原数据。旧报告、理论稿、地图及海报继续由原负责人维护。
"""
    (destination/"HANDOFF.md").write_text(handoff)
    by_priority = Counter(r["priority"] for r in ctx.gaps if r["status"]=="open")
    summary = ["# 数据质量摘要","",f"数据版本：`{version}`。","",
        f"自动检查：{report['check_count']}项；失败：{report['failure_count']}项。",
        f"开放缺口按优先级：{dict(sorted(by_priority.items()))}。","",
        "## 保留的限制与核验结果","",
        "- 补证45条完整保留；未核实、历史、政策推定与当期事实分别记录。",
        "- K7物理园区关联已有依据；D3→K7的18米异常仍排除。确认别名不等于确认路线。",
        "- 原39条路线及新增3条分开；旧六园敏感性不混入新候选。",
        "- 南国花园两条整租和一条出售挂牌不是小区均价；索引参考价冲突不自动裁决。",
        "- 未知坐标、实际费用继续留空；转换位置不是实测接送门。",
        "- 历史G12因老师勘误退役，不要求两个社区比较；初中不进入分析。",
        "- 旧住房哈希差异由LF/CRLF字节解释，原文件未改写。",
        "- 来源归档完整性与事实正确性分开；外部网页没有原件时仍标为仅引用。",
        "- 既有交通脚本在临时目录复算，四张CSV与原结果逐字节相同。",
        "- 远端同步保留本地29项未提交工作；索引只增加远端入口。","",
        "## 检查文件","",
        "- `data/research_gaps.csv`：优先级、原证据、所需补证及任务状态。",
        "- `data/work_evidence.csv`：45条补证的原核验标签、实体关联和采用边界。",
        "- `data/import_quarantine.csv`：通用导入待核行及原因。",
        "- `quality_report.json`：完整检查；`run_manifest.json`：输入、版本及输出哈希。",""]
    (destination/"QUALITY_SUMMARY.md").write_text("\n".join(summary))
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
