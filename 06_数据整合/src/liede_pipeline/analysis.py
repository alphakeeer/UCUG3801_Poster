from pathlib import Path

from .common import Context, citation, ids, stable_id


def build_analysis(ctx: Context):
    observations = ctx.table("housing_observations")
    for residence in ctx.table("residences"):
        metrics = {}
        for metric in ["market_reference_sale_cny_m2","rent_cny_month","rent_cny_m2_month"]:
            candidates = [r for r in observations if r["residence_id"]==residence["id"] and r["metric"]==metric]
            # Different observations are kept even when they agree. Contradictory
            # periods or quotations are not silently averaged or resolved.
            distinct = {(r["value"],r["reference_period"]) for r in candidates}
            if len(distinct)>1:
                metrics[metric] = (None,"conflicting_or_multiple_periods",[r["id"] for r in candidates])
                ctx.gap("MULTIPLE_PRICE_VALUES","P0",residence["id"]+":"+metric,
                    "Multiple values or periods require an explicit analysis selection",
                    "Review observation IDs; no mean, latest-value or preferred-source rule is applied",
                    sorted({r["source_id"] for r in candidates}))
            elif candidates:
                row = candidates[0]
                excluded = metric=="market_reference_sale_cny_m2" and not row["comparable_sale"]
                metrics[metric] = (None if excluded else row["value"],"not_comparable" if excluded else "reported_reference",[r["id"] for r in candidates])
            else:
                metrics[metric] = (None,"missing",[])
        sale,rent,unit_rent = (metrics[k] for k in ["market_reference_sale_cny_m2","rent_cny_month","rent_cny_m2_month"])
        ctx.table("residence_cost_summary").append(dict(id=residence["id"],residence_id=residence["id"],
            name=residence["name"],english_name=residence["english_name"],
            preferred_position_id=residence["preferred_position_id"],sale_reference_cny_m2=sale[0],
            sale_status=sale[1],sale_observation_ids=sale[2],rent_cny_month=rent[0],rent_status=rent[1],
            rent_observation_ids=rent[2],rent_cny_m2_month=unit_rent[0],unit_rent_status=unit_rent[1],
            unit_rent_observation_ids=unit_rent[2],
            note="Purposeful sample; prices are not household income; monthly aggregate rents lack a unit-level denominator"))
    costs = {r["residence_id"]:r for r in ctx.table("residence_cost_summary")}
    campuses = {r["id"]:r for r in ctx.table("education_campuses")}
    for route in ctx.table("transport_routes"):
        if not route["analytical_eligible"]:
            continue
        campus = campuses[route["campus_id"]]
        cost = costs[route["residence_id"]]
        ctx.table("housing_education_links").append(dict(id="LINK-"+route["id"],
            residence_id=route["residence_id"],campus_id=campus["id"],institution_id=campus["institution_id"],
            stage=campus["stage"],ownership=campus["ownership"],route_id=route["id"],
            walk_minutes=route["duration_s"]/60,distance_m=route["distance_m"],
            sale_reference_cny_m2=cost["sale_reference_cny_m2"],sale_status=cost["sale_status"],
            sale_observation_ids=cost["sale_observation_ids"],rent_cny_month=cost["rent_cny_month"],
            rent_cny_m2_month=cost["rent_cny_m2_month"],
            rule_ids=[r["rule_id"] for r in ctx.table("campus_admission_rules") if r["campus_id"]==campus["id"]],
            fee_ids=[r["fee_id"] for r in ctx.table("fee_applicability") if r["campus_id"]==campus["id"]],
            eligibility="not_determined_by_distance",actual_admission="unobserved",
            note="Route measured at its own POI, not the preferred housing map point; not a household observation"))
    _gaps(ctx)
    _evidence(ctx)


def _gaps(ctx):
    for r in ctx.table("residences"):
        if not r["preferred_position_id"]:
            ctx.gap("RESIDENCE_POSITION_MISSING","P0",r["id"],"No accepted residence reference coordinate",
                    "Add a sourced coordinate with position role; do not use a nearby development")
        if not r["has_housing_sample"]:
            ctx.gap("HOUSING_SAMPLE_MISSING","P0",r["id"],"Residence exists in transport research but not the frozen housing sample",
                    "Add comparable housing evidence or retain missing values")
    for r in ctx.table("education_campuses"):
        if not r["preferred_position_id"]:
            ctx.gap("CAMPUS_POSITION_MISSING","P0",r["id"],"No accepted campus reference coordinate",
                    "Verify campus identity and location; preserve unresolved candidates",[r["source_id"]])
        ctx.gap("ACTUAL_FEE_MISSING","P0",r["id"],"Frozen campus status table has no 2026 published tuition/care amount",
            "Obtain campus fee schedule and extra charges; imported evidence remains separately traceable",[r["source_id"]],
            "supplemented_requires_review" if any(f["campus_id"]==r["id"] and f["actual_charge"] for f in ctx.table("education_fees")) else "open")
    for r in ctx.table("entity_crosswalk"):
        if r["match_status"]=="unresolved":
            ctx.gap("UNRESOLVED_ENTITY","P0",r["namespace"]+":"+r["source_record_id"],
                r["match_basis"],r["note"])
    legacy = ctx.csv(Path("03_背景/教育专题/数据/缺口冲突与排除.csv"))
    for r in legacy:
        if r["gap_id"]=="G15":
            continue  # Junior campus allocation is outside this analysis.
        status = "retired_scope_erratum" if r["gap_id"]=="G12" else "archive_available_multipart" if r["gap_id"]=="G11" else "open"
        ctx.gap("LEGACY_"+r["gap_id"],"P2" if status!="open" else "P1",r["gap_id"],r["finding"],
            "No two-community requirement; obsolete task retained only for audit" if r["gap_id"]=="G12" else r["needed_evidence"],ids(r["source_id"]),status)
    ctx.gap("HOUSING_HASH_LINE_ENDINGS","P1","housing_csv",
        "Historical report hash matches CRLF representation, while the checkout uses LF",
        "Retain both byte hashes; current input manifest pins checkout bytes; do not rewrite original")
    ctx.gap("SOURCE_COVERAGE","P1","commercial_housing_quotes",
        "Many commercial quotations have repository extracts but no archived original response",
        "GPT Work may supply sourced records; keep reported values and temporal definitions")
    ctx.gap("NO_OUTCOME_DATA","P1","all_household_scenarios",
        "No observed household allocation, budget or actual commute is present",
        "Keep policy pathways and modeled burdens separate from outcomes")


def _evidence(ctx):
    def add(key, finding, references, sources, boundary, limitation, kind):
        ctx.table("evidence_matrix").append(dict(id=key,finding=finding,supporting_data=references,
            source_ids=sorted(set(sources)),evidence_kind=kind,
            interpretation_boundary=boundary,limitation=limitation))
    campuses = ctx.table("education_campuses")
    mapped = [r for r in campuses if r["preferred_position_id"]]
    add("F01",f"{len(mapped)} of {len(campuses)} candidate campus records have an accepted map reference",
        [citation("education_campuses",r["id"]) for r in campuses],
        [r["source_id"] for r in campuses],"Candidate-set completeness only; not a Liede census",
        "Unknown gates and incomplete geographic selection","record_coverage")
    prices = ctx.table("housing_observations")
    add("F02","Housing cost evidence uses distinct market references, listings, rents and platform transaction reports",
        [citation("housing_observations",r["id"]) for r in prices],
        [r["source_id"] for r in prices],"Do not pool metrics, periods, ordinary housing and unverified rights",
        "Purposeful sample, incomplete snapshots; housing price is not income","archived_quotations")
    access = ctx.table("accessibility_comparisons")
    selected = next(r for r in access if r["origin_legacy_id"]=="D3" and r["channel"]=="migrant_points_listed_example")
    add("F03",f"Nanguo: the listed migrant-points example has {selected['additional_minutes']:.2f} more modeled walking minutes than the address-linked route",
        [citation("accessibility_comparisons",selected["id"]),citation("transport_routes",selected["route_id"])],
        selected["source_ids"],"One listed option, not an allocation or nearest eligible-school result",
        "POI routes, unverified gates, no observed family assignment","derived_case_comparison")
    add("F04","Admission pathways depend on household eligibility in addition to physical proximity",
        [citation("admission_rules",r["id"]) for r in ctx.table("admission_rules")],
        [s for r in ctx.table("admission_rules") for s in r["source_ids"]],
        "Conditional rules, not a determination for a real household",
        "Affiliated-housing lists, exact addresses and documents require checking","policy_extract")
    actual = [r for r in ctx.table("education_fees") if r["id"].startswith("FEE-ACTUAL-")]
    add("F05",f"All {len(actual)} frozen campus status rows lack a published 2026 charge; policy and approval evidence remain separate",
        [citation("education_fees",r["id"]) for r in ctx.table("education_fees")],
        [s for r in ctx.table("education_fees") for s in r["source_ids"]],
        "Do not interpret unknown payments as zero or calculate net household cost",
        "Meals, care, age, subsidy eligibility and fee deductions are incomplete","collection_status_and_policy")
    sensitivity = [r for r in ctx.table("walking_sensitivity") if r["coverage"]=="original_6" and
        r["category"]=="public_kindergartens" and r["threshold_min"]==10 and r["scenario"] in {"amap_baseline","slower_1.00"}]
    counts = {s:sum(r["sample_count"]>0 for r in sensitivity if r["scenario"]==s) for s in {"amap_baseline","slower_1.00"}}
    add("F06",f"Within six original kindergarten campuses, 10-minute public-campus coverage changes from {counts['amap_baseline']}/3 to {counts['slower_1.00']}/3 origins under a 1.00 m/s scenario",
        [citation("walking_sensitivity",r["id"]) for r in sensitivity],
        [r["source_id"] for r in sensitivity],"Scenario sensitivity, not observed child speeds or population coverage",
        "Restricted campus sample and no gate delays","constructed_sensitivity")
    plan = next(r for r in ctx.table("admission_plans") if r["subject_id"]=="INS-SCH-TH1")
    add("F07","Tianhe First Primary has one shared seven-class institution plan, not seven classes per campus",
        [citation("admission_plans",plan["id"]),citation("education_campuses","CAP-P04"),citation("education_campuses","CAP-P05")],
        [plan["source_id"]],"Institution total is not allocated to individual campuses",
        "Campus split not supplied","aggregation_boundary")
    invalid = [r for r in ctx.table("transport_routes") if not r["analytical_eligible"]]
    add("F08",f"{len(invalid)} archived route records are excluded from integrated analysis because of length or unresolved identity",
        [citation("transport_routes",r["id"]) for r in invalid],
        [r["source_id"] for r in invalid],"Archive retention does not imply analytical eligibility",
        "K7 legacy name and physical gates remain unresolved","quality_control")
