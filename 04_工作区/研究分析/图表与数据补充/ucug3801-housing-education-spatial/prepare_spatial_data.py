import argparse
import csv
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from statistics import median

from pyproj import Transformer

parser = argparse.ArgumentParser()
parser.add_argument("source", type=Path, help="Checkout of integration commit 5101aa7")
parser.add_argument("output", type=Path)
parser.add_argument("--amap-input", type=Path, required=True)
args = parser.parse_args()
root, out = args.source, args.output
out.mkdir(parents=True, exist_ok=True)
data = out / "data"
data.mkdir(exist_ok=True)

def read(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def write(path, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fields)
        writer.writeheader()
        writer.writerows(rows)

def js(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

sha = "5101aa7ca61e0d2ddeff85a8209d9cf126a33508"
module = root / "06_数据整合"
base = module / "outputs" / "data"
housing_dir = root / "04_工作区/研究分析/房价分布"
old_homes = read(base / "residences.csv")
old_prices = read(housing_dir / "猎德住房价格数据_2026-11-11.csv")
old_obs = read(base / "housing_observations.csv")
old_points = {x["id"]: x for x in read(base / "positions.csv")}
sources = {x["id"]: x for x in read(base / "source_registry.csv")}
amap = js(args.amap_input)
src = importlib.util.spec_from_file_location("coordinates", module / "src/liede_pipeline/coordinates.py")
coords = importlib.util.module_from_spec(src)
src.loader.exec_module(coords)
scope = {"full": [113.308, 23.108, 113.370, 23.1355], "poster": [113.308, 23.108, 113.3485, 23.1355]}
transformer = Transformer.from_crs(4326, 32649, always_xy=True)

def in_scope(lon, lat, extent):
    w, s, e, n = scope[extent]
    return w <= float(lon) <= e and s <= float(lat) <= n

def position(key, poi):
    lon, lat = map(float, poi["location"].split(","))
    wgs_lon, wgs_lat = coords.gcj02_to_wgs84(lon, lat)
    recovered = coords.wgs84_to_gcj02(wgs_lon, wgs_lat)
    assert max(abs(lon-recovered[0]), abs(lat-recovered[1])) < 2e-8
    return dict(position_id="HES-AMAP-"+key, map_name=poi["name"], map_alias=poi.get("alias", ""),
                map_address=poi["address"], coordinate_type="project_or_campus_poi",
                raw_longitude=lon, raw_latitude=lat, raw_crs="GCJ-02",
                longitude_wgs84=wgs_lon, latitude_wgs84=wgs_lat, map_crs="EPSG:4326",
                transform="gcj_iterative_inverse_v1", poi_id=poi["id"], coordinate_checked="2026-11-13",
                coordinate_source_url=f"https://uri.amap.com/marker?position={lon},{lat}&name={poi['id']}")

official = "https://www.thnet.gov.cn/attachment/8/8016/8016210/10791180.pdf"
district_kg = {"education_department":"https://www.thnet.gov.cn/gzjg/qzf/qjyj/zsks/content/post_10815546.html",
               "other_department":"https://www.thnet.gov.cn/gzjg/qzf/qjyj/zsks/content/post_10815974.html",
               "private":"https://www.thnet.gov.cn/gzjg/qzf/qjyj/zsks/content/post_10815624.html"}
housing_match = {
    1: ("猎德大道20号（平台）／海文路7号（高德）", "same_project_different_reference", "海文路高德项目POI。原五区 WGS84 参照保留，勿互换为实际楼栋或通学门。"),
    2: ("金穗路70号（物业）／兴盛路9号（高德）", "same_project_multiple_frontages", "物业确认金穗路70号。高德按金穗路70号加小区名称地理编码返回与保利·心语项目POI完全相同的坐标。"),
    3: ("花城大道86号（房天下）／兴民路221号（高德）", "same_project_multiple_frontages", "采用高德项目POI；官方2026地段以花城大道列名。旧 OSM 项目参考点另保留。"),
    5: ("珠江新城清风街（多期）", "same_development_aggregate", "房天下2811048273聚合含一期/枫丹丽舍等，采用凯旋新世界整盘POI，不赋值给广粤观邸某一期。"),
    6: ("兴盛路6号", "alias_confirmed", "君御雅苑即尚东君御，房天下住宅页2811218224及高德alias相互支持。商铺页2811212568独立。"),
    8: ("金穗路711号", "alias_confirmed", "高德誉峰园与房天下誉峰同门牌。"),
    9: ("兴盛路10号", "name_address_match", "保留高德和房天下隽峰苑；2026地段表用字不作为本项目改名依据。"),
    10: ("兴盛路7号", "alias_confirmed", "高德领峰／合景领峰园。同名近似的岭峰园返回不同位置，排除。"),
    11: ("兴民路160号（原表）／冼村路80号（高德）", "same_project_multiple_frontages", "2026地段表按兴民路列名；项目POI在冼村路一侧。旧 OSM 项目参照另保留。"),
    12: ("华利路25号", "alias_confirmed", "都荟华庭/珠江都荟华庭与珠江都荟同项目。排除珠江·天河都荟。"),
    14: ("花城大道126–136号（双号）", "name_address_match", "使用颐德公馆（住宅）参考价，别墅记录单独。"),
    15: ("猎德大道31号（高德）／33号（房天下、管理处）", "same_project_multiple_frontages", "保留项目点、交通起点和管理处的独立角色。"),
    16: ("海清路3–19号（单号）", "same_project_multiple_phases", "高德海清路9号社区点为项目参考。含南、北区，指定人才配租为另外一项。"),
    18: ("平月路161号（房天下走势页）", "same_project_multiple_frontages", "房天下同项目ID的二手房页用马场西路。高德项目POI平月路，勿与尚东宏御合并。"),
    19: ("临江大道399号（房天下）／411号（高德）", "same_project_multiple_phases", "补南侧沿江较早商品住宅。高德项目、南区与北区别名并存；采用项目点，月报值另列。"),
    20: ("海安路9号", "official_resettlement_and_amap", "补北侧石牌回迁房。官方地段附件第38项并列凤凰苑、龙胜苑；高德门牌分开。"),
    21: ("海安路7号", "official_resettlement_and_amap", "补北侧石牌回迁房。只采用海安路7号高德结果，排除临江大道附近的同名候选。"),
    22: ("华利路27号", "name_address_match", "补西侧华利路的同平台可比住宅。按房天下住宅项目收录，旅馆POI排除。"),
}
address_refs = {
    2: "https://www.polywuye.com/City/iteminfo/52/133",
    5: "https://cms.nwd.com.hk/downloadIR/newsletter/58/New%20World%20Development%20-%20ARTISANAL%20CONNECT_Feb%202025_SC_final_1_0.pdf",
    6: "https://ganzhou.esf.fang.com/loupan/2811218224/housedetail.htm",
    12: "https://www.gzzjgf.com/static/upload/2024/10/15/202410156771.pdf",
    18: "https://fangjia.fang.com/gz/process/2811017236.htm",
    19: "https://sthjj.gz.gov.cn/attachment/7/7407/7407450/9145902.pdf",
}
new_prices = {
    18: ("90272", "2026-09", "https://www.fang.com/xiaoqu/gz-2811017236/", "fang_monthly_community_reference"),
    19: ("104778", "2026-08", "https://m.fang.com/news/gz/13202_55063314.html", "fang_monthly_market_report_average"),
    22: ("82491", "2026-08", "https://www.fang.com/xiaoqu/gz-2811672798/", "fang_monthly_community_reference"),
}
new_homes = {
    19: ("新城海滨花园", "New City Haibin Garden", "普通住宅，2000年建成（房天下）"),
    20: ("凤凰苑", "Fenghuang Court", "石牌回迁房（官方地段附件分类）"),
    21: ("龙胜苑", "Longsheng Court", "石牌回迁房（官方地段附件分类）"),
    22: ("广弘天琪", "Guanghong Tianqi", "住宅，70年（房天下）；产权以逐套资料为准"),
}
homes = []
price_log = []
location_deltas = []
for n in range(1, 23):
    key = f"RES{n:03}"
    legacy = old_homes[n-1] if n <= 18 else {}
    old_price = old_prices[n-1] if n <= 17 else {}
    raw = amap[key]
    poi = amap["RES005-COMPLEX"] if n == 5 else raw
    a, match, note = housing_match.get(n, (legacy.get("address", poi["address"]), "name_address_match", "项目名称和主要地址匹配。"))
    name, en, kind = new_homes.get(n, (legacy.get("name"), legacy.get("english_name"), legacy.get("housing_description")))
    if n == 1:
        en = "Liede Garden"
    if n == 5:
        name, en = "凯旋新世界（整盘）", "New World Garden (all phases)"
    prior_value = old_price.get("平台参考价元/㎡", "")
    prior_month = old_price.get("参考月份", "")
    prior_url = old_price.get("来源URL", "")
    value, month, url, metric = new_prices.get(n, (prior_value, prior_month, prior_url, "fang_monthly_community_reference"))
    if n == 12:
        metric = "fang_resale_listing_page_average"
    if n in {20, 21}:
        value = month = url = metric = ""
    status = ("comparable" if metric == "fang_monthly_community_reference" and value and n not in {1, 17}
              else "product_not_comparable" if n in {1, 17} else "other_price_metric" if value else "comparable_price_missing")
    check = ("publisher_match_month_and_value" if value and n not in {12, 19} else
             "publisher_match_page_listing_average" if n == 12 else "publisher_report_match_month_and_value" if n == 19 else
             "comparable_price_not_found")
    confirm = "https://m.fang.com/news/gz/13202_55186898.html" if n == 3 else url
    label_month = month[:7] if month else ""
    p = position(key, poi)
    prior_pos = old_points.get(legacy.get("preferred_position_id"), {})
    delta = ""
    if prior_pos:
        delta = round(coords.chord_m(float(prior_pos["longitude"]), float(prior_pos["latitude"]),
            p["longitude_wgs84"], p["latitude_wgs84"]), 1)
        location_deltas.append(dict(entity_id=key, purpose="previous_repository_point_retained",
            old_position_id=prior_pos["id"], old_role=prior_pos["position_role"],
            old_raw_longitude=prior_pos["original_longitude"], old_raw_latitude=prior_pos["original_latitude"],
            old_raw_crs=prior_pos["original_crs"], old_longitude_wgs84=prior_pos["longitude"], old_latitude_wgs84=prior_pos["latitude"],
            old_source_url=sources[prior_pos["source_id"]].get("url"), new_position_id=p["position_id"], delta_m=delta))
    if n == 5:
        phase = position("RES005-PHASE", raw)
        location_deltas.append(dict(entity_id=key, purpose="phase_poi_not_used_for_development_price",
            old_position_id=phase["position_id"], old_role="phase_poi", old_raw_longitude=phase["raw_longitude"],
            old_raw_latitude=phase["raw_latitude"], old_raw_crs=phase["raw_crs"], old_longitude_wgs84=phase["longitude_wgs84"],
            old_latitude_wgs84=phase["latitude_wgs84"], old_source_url=phase["coordinate_source_url"],
            new_position_id=p["position_id"], delta_m=round(coords.chord_m(phase["longitude_wgs84"], phase["latitude_wgs84"],
                p["longitude_wgs84"], p["latitude_wgs84"]),1)))
    price_id = next((x["id"] for x in old_obs if x["residence_id"]==key and x["metric"]=="market_reference_sale_cny_m2"), "")
    row = dict(residence_id=key, map_code=f"R{n:02}", name=name, name_en=en, sample_status="existing" if n <= 18 else "supplement",
        source_address=legacy.get("address", ""), adjudicated_address=a, housing_type=kind, research_group=legacy.get("research_group", ""),
        match_status=match, match_note=note, address_source_url=address_refs.get(n, official if n in {20,21} else url), **p,
        previous_point_delta_m=delta, source_price_observation_id=price_id,
        source_price_metric=old_price.get("价格口径", ""), observed_price_cny_m2=value,
        price_metric=metric, price_period=label_month, price_period_original=month,
        price_platform="房天下" if value else "", price_source_url=url, price_recheck_url=confirm,
        price_recheck_date="2026-11-13", price_recheck_status=check, map_price_status=status,
        map_price_cny_m2=value if status=="comparable" else "",
        map_price_wan_cny_m2=f"{float(value)/10000:.2f}" if status=="comparable" else "",
        in_full_map=in_scope(p["longitude_wgs84"], p["latitude_wgs84"], "full"),
        in_poster_map=in_scope(p["longitude_wgs84"], p["latitude_wgs84"], "poster"))
    homes.append(row)
    price_log.append(dict(residence_id=key, previous_value_cny_m2=prior_value, previous_period=prior_month, previous_url=prior_url,
        checked_value_cny_m2=value, checked_reference_period=month, price_type=metric, status=check,
        citation_url=confirm, second_source_url=url, checked_on="2026-11-13",
        matched_label=("09月参考价；移动端其他时点可变化" if n==18 else "09月参考价；同平台另一页面同时显示11月，固定保留原可回核页面" if n==16 else
            "二手房挂牌页显示均价，按原调查分类" if n==12 else "2026年8月均价；月报统计方法未确认一致" if n==19 else
            "公开同源页面的金额与月份标签" if value else "未找到同口径可用销售参考价")))
assert len(homes)==22 and all(h["in_full_map"] and h["in_poster_map"] for h in homes)

orig_campuses = read(module / "outputs/figure_source_data/figure_A_campuses.csv")
new_match_notes = {
    "CAP-E004-041":"高德员村西街1号之24–41；官方1号大院41号，同一园。",
    "CAP-E004-042":"园区全名匹配。高德东璟花园1–2号与官方东璟街2号口径有差异，园区POI，门址未核。",
    "CAP-E005-015":"广州数科集团幼儿园与名录广州数字科技集团有限公司幼儿园简称匹配，7号大院66号相同。",
    "CAP-E006-024":"同名与员村二横路都市兰亭小区匹配，官方25号与高德A4栋旁并存。",
    "CAP-E006-060":"官方园区与马场路519号匹配，高德地图类别较粗，以官方民办幼儿园分类为准。",
    "CAP-E006-061":"同址，地图旧称南雅苑托儿所，alias为育星南雅幼儿园。只用于建筑级地图。",
    "CAP-E006-108":"海乐路13号和核心名称匹配，高德追加海乐路，排除都市兰亭园。",
    "CAP-E006-114":"兴盛路8号同楼，官方三层301与地图118并存；只按同楼园区POI制图。",
}
campuses = []
for n, old in enumerate(orig_campuses,1):
    key = old["id"]
    name = old["name"].removeprefix("广州市").removeprefix("天河区").removeprefix("广州市")
    if key=="CAP-P04": name="天河第一小学·华利"
    if key=="CAP-P05": name="天河第一小学·华穗"
    name = name.removesuffix("有限公司")
    code = ("P"+key[-2:]) if old["stage"]=="primary" else f"G{n:02}"
    if old["longitude"]:
        old_p = old_points[old["preferred_position_id"]]
        p = dict(position_id=old_p["id"], map_name="", map_alias="", map_address="", coordinate_type=old_p["position_role"],
            raw_longitude=old_p["original_longitude"], raw_latitude=old_p["original_latitude"], raw_crs=old_p["original_crs"],
            longitude_wgs84=float(old["longitude"]), latitude_wgs84=float(old["latitude"]), map_crs="EPSG:4326", transform=old_p["transform"],
            poi_id="", coordinate_checked="", coordinate_source_url=sources[old_p["source_id"]].get("url") or sources[old_p["source_id"]].get("local_path"),
            position_origin="integration_accepted", match_status=old["coordinate_status"], match_note=old_p["note"])
    elif key in amap:
        p = position(key, amap[key])
        p.update(position_origin="new_amap_match", match_status="same_campus_building_reference" if key in new_match_notes else "official_name_address_match",
            match_note=new_match_notes.get(key, "2026官方园校名称和地址与高德结果相符。门点未核。"))
    else:
        p = dict(position_origin="unresolved", match_status="unresolved", match_note="未获得足以采用的点位。")
    lon, lat = p.get("longitude_wgs84"), p.get("latitude_wgs84")
    row = dict(campus_id=key, institution_id=old["institution_id"], map_code=code, name=old["name"], short_name=name,
        official_address=old["address"], stage=old["stage"], organizer_type=old["ownership"],
        organizer_raw=old["organizer_raw"], inclusive_status=old["inclusive_status"], listing_year=old["admission_year"],
        official_url=official if old["stage"]=="primary" else district_kg[old["ownership"]], official_locator=old["source_locator"], upstream_legacy_id=old["legacy_id"], **p,
        in_full_map=bool(lon and in_scope(lon, lat, "full")), in_poster_map=bool(lon and in_scope(lon, lat, "poster")))
    campuses.append(row)
    audit_poi = amap.get("AUDIT-"+key.removeprefix("CAP-"))
    if audit_poi:
        audit = position(key+"-AUDIT",audit_poi)
        row.update(alternate_poi_id=audit["poi_id"], alternate_map_address=audit["map_address"],
            alternate_raw_longitude=audit["raw_longitude"], alternate_raw_latitude=audit["raw_latitude"],
            alternate_raw_crs=audit["raw_crs"], alternate_longitude_wgs84=audit["longitude_wgs84"],
            alternate_latitude_wgs84=audit["latitude_wgs84"], alternate_map_url=audit["coordinate_source_url"],
            alternate_distance_m=round(coords.chord_m(float(lon),float(lat),audit["longitude_wgs84"],audit["latitude_wgs84"]),1))
        if key=="CAP-P02":
            row["match_note"] += " 高德小学部写平月路200号，官方校址为202号；采用原校区参考，保留高德补查点。"
        if key=="CAP-P12":
            row["match_note"] += " 官方整合地址员村一横路29号，高德学校点写员村南街自编11号；位置接近，保留原采纳坐标及差异。"
    if key == "CAP-E004-036":
        row["match_note"] += " 名录园区旧地图别名已关联，D3异常路线仍排除。"

write(data / "housing_projects.csv", homes)
write(data / "campuses.csv", campuses)
write(data / "price_rechecks.csv", price_log)
write(data / "prior_coordinate_crosswalk.csv", location_deltas)
obs = []
for old in old_obs:
    r = dict(old)
    r["source_url"] = sources[old["source_id"]].get("url", "")
    r["current_scope_status"] = "archived_original"
    if old["id"] == homes[11]["source_price_observation_id"]:
        r.update(metric="platform_listing_page_average_cny_m2", previous_metric=old["metric"], comparable_sale="false",
                 current_scope_status="metric_corrected_keep_original_id")
    obs.append(r)
for n,(v,month,url,metric) in new_prices.items():
    obs.append(dict(id=f"HES-PRICE-RES{n:03}",residence_id=f"RES{n:03}",metric=metric,value=v,unit="cny_per_m2",
        reference_period=month,observed_on="2026-11-13",evidence_type="publisher_reference", verification_status="publisher_rechecked",
        comparable_sale="true" if n != 19 else "false", source_id=f"HES-PRICE-SRC-{n:03}", source_url=url,
        source_locator="项目小区参考价" if n!=19 else "2026年8月月报正文", current_scope_status="supplement",
        note="房天下小区参考价或房价月报均值；不同类型分别保留。"))
write(data / "housing_price_observations.csv", obs)

def point(r):
    return transformer.transform(float(r["longitude_wgs84"]),float(r["latitude_wgs84"]))

bands = [0,8,10,12,14,20]
radii = [300,500,800]
categories = [("primary","public"),("primary","private"),("kindergarten","education_department"),
              ("kindergarten","other_department"),("kindergarten","private")]
nearby = []
pairs = []
for h in homes:
    x, y = point(h)
    distances = []
    for c in campuses:
        if not c.get("longitude_wgs84"):
            continue
        u,v = point(c)
        dist = math.hypot(u-x,v-y)
        distances.append((dist,c))
        if dist <= max(radii):
            pairs.append(dict(residence_id=h["residence_id"],campus_id=c["campus_id"],stage=c["stage"],organizer_type=c["organizer_type"],
                distance_m=round(dist,3),campus_position_origin=c["position_origin"]))
    for rad in radii:
        counts = Counter((c["stage"], c["organizer_type"]) for dist,c in distances if dist<=rad)
        nearby.append(dict(residence_id=h["residence_id"], radius_m=rad, price_cny_m2=h["map_price_cny_m2"],price_period=h["price_period"],
            primary_public=counts[categories[0]],primary_private=counts[categories[1]],kg_education_department=counts[categories[2]],
            kg_other_department=counts[categories[3]],kg_private=counts[categories[4]], total=sum(counts.values()),
            nearest_primary_m=round(min(d for d,c in distances if c["stage"]=="primary")),
            nearest_kg_m=round(min(d for d,c in distances if c["stage"]=="kindergarten"))))
write(data / "campus_proximity.csv", nearby)
write(data / "proximity_pairs_within_800m.csv", pairs)
summary = []
for period in ("all_reference_months","2026-09"):
    for radius in radii:
        for group, lower, upper in (("below_100000",0,100000),("at_least_100000",100000,float("inf"))):
            sample = [r for r in nearby if r["radius_m"]==radius and r["price_cny_m2"]
                      and lower <= float(r["price_cny_m2"]) < upper and (period=="all_reference_months" or r["price_period"]==period)]
            stats = {key+"_median":median(r[key] for r in sample) for key in ("total","primary_public",
                     "primary_private","kg_education_department","kg_other_department","kg_private")}
            summary.append(dict(reference_period=period,radius_m=radius,price_group=group,n=len(sample),**stats))
write(data / "price_proximity_summary.csv",summary)
write(data / "map_layers.csv",[dict(map=name, layer="housing" if "residence_id" in r else "education", entity_id=r.get("residence_id",r.get("campus_id")),
    map_code=r["map_code"],longitude_wgs84=r["longitude_wgs84"],latitude_wgs84=r["latitude_wgs84"],
    price_wan_cny_m2=r.get("map_price_wan_cny_m2",""),class_code=r.get("map_price_status",r.get("organizer_type")))
    for name in scope for r in homes+campuses if r[f"in_{name}_map"]])
save_json(data / "map_scope.json",dict(bounds_order=["west","south","east","north"],bounds_wgs84=scope,comparison_crs="EPSG:32649",
    reference_price_bands_wan_cny_m2=bands,buffer_radii_m=radii,study_unit="project POI and official campus POI",upstream_commit=sha,
    price_checked="2026-11-13",osm_snapshot_date="2026-11-12"))
print("campuses",Counter((r["stage"],r["position_origin"]) for r in campuses))
print("figure coverage", {f:dict(Counter(r["stage"] for r in campuses if r[f"in_{f}_map"])) for f in scope})
print("price",Counter((h["map_price_status"],h["price_period"]) for h in homes))

