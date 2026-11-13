import json
from collections import Counter
from pathlib import Path

from .common import Context, EDUCATION, TRANSPORT, digest
from .coordinates import chord_m, wgs84_to_gcj02


def protected_snapshot(root: Path,module: Path) -> dict:
    return {str(p.relative_to(root)):digest(p) for p in sorted(root.rglob("*"))
            if p.is_file() and ".git" not in p.relative_to(root).parts and not p.is_relative_to(module)}


def check_protected(root,module):
    path = module/".state/protected_files.json"
    if not path.exists():
        return dict(id="protected_working_files",passed=True,detail="本地未建保护基线；仍检查固定输入和已登记原件")
    baseline = json.loads(path.read_text())
    changed = [name for name,value in baseline.items() if not (root/name).is_file() or digest(root/name)!=value]
    return dict(id="protected_working_files",passed=not changed,detail=changed or "保护基线中的既有文件字节未变")


def input_checks(root,module):
    manifest = json.loads((module/"config/input_manifest.json").read_text())
    return [dict(id="input:"+name,passed=(root/name).is_file() and digest(root/name)==expected,
                 detail=name) for name,expected in manifest.items()]


def validate(ctx: Context) -> dict:
    checks = input_checks(ctx.root,ctx.module)+[check_protected(ctx.root,ctx.module)]
    checks += ctx.source_manager.verify_archives()+getattr(ctx,"legacy_checks",[])
    def check(name,condition,detail):
        checks.append(dict(id=name,passed=bool(condition),detail=detail))
    tables = ctx.tables
    for name,rows in tables.items():
        check("unique_id:"+name,len(rows)==len({r["id"] for r in rows}),f"{len(rows)} records")
    entities = {r["id"] for name in ["residences","education_campuses","institutions","admission_rules"] for r in tables[name]}
    keys = [(r["namespace"],r["source_record_id"],r["entity_type"]) for r in tables["entity_crosswalk"]]
    check("crosswalk_single_target",len(keys)==len(set(keys)),"命名空间、原对象ID与实体类型的组合须唯一")
    check("crosswalk_no_forced_match",all((r["entity_id"] in entities) if r["match_status"]=="matched" else not r["entity_id"] for r in tables["entity_crosswalk"]),"未确认对应不得填写已接受对象ID")
    check("primary_kindergarten_only",all(r["stage"] in {"primary","kindergarten"} for name in ["education_campuses","admission_rules","admission_plans","education_fees","household_scenarios","admission_conditions"] for r in tables[name]) and all(r["stage"] in {"","primary","kindergarten"} for r in tables["admission_evidence"]),"分析学段只含幼儿园和小学；住宅类文本注释可不指定学段，原政策文本可能覆盖更多学段")
    campuses = {r["id"] for r in tables["education_campuses"]}
    positions = {r["id"]:r for r in tables["positions"]}
    foreign_keys = {"residence_id":{r["id"] for r in tables["residences"]},
        "campus_id":campuses,"candidate_campus_id":campuses,
        "institution_id":{r["id"] for r in tables["institutions"]},
        "rule_id":{r["id"] for r in tables["admission_rules"]},
        "fee_id":{r["id"] for r in tables["education_fees"]},
        "route_id":{r["id"] for r in tables["transport_routes"]},
        "baseline_route_id":{r["id"] for r in tables["transport_routes"]},
        "preferred_position_id":set(positions),"origin_position_id":set(positions),"destination_position_id":set(positions),
        "work_evidence_id":{r["id"] for r in tables.get("work_evidence",[])}}
    invalid_links = [(name,r["id"],field,r[field]) for name,rows in tables.items() for r in rows
                     for field,allowed in foreign_keys.items() if r.get(field) and r[field] not in allowed]
    check("relational_foreign_keys",not invalid_links,invalid_links or "规范实体、位置、规则、计划和路线引用可解析")
    check("normalized_crs",all(p["crs"]=="EPSG:4326" and 112<p["longitude"]<115 and 22<p["latitude"]<25 for p in positions.values()),"统一WGS84经纬度，不用展示XY替代")
    errors = []
    for p in positions.values():
        if p["original_crs"]=="GCJ-02":
            lon,lat = wgs84_to_gcj02(p["longitude"],p["latitude"])
            errors.append(chord_m(lon,lat,p["original_longitude"],p["original_latitude"]))
    check("gcj_numeric_roundtrip",all(e<.02 for e in errors),{"max_numerical_error_m":max(errors,default=0),"not_a_field_accuracy_estimate":True})
    check("position_entity_references",all(not p["entity_id"] or p["entity_id"] in entities for p in positions.values()),"候选对应与已接受对应分开")
    check("preferred_positions",all(not r["preferred_position_id"] or (r["preferred_position_id"] in positions and positions[r["preferred_position_id"]]["entity_id"]==r["id"]) for name in ["residences","education_campuses"] for r in tables[name]),"默认位置须关联同一实体")
    routes = tables["transport_routes"]
    routekeys = [(r["origin_legacy_id"],r["destination_legacy_id"],r["route_date"],r["mode"]) for r in routes]
    legacy_routes = [r for r in routes if r["route_date"]=="2026-11-12"]
    check("routes_no_round1_double_count",len(legacy_routes)==39 and len(set(routekeys))==len(routes),"原30+9条与11月13日定向补查分开；第一轮18条不再追加")
    check("work_evidence_complete",len(tables.get("work_evidence",[]))==45,"完整保留45条补证及原核验标签，不整批提升可信度")
    check("work_subjects_resolve",all(s in entities for r in tables.get("work_evidence",[]) for s in r["subject_ids"]),"补证显式实体对应可解析；机构级未确认不下分园区")
    check("work_no_reference_price_invention",not any(r["id"].startswith("WORK-") and r["residence_id"]=="RES018" and r["metric"]=="market_reference_sale_cny_m2" for r in tables["housing_observations"]),"本轮南国花园挂牌与冲突索引不转为小区参考价；未来可靠新证据仍可经通用接口追加")
    check("work_estimated_fee_not_actual",all(not r["actual_charge"] for r in tables["education_fees"] if r["id"].startswith("WORK-")),"本轮没有取得2026逐园收费单，历史或推定不进入实际收费")
    check("work_targeted_routes",len([r for r in routes if r["route_date"]=="2026-11-13"])==3,"定向新增三条POI路线；与原六园敏感性样本分开")
    check("work_plan_traceability",all(p in {r["id"] for r in tables["admission_plans"]} for r in tables.get("plan_corroboration",[]) for p in r["plan_ids"]),"补证交叉核对指向既有计划，不追加或重复求和")
    check("work_snapshot_traceability",all(s in ctx.source_manager.rows for r in tables.get("work_evidence",[]) for s in r["snapshot_source_ids"]),"每条补证的本地载体来源均已登记")
    check("excluded_subchord_route",all(not r["analytical_eligible"] for r in routes if r["origin_legacy_id"]=="D3" and r["destination_legacy_id"]=="K7"),"已知异常路线保留归档，禁止进入分析")
    check("route_entity_integrity",all(not r["analytical_eligible"] or (r["campus_id"] in campuses and r["length_check_passed"]) for r in routes),"目的地未确认的路线不得进入分析")
    check("no_observed_admission_invention",all(r["actual_admission"]=="unobserved" for name in ["household_scenarios","accessibility_comparisons","housing_education_links"] for r in tables[name]),"当前结果为制度路径或模型路线")
    check("missing_fee_not_zero",all(r["value"] is None for r in tables["education_fees"] if r["value_status"] in {"unknown","not_collected"}),"缺失保留空值，政策零值另行保留")
    check("legal_zero_retained",any(r["id"]=="FEE-F06" and r["value"]==0 for r in tables["education_fees"]),"法定零学费不被缺失值处理抹去")
    shared = [r for r in tables["admission_plans"] if r["subject_id"]=="INS-SCH-TH1"]
    check("institution_plan_not_duplicated",len(shared)==1 and shared[0]["value"]==7 and shared[0]["unit"]=="class","机构7班总计划只记一次，不在两个校区各记7班")
    check("plan_subject_grain",all(r["subject_id"] in entities and r["unit"] in {"class","person"} for r in tables["admission_plans"]),"班数、人数和派位组成项分别保存")
    check("district_primary_points_total",sum(r["value"] for r in tables["district_primary_points_plan"])==315,"区级计划只计一次，不与地理样本合计")
    other = ctx.csv(TRANSPORT/"data/round-3/primary-migrant-points-plan-2026.csv")
    clean = lambda name:name.replace("广州市天河区","").replace("广州市","")
    check("overlapping_points_plan_consistent",sorted((clean(r["school_name"]),r["value"]) for r in tables["district_primary_points_plan"])==sorted((clean(r["school"]),float(r["places"])) for r in other),"重叠来源记录一致，不重复追加")
    source_ids = set(ctx.source_manager.rows)
    missing_sources = []
    for name,rows in tables.items():
        for r in rows:
            refs = ([r["source_id"]] if r.get("source_id") else [])+r.get("source_ids",[])
            missing_sources += [(name,r["id"],s) for s in refs if s not in source_ids]
    check("source_foreign_keys",not missing_sources,missing_sources or "所有分析来源引用可解析")
    refs = {f"{name}:{r['id']}" for name,rows in tables.items() for r in rows}
    missing_refs = [ref for r in tables["evidence_matrix"] for ref in r["supporting_data"] if ref not in refs]
    check("evidence_row_traceability",not missing_refs,missing_refs or "每项支持数据都能定位到输出行")
    failures = [r for r in checks if not r["passed"]]
    return dict(passed=not failures,check_count=len(checks),failure_count=len(failures),
                checks=checks,known_research_gaps=len(ctx.gaps),
                quarantine_count=len(tables.get("import_quarantine",[])))
