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
        return dict(id="protected_working_files",passed=True,detail="No local working baseline; pinned inputs and registered archives are still checked")
    baseline = json.loads(path.read_text())
    changed = [name for name,value in baseline.items() if not (root/name).is_file() or digest(root/name)!=value]
    return dict(id="protected_working_files",passed=not changed,detail=changed or "All pre-existing files unchanged")


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
    check("crosswalk_single_target",len(keys)==len(set(keys)),"Namespace + original ID + entity type must be unique")
    check("crosswalk_no_forced_match",all((r["entity_id"] in entities) if r["match_status"]=="matched" else not r["entity_id"] for r in tables["entity_crosswalk"]),"Unresolved rows have no accepted target")
    check("primary_kindergarten_only",all(r["stage"] in {"primary","kindergarten"} for name in ["education_campuses","admission_rules","admission_plans","education_fees","household_scenarios"] for r in tables[name]),"Scope applies to analytical stage columns; original source text can describe broader policies")
    campuses = {r["id"] for r in tables["education_campuses"]}
    positions = {r["id"]:r for r in tables["positions"]}
    check("normalized_crs",all(p["crs"]=="EPSG:4326" and 112<p["longitude"]<115 and 22<p["latitude"]<25 for p in positions.values()),"WGS84 longitude/latitude; no display XY substituted")
    errors = []
    for p in positions.values():
        if p["original_crs"]=="GCJ-02":
            lon,lat = wgs84_to_gcj02(p["longitude"],p["latitude"])
            errors.append(chord_m(lon,lat,p["original_longitude"],p["original_latitude"]))
    check("gcj_numeric_roundtrip",all(e<.02 for e in errors),{"max_numerical_error_m":max(errors,default=0),"not_a_field_accuracy_estimate":True})
    check("position_entity_references",all(not p["entity_id"] or p["entity_id"] in entities for p in positions.values()),"Candidate and accepted links remain distinct")
    check("preferred_positions",all(not r["preferred_position_id"] or (r["preferred_position_id"] in positions and positions[r["preferred_position_id"]]["entity_id"]==r["id"]) for name in ["residences","education_campuses"] for r in tables[name]),"Preferred position is associated with the same entity")
    routes = tables["transport_routes"]
    routekeys = [(r["origin_legacy_id"],r["destination_legacy_id"],r["route_date"],r["mode"]) for r in routes]
    check("routes_no_round1_double_count",len(routes)==39 and len(set(routekeys))==39,"30 baseline + 9 supplementary records; first-round 18 are not appended")
    check("excluded_subchord_route",all(not r["analytical_eligible"] for r in routes if r["origin_legacy_id"]=="D3" and r["destination_legacy_id"]=="K7"),"Known invalid route stays in archive but not analysis")
    check("route_entity_integrity",all(not r["analytical_eligible"] or (r["campus_id"] in campuses and r["length_check_passed"]) for r in routes),"Unresolved destination routes cannot enter analysis")
    check("no_observed_admission_invention",all(r["actual_admission"]=="unobserved" for name in ["household_scenarios","accessibility_comparisons","housing_education_links"] for r in tables[name]),"All current results are pathways or modeled trips")
    check("missing_fee_not_zero",all(r["value"] is None for r in tables["education_fees"] if r["value_status"] in {"unknown","not_collected"}),"Missing observations stay null; policy zeros remain valid")
    check("legal_zero_retained",any(r["id"]=="FEE-F06" and r["value"]==0 for r in tables["education_fees"]),"Statutory zero is not erased by missing-value handling")
    shared = [r for r in tables["admission_plans"] if r["subject_id"]=="INS-SCH-TH1"]
    check("institution_plan_not_duplicated",len(shared)==1 and shared[0]["value"]==7 and shared[0]["unit"]=="class","One seven-class plan, not two seven-class campus plans")
    check("plan_subject_grain",all(r["subject_id"] in entities and r["unit"] in {"class","person"} for r in tables["admission_plans"]),"Class counts, person counts and lottery components are separate")
    check("district_primary_points_total",sum(r["value"] for r in tables["district_primary_points_plan"])==315,"One district plan, not summed with geographic totals")
    other = ctx.csv(TRANSPORT/"data/round-3/primary-migrant-points-plan-2026.csv")
    clean = lambda name:name.replace("广州市天河区","").replace("广州市","")
    check("overlapping_points_plan_consistent",sorted((clean(r["school_name"]),r["value"]) for r in tables["district_primary_points_plan"])==sorted((clean(r["school"]),float(r["places"])) for r in other),"Overlapping source representations agree and are not appended")
    source_ids = set(ctx.source_manager.rows)
    missing_sources = []
    for name,rows in tables.items():
        for r in rows:
            refs = ([r["source_id"]] if r.get("source_id") else [])+r.get("source_ids",[])
            missing_sources += [(name,r["id"],s) for s in refs if s not in source_ids]
    check("source_foreign_keys",not missing_sources,missing_sources or "All analytical source references resolve")
    refs = {f"{name}:{r['id']}" for name,rows in tables.items() for r in rows}
    missing_refs = [ref for r in tables["evidence_matrix"] for ref in r["supporting_data"] if ref not in refs]
    check("evidence_row_traceability",not missing_refs,missing_refs or "Every supporting row is available")
    failures = [r for r in checks if not r["passed"]]
    return dict(passed=not failures,check_count=len(checks),failure_count=len(failures),
                checks=checks,known_research_gaps=len(ctx.gaps),
                quarantine_count=len(tables.get("import_quarantine",[])))
