from __future__ import annotations

import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from .common import EDUCATION, HOUSING, TRANSPORT, Context, number, read_csv, stable_id
from .coordinates import position


def workbook_sheet(path: Path, sheet_name: str) -> list[list[str]]:
    """Read cached values without modifying the original Excel workbook."""
    ns = {"m":"http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with ZipFile(path) as archive:
        shared = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared = ["".join(t.text or "" for t in node.findall(".//m:t",ns))
                for node in ET.fromstring(archive.read("xl/sharedStrings.xml")).findall("m:si",ns)]
        sheets = ET.fromstring(archive.read("xl/workbook.xml")).findall("m:sheets/m:sheet",ns)
        index = next(i for i,s in enumerate(sheets,1) if s.get("name")==sheet_name)
        rows = ET.fromstring(archive.read(f"xl/worksheets/sheet{index}.xml")).findall("m:sheetData/m:row",ns)
        result = []
        for row in rows:
            values = {}
            for cell in row.findall("m:c",ns):
                value = cell.find("m:v",ns)
                text = value.text if value is not None else "".join(t.text or "" for t in cell.findall(".//m:t",ns))
                if cell.get("t")=="s" and text:
                    text = shared[int(text)]
                letters = "".join(c for c in cell.get("r") if c.isalpha())
                column = 0
                for c in letters:
                    column = column*26 + ord(c)-64
                values[column] = text or ""
            result.append([values.get(i,"") for i in range(1,max(values,default=0)+1)])
        return result


def add_crosswalk(ctx: Context, namespace: str, old_id: str, kind: str,
                  new_id: str, basis: str, status: str="matched",
                  confidence: str="high", candidate: str="", note: str="") -> dict:
    row = dict(id=stable_id("XW-",namespace,old_id,kind), namespace=namespace,
        source_record_id=old_id, entity_type=kind, entity_id=new_id,
        candidate_entity_id=candidate, match_status=status, confidence=confidence,
        match_basis=basis, note=note)
    ctx.table("entity_crosswalk").append(row)
    return row


def build_entities(ctx: Context):
    src = ctx.source_manager
    residences = read_csv(ctx.module/"config/residence_ids.csv")
    homes = {r["source_name"]:r for r in residences}
    raw_homes = ctx.csv(HOUSING/"猎德住房价格数据_2026-11-11.csv")
    grouped = {r["小区"]:r for r in ctx.csv(HOUSING/"猎德区域分析_逐小区分组.csv")}
    for r in residences:
        raw = next((x for x in raw_homes if x["小区"]==r["source_name"]),{})
        ctx.table("residences").append(dict(id=r["id"], name=r["display_name"],
            english_name=r["english_name"], source_name=r["source_name"],
            address=raw.get("地址","珠江新城平月路" if r["id"]=="RES018" else ""),
            housing_description=raw.get("住房/产权类别（仅有证据时分类）","交通研究记录为商品住宅；非产权登记"),
            construction_year_raw=raw.get("建筑年代",""),
            research_group=grouped.get(r["source_name"],{}).get("区域分析组","transport_only"),
            has_housing_sample=bool(raw), preferred_position_id="",
            housing_evidence_status="reported_platform_and_background" if raw else "housing_sample_missing",
            note="住宅开发项目层对象，不推定家庭收入或逐套权属"))
        if raw:
            add_crosswalk(ctx,"housing_csv",r["source_name"],"residence",r["id"],
                "冻结住房记录逐条登记；住宅项目对应不等于相同入口")
    ctx.homes = homes
    _housing_observations(ctx, raw_homes, homes)

    primary = [r for r in ctx.csv(EDUCATION/"数据/小学初中校区学段.csv") if r["stage"]=="小学"]
    kg = ctx.csv(EDUCATION/"数据/猎德及周边幼儿园候选.csv")
    institution_links = {r["source_record_id"]:r for r in read_csv(ctx.module/"config/institution_links.csv")}
    institutions = {}
    for r in kg+primary:
        legacy = r["record_id"]
        stage = "kindergarten" if r in kg else "primary"
        entity = "CAP-"+legacy
        link = institution_links.get(legacy,{})
        institution = link.get("institution_id") or "INS-"+r.get("institution_id",legacy)
        institutions.setdefault(institution,dict(id=institution,
            name=r["name"], linkage_status=link.get("match_status","official_institution_id" if stage=="primary" else "campus_specific_reference"),
            basis=link.get("match_basis","官方机构ID" if stage=="primary" else "不合并尚未证实同一机构的同名对象")))
        owner = r.get("organizer",r.get("ownership",""))
        ownership = "private" if owner=="民办" else "education_department" if owner=="教育部门办" else "public" if owner=="公办" else "other_department"
        source_id = r.get("source_id",r.get("address_source_id"))
        ctx.table("education_campuses").append(dict(id=entity,institution_id=institution,
            legacy_id=legacy,name=r["name"],campus_name=r.get("campus",r["name"]),stage=stage,
            ownership=ownership,organizer_raw=owner,
            inclusive_status=r.get("inclusive_raw") or "not_recorded",
            address=r["address"],address_year=r.get("address_year",r.get("year")),
            admission_year=2026,spatial_status=r["spatial_status"],
            preferred_position_id="",source_id=source_id,
            source_locator=r.get("admission_locator") or f"HTML row {r.get('html_row')}",
            verification_status="official_listing_campus_record",
            note="候选样本而非全域普查；学段与入学年级分开"))
        add_crosswalk(ctx,"education_csv",legacy,"campus",entity,"官方园校记录及学段独立保留")
    ctx.tables["institutions"] = list(institutions.values())
    ctx.education_raw = kg+primary
    for row in read_csv(ctx.module/"config/transport_entity_mapping.csv"):
        add_crosswalk(ctx,row["namespace"],row["source_record_id"],row["entity_type"],
            row["entity_id"],row["match_basis"],row["match_status"],row["confidence"],
            row["candidate_entity_id"],row["note"])
    ctx.transport_mapping = {r["source_record_id"]:r for r in ctx.table("entity_crosswalk") if r["namespace"]=="transport"}
    _positions(ctx)
    return ctx


def _housing_observations(ctx, rows, homes):
    src = ctx.source_manager
    for n,r in enumerate(rows,2):
        entity = homes[r["小区"]]["id"]
        path = str(HOUSING/"猎德住房价格数据_2026-11-11.csv")
        metrics = [
            ("market_reference_sale_cny_m2","平台参考价元/㎡","来源URL","cny_per_m2",r["参考月份"],"platform_reference"),
            ("sale_ask_cny_m2","挂牌单价元/㎡","挂牌来源URL","cny_per_m2",r["房源发布日期/页面时点"],"listing_example"),
            ("rent_cny_month","整租元/月","租金来源URL","cny_per_month","", "listing_example" if r["租赁面积㎡"] else "platform_rent_aggregate"),
            ("rent_cny_m2_month","租金元/㎡/月","租金来源URL","cny_per_m2_month","","listing_example"),
        ]
        for metric,field,urlfield,unit,period,kind in metrics:
            value = number(r[field])
            if value is None:
                continue
            source = src.reference(r[urlfield] or r["来源URL"],r["小区"]+" housing evidence",path,"commercial_platform")
            ctx.table("housing_observations").append(dict(id=stable_id("HOBS-",entity,metric,path,n),
                residence_id=entity,metric=metric,value=value,unit=unit,
                reference_period=period,observed_on="2026-11-11",area_m2=number(r["租赁面积㎡"] if metric.startswith("rent") else r["挂牌面积㎡"] if metric=="sale_ask_cny_m2" else ""),
                total_ask_cny=number(r["挂牌总价万元"])*10000 if metric=="sale_ask_cny_m2" and r["挂牌总价万元"] else None,
                evidence_type=kind,verification_status="reported_repository_extract",
                comparable_sale=entity not in {"RES001","RES017"},
                source_id=source,source_path=path,source_locator=f"CSV row {n}; {field}",
                conflict_status="unresolved_ownership_or_product" if entity in {"RES001","RES017"} and "sale" in metric else "no_adjudication",
                note=r["质量说明"]+"；查询日不等于成交日或参考时期"))
    workbook = HOUSING/"猎德住房价格数据_2026-11-11.xlsx"
    for n,row in enumerate(workbook_sheet(ctx.root/workbook,"Transactions")[2:],3):
        name,kind,date,total,area,value,layout,platform,url,note = row[:10]
        candidates = [r for r in homes.values() if r["display_name"]==name or (name=="凯旋新世界" and r["id"]=="RES005")]
        entity = candidates[0]["id"] if len(candidates)==1 else ""
        source = src.reference(url,name+" reported transaction",str(workbook),"commercial_platform")
        ctx.table("housing_observations").append(dict(id=stable_id("HOBS-",str(workbook),n),
            residence_id=entity,metric="platform_transaction_sale_cny_m2",value=number(value),unit="cny_per_m2",
            reference_period=date,observed_on="2026-11-11",area_m2=number(area),total_ask_cny=None,
            evidence_type="platform_reported_transaction",verification_status="reported_repository_extract",
            comparable_sale=False,source_id=source,source_path=str(workbook),source_locator=f"Transactions row {n}",
            conflict_status="requires_source_verification" if entity=="RES005" else "no_adjudication",
            note=f"{note}；平台转述，非政府交易登记；{layout}; total {total}万元"))


def _positions(ctx):
    src = ctx.source_manager
    paths = {"RES001":"https://mapcarta.com/W616267312", "RES003":"https://mapcarta.com/W515737466", "RES011":"https://mapcarta.com/W206602237"}
    for r in ctx.csv(HOUSING/"猎德住房价格数据_2026-11-11.csv"):
        if not r["经度WGS84"]:
            continue
        entity = ctx.homes[r["小区"]]["id"]
        source = src.reference(paths[entity],r["小区"]+" OSM reference",str(HOUSING/"猎德住房空间分布调查报告_2026-11-11.md"),"OSM_reference")
        ctx.table("positions").append(position("POS-H-"+entity,entity,
            "residential_phase_reference" if entity=="RES001" else "development_reference",
            float(r["经度WGS84"]),float(r["纬度WGS84"]),"WGS84",source,"housing CSV WGS84 fields",
            "repository_osm_reference", "仅五区参照，不是交通路线起点" if entity=="RES001" else "住宅项目参照点，非实际入口"))
    valid = {r["legacy_id"] for r in ctx.table("education_campuses")}
    for r in ctx.csv(EDUCATION/"地图/学校点位_WGS84.csv"):
        if r["record_id"] not in valid or not r["longitude"]:
            continue
        pending = r["record_id"]=="P03"
        entity = "CAP-"+r["record_id"]
        source = src.reference(r["source_url"],r["map_name"],str(EDUCATION/"地图/学校点位_WGS84.csv"),"OSM_feature")
        ctx.table("positions").append(position("POS-OSM-"+r["record_id"],"" if pending else entity,
            "campus_centroid" if "中心" in r["method"] else "campus_reference",float(r["longitude"]),float(r["latitude"]),
            "WGS84",source,r["record_id"],"provisional_alias" if pending else "repository_osm_reference",r["note"],entity if pending else ""))
    basepath = TRANSPORT/"data/round-2/liede-accessibility-round-2.json"
    baseline = json.loads((ctx.root/basepath).read_text())
    suppath = TRANSPORT/"data/round-3/supplementary-amap.json"
    supplement = json.loads((ctx.root/suppath).read_text())
    points = baseline["residential_points"]+baseline["education_points"]
    points += [dict(id=k,name=v["name"],longitude=float(v["location"].split(",")[0]),latitude=float(v["location"].split(",")[1]),
                    map_url="https://www.amap.com/place/"+v["id"],note=v["address"]) for k,v in supplement["pois"].items()]
    for r in points:
        mapping = ctx.transport_mapping[r["id"]]
        source = src.reference(r["map_url"],r["name"]+" Amap POI",str(basepath if r["id"] not in supplement["pois"] else suppath),"Amap_POI")
        ctx.table("positions").append(position("POS-AMAP-"+r["id"],mapping["entity_id"],
            "transport_origin_poi" if r["id"].startswith("D") else "transport_destination_poi",
            float(r["longitude"]),float(r["latitude"]),"GCJ-02",source,r["id"],
            "provisional_alias" if mapping["match_status"]!="matched" else "transformed_poi_estimate",
            mapping["note"]+"; "+str(r.get("note", "")),mapping["candidate_entity_id"]))
    select_positions(ctx)


def select_positions(ctx):
    positions = ctx.table("positions")
    priority = {"repository_osm_reference":0,"external_verified":1,"transformed_poi_estimate":2}
    for table in ["residences","education_campuses"]:
        for r in ctx.table(table):
            choices = [p for p in positions if p["entity_id"]==r["id"] and p["verification_status"] in priority]
            choices.sort(key=lambda p:(priority[p["verification_status"]],p["id"]))
            r["preferred_position_id"] = choices[0]["id"] if choices else ""
