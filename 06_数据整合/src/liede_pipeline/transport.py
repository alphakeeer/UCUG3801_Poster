"""Reuse the existing transport pipeline in a disposable directory only."""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .common import TRANSPORT, Context, digest, number, read_csv, stable_id

LEGACY_OUTPUTS = ["supplementary-route-audit.csv", "threshold-sensitivity.csv",
                  "household-scenarios.csv", "commute-burden-scenarios.csv"]


def reproduce_legacy(root: Path) -> tuple[dict, list[dict]]:
    base = root/TRANSPORT
    with tempfile.TemporaryDirectory(prefix="liede-transport-") as directory:
        work = Path(directory)
        for target in ["scripts", "data/round-2", "data/round-3"]:
            (work/target).mkdir(parents=True)
        for relative in ["scripts/reproduce.py", "data/round-2/liede-accessibility-round-2.json", "data/round-3/supplementary-amap.json"]:
            shutil.copyfile(base/relative,work/relative)
        subprocess.run([sys.executable,str(work/"scripts/reproduce.py"),"--no-figure"],
                       check=True,capture_output=True,text=True)
        outputs,checks = {},[]
        for name in LEGACY_OUTPUTS:
            output = work/"data/round-3"/name
            original = base/"data/round-3"/name
            checks.append(dict(id="legacy_reproduction:"+name,passed=digest(output)==digest(original),
                               detail="Disposable copy; legacy files not written"))
            outputs[name] = read_csv(output)
        return outputs,checks


def build_transport(ctx: Context):
    derived,checks = reproduce_legacy(ctx.root)
    ctx.legacy_checks = checks
    basepath = TRANSPORT/"data/round-2/liede-accessibility-round-2.json"
    suppath = TRANSPORT/"data/round-3/supplementary-amap.json"
    base = json.loads((ctx.root/basepath).read_text())
    supplement = json.loads((ctx.root/suppath).read_text())
    base_source = ctx.source_manager.archive_local(str(basepath),"Amap transport round 2 compilation","route_snapshot")
    sup_source = ctx.source_manager.archive_local(str(suppath),"Amap supplemental response","route_response")
    r1 = ctx.root/TRANSPORT/"data/round-1/liede-transport-accessibility-2026.json"
    ctx.legacy_checks.append(dict(id="round1_provenance",passed=digest(r1)==base["first_round_provenance"]["sha256"],detail="Round 1 is a subset, not an additional route sample"))
    for r in base["routes"]:
        _route(ctx,r["origin_id"],r["destination_id"],r["walking_meters"],r["walking_seconds"],
            "amap_estimate_gate_unverified",base_source,str(basepath),r.get("walking_url",""),
            r.get("amap_pc_morning_transit",{}))
    for r in derived["supplementary-route-audit.csv"]:
        _route(ctx,r["origin_id"],r["destination_id"],float(r["walking_meters"]),float(r["walking_seconds"]),
            r["quality"],sup_source,str(suppath),r["amap_walking_url"],{},number(r["endpoint_chord_m_for_qa"]))
    for r in derived["threshold-sensitivity.csv"]:
        typed = dict(r)
        for field in ["speed_mps","closest_minutes"]:
            typed[field] = number(r[field])
        for field in ["added_distance_m","added_delay_s","threshold_min","sample_count"]:
            typed[field] = int(r[field])
        typed["reachable_ids"] = r["reachable_ids"].split("|") if r["reachable_ids"] else []
        ctx.table("walking_sensitivity").append(dict(id=stable_id("SENS-",r),**typed,
            evidence_type="constructed_sensitivity",source_id=base_source,
            source_ids=[base_source] if r["coverage"]=="original_6" else [base_source,sup_source]))
    ctx.tables["escort_scenarios"] = [dict(id=stable_id("ESCORT-",r),
        **{k:v if k in {"origin_id","destination_id"} else number(v) for k,v in r.items()},
        evidence_type="constructed_scenario",source_id=base_source) for r in derived["commute-burden-scenarios.csv"]]
    for r in derived["household-scenarios.csv"]:
        stage = "primary" if r["stage"]=="primary_1" else "kindergarten"
        origin = ctx.transport_mapping[r["origin_id"]]["entity_id"]
        target = r["school_for_policy_comparison"]
        dest = ctx.transport_mapping[target]["entity_id"] if target else ""
        source = ctx.source_manager.reference(r["source_url"],"Admission policy supporting scenario",
            str(TRANSPORT/"scripts/reproduce.py"),"policy_reference")
        ctx.table("household_scenarios").append(dict(id=stable_id("SCEN-",r["origin_id"],r["profile"],stage),
            residence_id=origin,origin_legacy_id=r["origin_id"],stage=stage,profile=r["profile"],
            campus_id=dest,destination_legacy_id=target,conditions=r["conditions"],
            eligibility_status=r["eligibility_status"],actual_admission="unobserved",
            affordability="unknown",walk_minutes=number(r["comparison_route_walk_minutes"]),
            source_ids=[source],source_locator="Legacy scenario model",
            evidence_type="constructed_household_scenario",note="No real household was observed"))
    _comparisons(ctx)


def _route(ctx, origin, destination, meters, seconds, quality, source, path, url, transit, chord=None):
    a,b = ctx.transport_mapping[origin],ctx.transport_mapping[destination]
    length_valid = quality!="excluded_subchord_distance"
    mapping_valid = a["match_status"]=="matched" and b["match_status"]=="matched"
    eligible = length_valid and mapping_valid
    t,fare = None,None
    if transit.get("status")=="itinerary_returned":
        choice = transit["options"][transit["preferred_index"]]
        t,fare = choice["time_minutes"],choice["fare_cny"]
    ctx.table("transport_routes").append(dict(id=f"ROUTE-{origin}-{destination}-20261112-walk",
        residence_id=a["entity_id"],campus_id=b["entity_id"],candidate_campus_id=b["candidate_entity_id"],
        origin_legacy_id=origin,destination_legacy_id=destination,
        origin_position_id="POS-AMAP-"+origin,destination_position_id="POS-AMAP-"+destination,
        route_date="2026-11-12",mode="walking",distance_m=float(meters),duration_s=float(seconds),
        model_speed_mps=1.25,length_check_passed=length_valid,quality=quality,
        analytical_eligible=eligible,exclusion_reason="" if eligible else "subchord_distance" if not length_valid else "unresolved_destination_identity",
        endpoint_chord_m=chord,actual_trip_observed=False,gate_verified=False,
        source_id=source,source_path=path,source_locator=origin+"→"+destination,route_url=url,
        morning_transit_minutes=t,morning_adult_fare_cny=fare,
        transit_model_departure="2026-11-12 07:20 Asia/Shanghai" if transit else "",
        note="POI-to-POI model estimate; no route polyline or verified school gate; an absent transit result is not proof of no service"))


def _comparisons(ctx):
    routes = {(r["origin_legacy_id"],r["destination_legacy_id"]):r for r in ctx.table("transport_routes")}
    assigned = {"D1":"S1","D2":"S3","D3":"S4"}
    for origin,base in assigned.items():
        for channel,target,rule in [("address_linked_conditional",base,"P1"),
                ("migrant_points_listed_example","S5","P3"),("hk_macao_listed_channel","S4","P4")]:
            r,b = routes[origin,target],routes[origin,base]
            ctx.table("accessibility_comparisons").append(dict(id=f"ACCESS-{origin}-{channel}",
                residence_id=r["residence_id"],origin_legacy_id=origin,campus_id=r["campus_id"],
                channel=channel,rule_id=ctx.rule_ids[rule],route_id=r["id"],
                baseline_route_id=b["id"],walk_minutes=r["duration_s"]/60,
                baseline_minutes=b["duration_s"]/60,additional_minutes=(r["duration_s"]-b["duration_s"])/60,
                policy_year=2026,eligibility="conditional_pathway_only",actual_admission="unobserved",
                actual_commute="unobserved",analytical_eligible=r["analytical_eligible"],
                source_ids=[r["source_id"],"E002"]+(["E030","E030-A001"] if rule=="P3" else ["E031"] if rule=="P4" else []),
                interpretation_boundary="Xian Cun is one listed option, not the nearest eligible option or an allocation; address-linked eligibility requires full household checks"))
