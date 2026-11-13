"""Append-only, typed import boundary for GPT Work verified-fact CSVs."""

import json
from datetime import date
from collections import defaultdict
from pathlib import Path

from .common import Context, digest, number, read_csv, stable_id
from .coordinates import position
from .entities import select_positions

FACT_FIELDS = ["fact_id","subject_type","subject_id","predicate","value","unit",
    "reference_period","stage","source_id","source_url","source_title","source_locator",
    "evidence_type","verification_status","verified_on","verified_by","notes"]
NUMERIC = {
    "housing_reference_price_cny_m2":("residence","cny_per_m2","market_reference_sale_cny_m2"),
    "housing_rent_cny_month":("residence","cny_per_month","rent_cny_month"),
    "housing_rent_cny_m2_month":("residence","cny_per_m2_month","rent_cny_m2_month"),
    "policy_rent_cny_m2_month":("residence","cny_per_m2_month","policy_rent_cny_m2_month"),
    "tuition_cny_term":("campus","cny_per_person_term","published_tuition"),
    "care_fee_cny_month":("campus","cny_per_person_month","published_care_fee"),
    "meal_fee_cny_month":("campus","cny_per_person_month","published_meal_fee"),
    "subsidy_cny_term":("campus","cny_per_person_term","conditional_subsidy"),
}
PREDICATES = set(NUMERIC) | {"coordinate_wgs84","admission_note","research_gap"}


def read_feed(path: Path) -> list[dict]:
    import csv
    with path.open(encoding="utf-8-sig",newline="") as handle:
        reader = csv.DictReader(handle)
        missing = set(FACT_FIELDS)-set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path.name}: missing columns {sorted(missing)}")
        rows = list(reader)
        if any(None in row or any(value is None for value in row.values()) for row in rows):
            raise ValueError(f"{path.name}: malformed CSV row (check JSON quoting)")
        return rows


def integrate_feeds(ctx: Context, inbox: Path):
    records = []
    # Local facts are curator annotations of existing reports, not fresh research.
    paths = [(ctx.module/"config/local_facts.csv",True)]
    paths += [(p,False) for p in sorted(inbox.glob("*.csv")) if not p.name.startswith(".")]
    for path,local in paths:
        if not path.exists():
            continue
        for n,r in enumerate(read_feed(path),2):
            records.append((r,path,n,local))
    grouped = defaultdict(list)
    for item in records:
        grouped[item[0]["fact_id"]].append(item)
    for fact_id,items in sorted(grouped.items()):
        payloads = {json.dumps(r,sort_keys=True,ensure_ascii=False) for r,_,_,_ in items}
        if len(payloads)>1:
            for r,path,n,_ in items:
                _quarantine(ctx,r,path,n,"conflicting_duplicate_fact_id")
            continue
        r,path,n,local = items[0]
        reason = _validate_fact(ctx,r,local)
        if reason:
            _quarantine(ctx,r,path,n,reason)
            continue
        try:
            source = r["source_id"]
            if r["source_url"]:
                source = ctx.source_manager.reference(r["source_url"],r["source_title"],path.name,
                    "external_declared_verified" if not local else "repository_report_reference",
                    requested_id=source)
            status = "reported_repository" if local else "external_declared_verified"
            _apply(ctx,r,source,status)
        except (ValueError,KeyError,TypeError,json.JSONDecodeError) as error:
            _quarantine(ctx,r,path,n,"invalid_value_or_source: "+str(error))
            continue
        ctx.table("verified_facts").append(dict(id=fact_id,**r,
            input_file=path.name,input_sha256=digest(path),input_row=n,
            resolved_source_id=source,integration_status="appended_without_overwrite",
            local_verification=status,duplicate_copies_ignored=len(items)-1))
    select_positions(ctx)


def _validate_fact(ctx,r,local):
    required = ["fact_id","subject_type","subject_id","predicate","value","reference_period",
                "source_locator","evidence_type","verification_status","verified_by"]
    if any(not r[k].strip() for k in required):
        return "missing_required_value"
    if r["verification_status"] != ("reported_repository" if local else "verified"):
        return "verification_not_confirmed"
    if not local and not r["verified_on"]:
        return "missing_verification_date"
    if not local:
        try:
            date.fromisoformat(r["verified_on"])
        except ValueError:
            return "invalid_verification_date"
    registry = {"residence":ctx.table("residences"),"campus":ctx.table("education_campuses"),
                "institution":ctx.table("institutions"),"rule":ctx.table("admission_rules")}
    if r["subject_type"] not in registry or r["subject_id"] not in {x["id"] for x in registry[r["subject_type"]]}:
        return "unresolved_entity_id"
    if r["stage"] not in {"","primary","kindergarten"}:
        return "out_of_scope_stage"
    if r["subject_type"]=="campus":
        campus = next(x for x in ctx.table("education_campuses") if x["id"]==r["subject_id"])
        if r["stage"] != campus["stage"]:
            return "campus_stage_mismatch"
    if r["predicate"] not in PREDICATES:
        return "unsupported_predicate"
    if r["predicate"] in NUMERIC:
        kind,unit,_ = NUMERIC[r["predicate"]]
        if kind!=r["subject_type"] or unit!=r["unit"]:
            return "predicate_subject_or_unit_mismatch"
    elif r["predicate"]=="coordinate_wgs84" and r["subject_type"] not in {"residence","campus"}:
        return "coordinate_subject_mismatch"
    if not r["source_url"] and r["source_id"] not in ctx.source_manager.rows:
        return "unresolved_source"
    if r["source_id"] not in ctx.source_manager.rows and not r["source_title"].strip():
        return "missing_source_title"
    if r["predicate"]=="coordinate_wgs84" and r["unit"]!="degrees":
        return "coordinate_unit_mismatch"
    return ""


def _quarantine(ctx,r,path,n,reason):
    ctx.table("import_quarantine").append(dict(id=stable_id("QUAR-",path.name,digest(path),n,r),
        fact_id=r.get("fact_id",""),input_file=path.name,input_row=n,
        reason=reason,original_record=r))
    ctx.gap("IMPORT_REVIEW","P0",r.get("fact_id",""),reason,"Resolve entity/source/unit or fact conflict; no automatic matching")


def _apply(ctx,r,source,status):
    predicate = r["predicate"]
    if predicate in NUMERIC:
        kind,unit,metric = NUMERIC[predicate]
        value = number(r["value"])
        if value is None or value<0:
            raise ValueError("A nonnegative finite number is required")
        if kind=="residence":
            ctx.table("housing_observations").append(dict(id="FACT-"+r["fact_id"],residence_id=r["subject_id"],
                metric=metric,value=value,unit=unit,reference_period=r["reference_period"],observed_on="",
                area_m2=None,total_ask_cny=None,evidence_type=r["evidence_type"],verification_status=status,
                comparable_sale=r["subject_id"] not in {"RES001","RES017"},source_id=source,
                source_path="import:"+r["fact_id"],source_locator=r["source_locator"],conflict_status="no_adjudication",
                note=r["notes"]+"; Imported evidence is appended; original observations remain"))
        else:
            ctx.table("education_fees").append(dict(id="FACT-"+r["fact_id"],stage=r["stage"],campus_id=r["subject_id"],
                metric=metric,value=value,unit=unit,value_status="externally_reported_verified",amount_relation="stated",
                evidence_type=r["evidence_type"],reference_period=r["reference_period"],
                evidence_year=int(r["reference_period"][:4]) if r["reference_period"][:4].isdigit() else None,
                applicability=r["notes"],target_raw="",source_ids=[source],source_path="import:"+r["fact_id"],
                source_locator=r["source_locator"],verification_status=status,
                actual_charge=predicate in {"tuition_cny_term","care_fee_cny_month","meal_fee_cny_month"} and r["evidence_type"] in {"published_fee_schedule","actual_receipt"},
                note="Published schedule or reported charge; not automatically an observed household payment"))
    elif predicate=="coordinate_wgs84":
        value = json.loads(r["value"])
        lon,lat = number(value["longitude"]),number(value["latitude"])
        role = value["position_role"]
        if lon is None or lat is None or not (112<lon<115 and 22<lat<25):
            raise ValueError("Coordinate must be a finite Guangzhou WGS84 longitude/latitude")
        if role not in {"campus_reference","campus_centroid","development_reference","residential_phase_reference","transport_origin_poi","transport_destination_poi","verified_gate"}:
            raise ValueError("Unsupported position role")
        existing = [p for p in ctx.table("positions") if p["entity_id"]==r["subject_id"] and p["position_role"]==role]
        conflict = any(abs(p["longitude"]-lon)>1e-8 or abs(p["latitude"]-lat)>1e-8 for p in existing)
        p = position("FACT-"+r["fact_id"],"" if conflict else r["subject_id"],role,lon,lat,"WGS84",source,
            r["source_locator"],"conflicting_external_coordinate" if conflict else "external_verified",
            r["notes"],r["subject_id"] if conflict else "")
        p["gate_verified"] = role=="verified_gate" and not conflict
        ctx.table("positions").append(p)
        if conflict:
            ctx.gap("COORDINATE_CONFLICT","P0",r["subject_id"],"Same-role coordinate disagrees with existing evidence",
                    "Review both positions; existing default retained",[source])
    elif predicate=="admission_note":
        ctx.table("admission_evidence").append(dict(id="FACT-"+r["fact_id"],subject_id=r["subject_id"],
            subject_type=r["subject_type"],stage=r["stage"],reference_period=r["reference_period"],
            claim=r["value"],source_id=source,source_locator=r["source_locator"],verification_status=status,
            note="Append-only evidence; eligibility logic requires explicit review before changing scenarios"))
    else:
        ctx.gap("EXTERNAL_GAP","P1",r["subject_id"],r["value"],r["notes"],[source])
