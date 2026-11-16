"""把 OSM 底图与住宅、园校点位转成海报用的矢量地图数据 shared/mapdata.js。

坐标统一为 WGS84，投影为以研究区中心为原点的等距近似（单位：米，x 向东，y 向南），
在 3 km 范围内误差可忽略，比例尺可直接按米绘制。

    python3 tools/build_map_data.py
"""
import csv, gzip, json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))  # 04_工作区
SP = os.path.join(ROOT, "研究分析/图表与数据补充/ucug3801-housing-education-spatial/data")
OUT = os.path.join(HERE, "..", "shared", "mapdata.js")

LON0, LAT0 = 113.329, 23.122
KX = math.cos(math.radians(LAT0)) * 111320.0
KY = 110574.0
BBOX = (113.300, 23.104, 113.358, 23.140)  # 预留裁切余量


def proj(lon, lat):
    return (round((lon - LON0) * KX, 1), round(-(lat - LAT0) * KY, 1))


def inside(lon, lat, pad=0.0):
    w, s, e, n = BBOX
    return w - pad <= lon <= e + pad and s - pad <= lat <= n + pad


def dp(pts, tol):
    """Douglas–Peucker 简化。"""
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy)
    imax, dmax = 0, -1
    for i in range(1, len(pts) - 1):
        x, y = pts[i]
        d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / L if L > 1e-6 else math.hypot(x - x1, y - y1)
        if d > dmax:
            imax, dmax = i, d
    if dmax > tol:
        return dp(pts[: imax + 1], tol)[:-1] + dp(pts[imax:], tol)
    return [pts[0], pts[-1]]


def path(pts, close=False):
    s = "M" + "L".join(f"{x:g},{y:g}" for x, y in pts)
    return s + ("Z" if close else "")


def join_rings(segs):
    """把多段外环拼成闭合环。segs: list of [(lon,lat),...]"""
    segs = [list(s) for s in segs if len(s) > 1]
    rings = []
    while segs:
        ring = segs.pop(0)
        changed = True
        while ring[0] != ring[-1] and changed:
            changed = False
            for i, s in enumerate(segs):
                if s[0] == ring[-1]:
                    ring += s[1:]
                elif s[-1] == ring[-1]:
                    ring += s[::-1][1:]
                elif s[-1] == ring[0]:
                    ring = s[:-1] + ring
                elif s[0] == ring[0]:
                    ring = s[::-1][:-1] + ring
                else:
                    continue
                segs.pop(i)
                changed = True
                break
        rings.append(ring)
    return rings


ROAD_CLASS = {
    "motorway": "major", "trunk": "major", "primary": "major",
    "motorway_link": "secondary", "trunk_link": "secondary", "primary_link": "secondary",
    "secondary": "secondary", "secondary_link": "minor",
    "tertiary": "tertiary", "tertiary_link": "minor",
    "residential": "minor", "unclassified": "minor", "living_street": "minor", "pedestrian": "minor",
}

osm = json.load(gzip.open(os.path.join(SP, "osm_basemap_2026-11-12.json.gz")))["elements"]
roads = {k: [] for k in ("major", "secondary", "tertiary", "minor")}
road_named = {}
water, parks, bounds = [], [], []

for e in osm:
    t = e.get("tags", {})
    if e["type"] == "way" and "geometry" in e:
        g = [(p["lon"], p["lat"]) for p in e["geometry"]]
        if not any(inside(*p, pad=0.004) for p in g):
            continue
        hw = t.get("highway")
        if hw in ROAD_CLASS and t.get("tunnel") != "yes":
            cls = ROAD_CLASS[hw]
            pts = dp([proj(*p) for p in g], 2.5)
            roads[cls].append(path(pts))
            nm = t.get("name")
            if nm and cls in ("major", "secondary", "tertiary"):
                road_named.setdefault(nm, []).append(pts)
        elif t.get("leisure") == "park" and g[0] == g[-1]:
            parks.append(path(dp([proj(*p) for p in g], 2.0), True))
        elif t.get("natural") == "water" and g[0] == g[-1]:
            water.append(path(dp([proj(*p) for p in g], 2.0), True))
    elif e["type"] == "relation":
        outers = [[(p["lon"], p["lat"]) for p in m["geometry"]]
                  for m in e.get("members", []) if m.get("role") == "outer" and "geometry" in m]
        if t.get("natural") == "water":
            for r in join_rings(outers):
                if any(inside(*p, pad=0.02) for p in r):
                    water.append(path(dp([proj(*p) for p in r], 2.0), True))
        elif t.get("boundary") == "administrative":
            for r in join_rings(outers):
                bounds.append({"name": t.get("name"), "d": path(dp([proj(*p) for p in r], 3.0), True)})

# 道路名：取同名最长一段的中点与方向，供设计稿挑选标注
labels = {}
for nm, parts in road_named.items():
    best = max(parts, key=lambda p: sum(math.dist(p[i], p[i + 1]) for i in range(len(p) - 1)))
    L = sum(math.dist(best[i], best[i + 1]) for i in range(len(best) - 1))
    acc, half = 0.0, L / 2
    for i in range(len(best) - 1):
        seg = math.dist(best[i], best[i + 1])
        if acc + seg >= half:
            (x1, y1), (x2, y2) = best[i], best[i + 1]
            f = (half - acc) / (seg or 1)
            ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
            if ang > 90: ang -= 180
            if ang < -90: ang += 180
            labels[nm] = {"x": round(x1 + f * (x2 - x1)), "y": round(y1 + f * (y2 - y1)), "a": round(ang, 1), "len": round(L)}
            break
        acc += seg

# 住宅
houses = []
for r in csv.DictReader(open(os.path.join(SP, "housing_projects.csv"), encoding="utf-8-sig")):
    x, y = proj(float(r["longitude_wgs84"]), float(r["latitude_wgs84"]))
    p = r["map_price_wan_cny_m2"]
    houses.append({"id": r["map_code"], "name": r["name"].replace("（整盘）", ""), "nameEn": r["name_en"].split(" (")[0], "x": x, "y": y,
                   "price": float(p) if p else None, "status": r["map_price_status"],
                   "resettle": "回迁" in r["housing_type"]})

# 每个住宅 300/500/800 米内园校数（交接数据，EPSG:32649 计算）
near = {}
for r in csv.DictReader(open(os.path.join(SP, "campus_proximity.csv"), encoding="utf-8-sig")):
    near.setdefault(r["residence_id"], {})[r["radius_m"]] = int(r["total"])
ids = {r["map_code"]: r["residence_id"] for r in csv.DictReader(open(os.path.join(SP, "housing_projects.csv"), encoding="utf-8-sig"))}
for h in houses:
    n = near.get(ids[h["id"]], {})
    h["n300"], h["n500"], h["n800"] = n.get("300"), n.get("500"), n.get("800")

# 园校
SHORT = {"P04": "天河一小·华利", "P05": "天河一小·华穗"}
schools = []
for r in csv.DictReader(open(os.path.join(SP, "campuses.csv"), encoding="utf-8-sig")):
    x, y = proj(float(r["longitude_wgs84"]), float(r["latitude_wgs84"]))
    org = r["organizer_type"]
    kind = "primary" if r["stage"] == "primary" else "kg"
    sub = ("public" if org in ("public", "education_department", "other_department") else "private")
    nm = SHORT.get(r["map_code"], r["short_name"])
    schools.append({"id": r["map_code"], "name": nm, "x": x, "y": y, "kind": kind, "org": sub, "orgRaw": org})

# 三个路线起点与目的地（交通研究 D1–D3；坐标与上表同一 POI）
routes = {
    "origins": [{"id": "D1", "house": "R01"}, {"id": "D2", "house": "R15"}, {"id": "D3", "house": "R18"}],
    "local": {"D1": "P01", "D2": "P06", "D3": "P02"},
    "points": "P07",
    "sec": {"D1": [354, 1413], "D2": [605, 705], "D3": [166, 1706]},
}

data = {
    "origin": [LON0, LAT0],
    "roads": roads, "water": water, "parks": parks, "bounds": bounds, "labels": labels,
    "houses": houses, "schools": schools, "routes": routes,
    "attribution": "© OpenStreetMap contributors (ODbL) · 房天下 · 天河区教育局 · 高德",
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write("// 由 tools/build_map_data.py 生成，勿手改\nwindow.MAPDATA = ")
    json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    f.write(";\n")
print("roads", {k: len(v) for k, v in roads.items()}, "water", len(water), "parks", len(parks),
      "bounds", len(bounds), "houses", len(houses), "schools", len(schools),
      "size", os.path.getsize(OUT) // 1024, "KB")
print("labels:", sorted(labels, key=lambda k: -labels[k]["len"])[:30])
