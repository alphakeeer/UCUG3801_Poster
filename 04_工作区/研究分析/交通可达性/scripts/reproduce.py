"""Reproduce derived tables from the archived Round 2 data and nine targeted Amap queries."""
import argparse
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "round-2" / "liede-accessibility-round-2.json"
OUT = ROOT / "data" / "round-3"
FIGURE = ROOT / "figures" / "figure-4-admission-channels-walking-time.png"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--round2", type=Path, default=DATA)
parser.add_argument("--no-figure", action="store_true")
args = parser.parse_args()
baseline = json.loads(args.round2.read_bytes())
supplement = json.loads((OUT / "supplementary-amap.json").read_bytes())
original = {(r["origin_id"], r["destination_id"]): r for r in baseline["routes"]}
homes = {"D1": "Liede Garden", "D2": "Zhonghai Jinghui Huating", "D3": "Nanguo Garden"}
matches = {"D1": "S1", "D2": "S3", "D3": "S4"}
public = {"K1", "K5", "K6", "K7", "K8"}
primary_policy = "https://www.thnet.gov.cn/attachment/8/8016/8016210/10791180.pdf"
points_policy = "https://www.thnet.gov.cn/gzjg/qzf/qjyj/zsks/content/post_10872346.html"
points_list = "https://www.thnet.gov.cn/attachment/8/8040/8040292/10872346.xls"
hk_policy = "https://www.thnet.gov.cn/gzjg/qzf/qjyj/zsks/content/post_10833283.html"
kg_policy = "https://www.thnet.gov.cn/gzjg/qzf/qjyj/zsks/content/post_10777181.html"
kg_plan = "https://www.thnet.gov.cn/gzjg/qzf/qjyj/zsks/content/post_10815546.html"

def write_csv(name, rows):
    with (OUT / name).open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def chord_m(a, b):
    lon1, lat1 = map(float, a.split(","))
    lon2, lat2 = map(float, b.split(","))
    return math.hypot((lon2 - lon1) * math.cos(math.radians((lat1 + lat2)/2)), lat2 - lat1) * 111195

new = {}
audit = []
for item in supplement["raw_routes"]:
    origin, dest = item["origin_id"], item["destination_id"]
    a, b = item["query_origin_gcj02"], item["query_destination_gcj02"]
    p = item["amap_response"]["route"]["paths"][0]
    d, s = float(p["distance"]), float(p["duration"])
    chord = chord_m(a, b)
    flag = d + 5 < chord
    url = f"https://uri.amap.com/navigation?from={a}&to={b}&mode=walk"
    row = dict(origin_id=origin, destination_id=dest, walking_meters=int(d), walking_seconds=int(s), query_date_cst=supplement["query_date_cst"], origin_gcj02=a, destination_gcj02=b,
               endpoint_chord_m_for_qa=round(chord, 1), quality="excluded_subchord_distance" if flag else ("provisional_address_match_map_legacy_name" if dest == "K7" else "amap_estimate_gate_unverified"),
               amap_poi_url=f"https://www.amap.com/place/{supplement['pois'][dest]['id']}", amap_walking_url=url, official_source=points_list if dest == "S5" else kg_plan)
    audit.append(row)
    if not flag:
        new[origin, dest] = row
assert len(original) == 30 and len(audit) == 9 and len(new) == 8
assert ("D3", "K7") not in new
write_csv("supplementary-route-audit.csv", audit)

routes = original | new
max_error = max(abs(r["walking_seconds"] - r["walking_meters"]/1.25) for r in original.values())
assert max_error <= 0.5, max_error
cases = {
    "amap_baseline": (None, 0, 0),
    "steady_1.25": (1.25, 0, 0),
    "slower_1.00": (1.00, 0, 0),
    "slower_0.80": (0.80, 0, 0),
    "gate_minus100": (1.25, -100, 0),
    "gate_plus100": (1.25, 100, 0),
    "gate_plus200": (1.25, 200, 0),
    "combined_stress": (1.00, 100, 90),
}
def seconds(route, speed, extra_m, delay_s):
    return route["walking_seconds"] if speed is None else max(0, route["walking_meters"] + extra_m)/speed + delay_s

thresholds = []
for d in homes:
    for coverage, pool in [
        ("original_6", original),
        ("add_k8", original | {k:r for k,r in new.items() if k[1] == "K8"}),
        ("add_k8_and_plausible_k7_routes", routes),
    ]:
        for category in ("all_kindergartens", "public_kindergartens", "original_primary"):
            choices = {
                dest: r for (origin,dest), r in pool.items() if origin == d and (
                    category == "all_kindergartens" and dest.startswith("K") or
                    category == "public_kindergartens" and dest in public or
                    category == "original_primary" and dest in {"S1","S2","S3","S4"})
            }
            for scenario, (speed, extra_m, delay_s) in cases.items():
                ts = {dest:seconds(r, speed, extra_m, delay_s) for dest,r in choices.items()}
                closest = min(ts, key=ts.get)
                for limit in (10, 15, 20):
                    reached = sorted(dest for dest,s in ts.items() if s <= limit*60)
                    thresholds.append(dict(origin_id=d, coverage=coverage, category=category, scenario=scenario, speed_mps=speed, added_distance_m=extra_m, added_delay_s=delay_s,
                                           threshold_min=limit, sample_count=len(reached), reachable_ids="|".join(reached), closest_id=closest, closest_minutes=round(ts[closest]/60,3)))
write_csv("threshold-sensitivity.csv", thresholds)

def route(d, dest):
    return routes.get((d, dest)) if dest else None

def nums(r, key):
    return r[key] if r is not None else None

def fare(r):
    t = r.get("amap_pc_morning_transit", {}) if r else {}
    if t.get("status") == "itinerary_returned":
        o = t["options"][t["preferred_index"]]
        return o["fare_cny"], o["time_minutes"]
    return None, None

def policy_row(d, profile, stage, dest, geo, rule, status, source):
    target, nearest = route(d, dest), route(d, geo)
    f, m = fare(target)
    delta = (target["walking_seconds"] - nearest["walking_seconds"])/60 if target and nearest else None
    return dict(origin_id=d, profile=profile, stage=stage, closest_in_original_sample=geo, geographic_baseline_walk_minutes=round(nearest["walking_seconds"]/60,3), school_for_policy_comparison=dest,
                eligibility_status=status, conditions=rule, comparison_route_walk_m=nums(target,"walking_meters"),
                comparison_route_walk_minutes=round(target["walking_seconds"]/60,3) if target else None,
                comparison_minus_geographic_baseline_walk_minutes=round(delta,3) if delta is not None else None,
                comparison_route_amap_0720_fare_cny=f, comparison_route_amap_0720_transit_minutes=m,
                affordability="unknown_household_budget_and_costs", actual_admission="unobserved", source_url=source)

scenarios = []
for d, s in matches.items():
    specs = [
        ("Tianhe_hukou_matching_full_home", s, "Catchment route subject to matching full ownership, actual address, unoccupied seat and verification; D2 also has the Xingguo capacity warning", "conditional_catchment_school", primary_policy),
        ("Guangzhou_hukou_eligible_renter", None, "No owned home in Guangzhou, sole address and accepted lease filing; non-Tianhe Guangzhou hukou also subject to 2026 filing cutoff and minimum lease term", "district_coordination_destination_unknown", primary_policy),
        ("Non_Guangzhou_approved_policy_care", None, "Policy-care category and residence evidence verified; address-linked school receives application; district allocates", "district_coordination_destination_unknown", primary_policy),
        ("Non_Guangzhou_approved_migrant_points", "S5", "Approved and publicly cleared for points intake; Xian Cun is one listed option, ranking and preferences apply", "one_verified_listed_option_not_assignment", points_policy),
        ("Eligible_HK_Macao_points", "S4", "Approved and publicly cleared for separate HK/Macao intake, ordered by points; Nanguo is named for grade 1", "named_school_for_separate_channel_not_assignment", hk_policy),
        ("Non_Guangzhou_no_public_channel_in_scope", None, "No verified policy-care or migrant-points route in this scenario; private primary admission requirements and costs still apply", "no_ordinary_sampled_public_route_identified", primary_policy),
    ]
    for profile,dest,rule,status,source in specs:
        scenarios.append(policy_row(d,profile,"primary_1",dest,s,rule,status,source))
    geo = {"D1":"K1","D2":"K2","D3":"K4"}[d]
    kpub = {"D1":"K1","D2":"K5","D3":"K6"}[d]
    for profile,rule,status in [
        ("Tianhe_hukou_eligible_owner", "Age and Tianhe hukou; public general lottery possible; priority only if specific affiliated campus, ownership and seat conditions verified", "general_lottery_plus_possible_campus_priority"),
        ("Tianhe_hukou_renter_no_ownership_priority", "Age and Tianhe hukou; may select one education-department kindergarten in general online lottery", "general_lottery_without_owner_priority"),
        ("Non_Guangzhou_approved_policy_care", "Age and document verification; policy-care condition permits public general lottery", "general_lottery_if_policy_care_verified"),
        ("Outside_Tianhe_hukou_no_policy_exception", "No identified general lottery pathway; private campus-specific registration, priority and fees to check", "public_general_lottery_criteria_not_met"),
    ]:
        scenarios.append(policy_row(d,profile,"kindergarten_small_class",None if profile.startswith("Outside") else kpub,geo,rule,status,kg_policy))
write_csv("household-scenarios.csv", scenarios)

commute = []
selected = [(d, k) for d, s in matches.items() for k in (s, "S5") + (("S4",) if s != "S4" else ())]
selected += [("D2","K2"),("D2","K5"),("D2","K6"),("D2","S2")]
for d, dest in selected:
    r = route(d,dest)
    s, dist = r["walking_seconds"], r["walking_meters"]
    f, t = fare(r)
    # Two legs with a child and two adult-only return legs, assuming a symmetric route.
    commute.append(dict(origin_id=d,destination_id=dest,one_way_amap_walk_minutes=round(s/60,3),days=5,escort_legs_per_day=2,
                        weekly_minutes_two_escort_legs_amap=round(10*s/60,3),
                        weekly_minutes_four_legs_amap=round(20*s/60,3),
                        weekly_minutes_four_legs_mixed_1mps_escort_1_25mps_solo=round(10*(dist+dist/1.25)/60,3),
                        amap_0720_one_way_transit_minutes=t, amap_0720_one_adult_boarding_cny=f,
                        scenario_weekly_fare_10_adult_boardings=10*f if f is not None else None,
                        scenario_weekly_fare_20_adult_boardings=20*f if f is not None else None))
write_csv("commute-burden-scenarios.csv", commute)

if not args.no_figure:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color":"#16344A"})
    fig,ax=plt.subplots(figsize=(11.8,5.9))
    fig.patch.set_facecolor("#F7F9FA")
    ax.set_facecolor("#F7F9FA")
    fig.text(.046,.91,"Admission channels change which walks matter",fontsize=24,weight="bold")
    fig.text(.047,.849,"Grade 1 in Tianhe, 2026  /  Amap walking estimates from three residential points",fontsize=11,color="#445C6A")
    markers = [("o","#06766D","Address-linked school"),("s","#8A4F78","Migrant-points example: Xian Cun Primary"),("D","#A34F19","HK/Macao points: Nanguo Primary")]
    for i,(d, school) in enumerate(matches.items()):
        y=2-i
        schools=[school,"S5","S4"]
        times=[route(d,k)["walking_seconds"]/60 for k in schools]
        ax.hlines(y,min(times),max(times),color="#C7D3D9",lw=2,zorder=1)
        for offset,value,(marker,color,_) in zip((.19,0,-.19),times,markers):
            ax.scatter(value,y+offset,color=color,marker=marker,s=90,zorder=3)
            ax.annotate(f"{value:.1f}",(value,y+offset),xytext=(8,0),textcoords="offset points",va="center",fontsize=10,color=color,weight="bold")
    ax.set(yticks=[2,1,0],yticklabels=list(homes.values()),xlim=(0,32.5),ylim=(-.55,2.55),xlabel="One-way walking time (minutes)")
    ax.set_xticks(range(0,31,5))
    ax.tick_params(axis="both", length=0, pad=8, labelsize=11, colors="#16344A")
    for spine in ax.spines.values(): spine.set_visible(False)
    ax.grid(axis="x", color="#DCE5E8")
    ax.legend(handles=[Line2D([0],[0],color=color,marker=marker,linestyle="",label=label,markersize=8) for marker,color,label in markers],
              loc="upper left",bbox_to_anchor=(0,1.17),frameon=False,ncol=3,fontsize=9.2,handletextpad=.35,columnspacing=1.2)
    fig.subplots_adjust(left=.227,right=.965,top=.724,bottom=.235)
    fig.text(.048,.087,"Xian Cun is one listed option. All routes use map points. Actual assignments and enrolment are unobserved.",fontsize=10,color="#445C6A")
    fig.text(.048,.051,"Sources: Amap, 12 Nov 2026; Tianhe District Education Bureau, 2026 admissions rules and points intake plans.",fontsize=9.2,color="#445C6A")
    fig.savefig(FIGURE, dpi=300)
    plt.close(fig)
print("original_routes",len(original),"new_raw",len(audit),"new_pass_length_check",len(new),"max_amap_speed_error_seconds",max_error)
for row in thresholds:
    if row["coverage"]=="original_6" and row["category"]=="public_kindergartens" and row["scenario"] in {"amap_baseline","slower_1.00","combined_stress"}:
        print(row["origin_id"],row["scenario"],row["threshold_min"],row["sample_count"],row["closest_minutes"])
