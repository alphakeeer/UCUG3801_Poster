"""GPT Work 2026-11-13 原格式补证的显式、可追溯适配器。

核验标签原样保留；不把整份 CSV 提升为已核实事实，不重新访问外部网站。
"""

import json
from pathlib import Path

from .common import TRANSPORT, digest, read_csv
from .coordinates import chord_m, position
from .entities import add_crosswalk, select_positions
from .transport import _route

WORK = Path("04_工作区/研究分析/定向证据补全/2026-11-13")
CORE = ["CAP-E004-052", "CAP-E004-053", "CAP-E004-054", "CAP-E004-036"]
SUBJECTS = {
    "A01":["RULE-K1-2026"], "A02":["RULE-K1-2026"], "A03":["RULE-K1-2026"],
    "A04":[CORE[0]], "A05":[CORE[1]], "A06":[CORE[2]], "A07":[CORE[3]],
    "A08":["RES001",CORE[0]], "A09":[CORE[2]], "A10":["RES018",CORE[3]],
    "A11":["RULE-P1-2026"], "A12":["RULE-P1-2026"],
    "A13":["RES001","RES015","RES018","CAP-P01","CAP-P06","CAP-P02"],
    "A14":["RULE-K1-2026"], "A15":[CORE[0]], "A16":[CORE[0],CORE[2],CORE[3]],
    "F01":["RULE-K1-2026"], "F02":["RULE-K1-2026"], "F03":["RULE-K1-2026"],
    "F04":[CORE[0]], "F05":[], "F06":CORE, "F07":[], "F08":["RULE-K1-2026"],
    "F09":[CORE[0]], "F10":[CORE[0]],
    **{key:["RES018"] for key in ["H01","H02","H03","H04","H05","H11"]},
    **{key:["RES001"] for key in ["H06","H07","H08"]},
    "H09":["RES015"], "H10":["RES015"],
    "G01":[CORE[3]], "G02":["CAP-P01"], "G03":["RES018","CAP-P02"],
    "G04":["CAP-E005-032"], "G05":["CAP-E006-072"],
    "G06":["RES001","CAP-E005-032"], "G07":["RES015","CAP-E005-032"],
    "G08":["RES018","CAP-E006-072"],
}


def prepare_work(ctx):
    """登记完整补证包；K7 人工映射变更须通过同址、同 POI 的证据门槛。"""
    path = WORK/"verified-facts.csv"
    rows = read_csv(ctx.root/path)
    assert len(rows)==45 and {r["evidence_id"] for r in rows}==set(SUBJECTS)
    archives = [ctx.source_manager.archive_local(str(p.relative_to(ctx.root)),
        "GPT Work 补证包："+p.name,"gpt_work_evidence_snapshot")
        for p in sorted((ctx.root/WORK).iterdir()) if p.is_file()]
    amap = json.loads((ctx.root/WORK/"amap-targeted-checks.json").read_text())
    results = amap["poi_searches"][:2]
    assert all(r["first_result"]["id"]=="B00141TQB7" for r in results)
    assert amap["poi_details"]["k7"]["address"].startswith("南国一街9号")
    old = json.loads((ctx.root/TRANSPORT/"data/round-3/supplementary-amap.json").read_text())["pois"]["K7"]
    assert old["id"]==amap["poi_details"]["k7"]["id"] and old["location"]==amap["poi_details"]["k7"]["location"]
    assert next(r for r in rows if r["evidence_id"]=="G01")["verification_status"]=="官方地址加地图交叉支持"
    official = next(r for r in ctx.csv(Path("03_背景/教育专题/数据/猎德及周边幼儿园候选.csv")) if r["record_id"]=="E004-036")
    assert "第二实验" in official["name"] and "南国一街9号" in official["address"]
    for n,r in enumerate(rows,2):
        key = r["evidence_id"]
        refs = [ctx.source_manager.reference(url.strip(),r["object_name"]+"："+r["fact_field"],
            str(path),"gpt_work_reported_reference") for url in r["source_urls"].split(" | ") if url.strip()]
        action = ("追加逐条住房挂牌，不进入小区参考价或均价" if key in {"H02","H03","H11"}
            else "接入点位、显式别名映射或补充路线" if key.startswith("G") and key!="G02" and key!="G03"
            else "与已有招生计划交叉核对，原计划不重复追加" if key in {"A04","A05","A06","A07"}
            else "保留为缺失，不填数值" if not r["value_or_rule"]
            else "仅保留政策推定或历史证据，禁止当作2026实际收费" if key in {"F07","F09","F10"}
            else "仅保留平台索引或版本冲突线索，不写入同口径价格" if key in {"H01","H04"}
            else "保留机构层预算或历史介绍，不下分到K7园区" if key=="F05"
            else "追加有原核验标签和年份的证据注释")
        ctx.table("work_evidence").append(dict(id="WORK-"+key,original_evidence_id=key,**r,
            subject_ids=SUBJECTS[key],entity_resolution="unresolved_institution" if key in {"F05","F07"} else "explicit_reviewed_mapping",
            source_ids=refs,snapshot_source_ids=archives,input_file=str(path),input_sha256=digest(ctx.root/path),
            input_row=n,integration_action=action,
            verification_boundary="沿用GPT Work声明；本流水线核对仓库原件与字段一致性，未重新联网核验"))
    ctx.work_rows = {r["original_evidence_id"]:r for r in ctx.table("work_evidence")}
    ctx.work_amap = amap


def integrate_work(ctx):
    """只将证据充分的字段转换为领域记录，其余仍可在补证表完整检索。"""
    for r in ctx.table("work_evidence"):
        if r["topic"]=="招生" and r["value_or_rule"]:
            for subject in r["subject_ids"]:
                kind = "rule" if subject.startswith("RULE-") else "campus" if subject.startswith("CAP-") else "residence"
                ctx.table("admission_evidence").append(dict(id=r["id"]+"-"+subject,
                    subject_id=subject,subject_type=kind,stage="primary" if r["original_evidence_id"] in {"A11","A12","A13"} else "kindergarten",
                    reference_period=r["applicable_year_or_period"],claim=r["value_or_rule"],
                    source_id=r["source_ids"][0],source_ids=r["source_ids"],source_locator=r["source_locator"],
                    verification_status=r["verification_status"],work_evidence_id=r["id"],note=r["notes"]))
        if not r["value_or_rule"] or r["verification_status"] in {"未核实","仅索引且版本冲突","仅索引"}:
            ctx.gap("WORK_UNRESOLVED","P0",r["id"],r["fact_field"]+"："+(r["value_or_rule"] or "未取得可采用值"),r["notes"],r["source_ids"])
    _conditions(ctx)
    _housing(ctx)
    _positions_and_routes(ctx)
    _fee_context(ctx)
    for key,campus,values in [("A04",CORE[0],[135,85,50]),("A05",CORE[1],[45,0,45]),
                             ("A06",CORE[2],[68,23,45]),("A07",CORE[3],[68,24,44])]:
        metrics=["social_lottery_total","owner_children_places","remaining_random_places"]
        plans=[next(p for p in ctx.table("admission_plans") if p["subject_id"]==campus and p["metric"]==metric) for metric in metrics]
        assert [p["value"] for p in plans]==values
        ctx.table("plan_corroboration").append(dict(id="CHECK-WORK-"+key,campus_id=campus,
            work_evidence_id="WORK-"+key,plan_ids=[p["id"] for p in plans],
            source_ids=ctx.work_rows[key]["source_ids"],result="与原三类计划一致，不追加计划数值"))
    # D2只确认项目层对应；多个门牌的独立位置角色继续保留。
    x = next(r for r in ctx.table("entity_crosswalk") if r["namespace"]=="transport" and r["source_record_id"]=="D2")
    x.update(confidence="high",match_basis=x["match_basis"]+"；WORK-H09/H10同名项目及历史官方门牌交叉支持")
    x["source_ids"]=sorted(set(ctx.work_rows["H09"]["source_ids"]+ctx.work_rows["H10"]["source_ids"]))
    x = next(r for r in ctx.table("entity_crosswalk") if r["namespace"]=="transport" and r["source_record_id"]=="K7")
    x["source_ids"]=ctx.work_rows["G01"]["source_ids"]
    select_positions(ctx)


def _conditions(ctx):
    entries = [
        ("A01","RULE-K1-2026","general_lottery","2022-09-01至2023-08-31出生；天河户籍或符合政策性照顾的非穗籍；网上选一园","可报名一般派位；未保证录取"),
        ("A02","RULE-K1-2026","affiliated_owner","本区户籍、对应住宅及产权和学位占用材料均符合规定","配套业主优先路径；具体覆盖楼栋未核"),
        ("A03","RULE-K1-2026","owner_over_capacity","合格业主超过总计划时在业主类别内派位或摇珠","90%为社会派位招生比例，非个人概率"),
        ("A14","RULE-K1-2026","special_owner_sequence","普通完全住宅房产业主优先；祖辈、同父母兄弟姐妹及合格不完全产权等余位后考虑","不能把特殊情形等同于普通业主第一顺序"),
        ("A11","RULE-P1-2026","relocation_coordinated","拆迁办安置、区内实际居住、广州户籍，核拆迁协议","地段生安排后优先考虑地段校，属于统筹"),
        ("A12","RULE-P1-2026","tenant_standard_lease","穗籍、广州无房、唯一住址；备案审核早于2025-09-01且租期至少到2028-08-31","符合条件走统筹；去向未观察"),
        ("A12","RULE-P1-2026","tianhe_tenant_alternative","天河户籍可用审核早于2026-05-11且租期至少到2029-08-31的备案，其他条件照核","替代期限仅适用相应天河户籍类别；与幼儿园一般派位无关"),
    ]
    for evidence,rule,category,conditions,boundary in entries:
        r = ctx.work_rows[evidence]
        ctx.table("admission_conditions").append(dict(id="COND-"+category,rule_id=rule,
            stage="primary" if evidence in {"A11","A12"} else "kindergarten",policy_year=2026,
            household_category=category,conditions=conditions,interpretation_boundary=boundary,
            actual_admission="unobserved",source_ids=r["source_ids"],source_locator=r["source_locator"],work_evidence_id=r["id"]))


def _housing(ctx):
    listing = json.loads((ctx.root/WORK/"housing-listing-observation.json").read_text())
    for key,monthly,area,date in [("H02",7500,108.58,"2026-11-10"),("H03",5800,80,"2026-09-20")]:
        for metric,value,unit in [("rent_cny_month",monthly,"cny_per_month"),("rent_cny_m2_month",round(monthly/area,2),"cny_per_m2_month")]:
            _housing_row(ctx,key,metric,value,unit,date,area)
    _housing_row(ctx,"H11","sale_ask_cny_m2",listing["displayed_unit_asking_cny_m2"],"cny_per_m2",
        listing["displayed_date"],listing["displayed_gross_area_m2"],listing["displayed_asking_price_cny"])
    home = next(r for r in ctx.table("residences") if r["id"]=="RES018")
    home["housing_evidence_status"]="supplemented_individual_listings_aggregate_missing"
    home["note"]+="；原冻结住房样本未收录，本轮补入两条整租与一条出售挂牌；汇总指标仍缺"


def _housing_row(ctx,key,metric,value,unit,period,area,total=None):
    r = ctx.work_rows[key]
    assert r["verification_status"]=="原页面核实"
    ctx.table("housing_observations").append(dict(id="WORK-"+key+"-"+metric,residence_id="RES018",
        metric=metric,value=value,unit=unit,reference_period=period,observed_on=r["checked_cst"],
        area_m2=area,total_ask_cny=total,evidence_type="listing_example",verification_status="external_declared_page_checked",
        comparable_sale=False,source_id=r["source_ids"][0],source_path=r["input_file"],source_locator=r["source_locator"],
        conflict_status="individual_listing_not_aggregate",work_evidence_id=r["id"],
        note=r["notes"]+"；个案挂牌不等于合同、成交或小区均价；面积仅用于该条单价换算"))


def _positions_and_routes(ctx):
    amap = ctx.work_amap
    source = ctx.source_manager.archive_local(str(WORK/"amap-targeted-checks.json"),"GPT Work 高德返回快照","route_response")
    for key,alias,entity,evidence in [("huawen","HW","CAP-E005-032","G04"),("haibin","HB","CAP-E006-072","G05")]:
        poi = amap["poi_details"][key]; lon,lat = map(float,poi["location"].split(","))
        add_crosswalk(ctx,"gpt_work_poi",poi["id"],"campus",entity,"2026官方同名地址与高德POI一致；WORK-"+evidence,note="仅校区参照位置，不确认接送门")
        mapping = dict(entity_id=entity,candidate_entity_id="",match_status="matched")
        ctx.transport_mapping[alias] = mapping
        ctx.table("positions").append(position("POS-AMAP-"+alias,entity,"transport_destination_poi",lon,lat,"GCJ-02",source,
            "poi_details."+key,"transformed_poi_estimate","官方地址与地图点交叉支持；未经实测接送门"))
    # 同项目管理处另列角色，不用于替换D2路线端点。
    poi = amap["poi_details"]["d2mgmt"]; lon,lat = map(float,poi["location"].split(","))
    ctx.table("positions").append(position("POS-WORK-D2-MGMT","RES015","management_office_poi",lon,lat,
        "GCJ-02",source,"poi_details.d2mgmt","transformed_poi_estimate","33号管理处不是31号路线起点或通学门"))
    for key,evidence in [("D1-HW","G06"),("D2-HW","G07"),("D3-HB","G08")]:
        r = amap["walking_routes"][key]; origin,destination=key.split("-"); p=r["amap"]["route"]["paths"][0]
        a,b = list(map(float,r["origin"].split(","))),list(map(float,r["destination"].split(",")))
        assert sum(s["distance"] for s in p["steps"])==p["distance"]
        assert p["distance"]>=chord_m(*a,*b)
        # 新路线须与原起点的原始GCJ坐标一致；不跨点拼接。
        old = next(p for p in ctx.table("positions") if p["id"]=="POS-AMAP-"+origin)
        assert a==[old["original_longitude"],old["original_latitude"]]
        _route(ctx,origin,destination,p["distance"],p["duration"],"amap_estimate_gate_unverified",source,
            str(WORK/"amap-targeted-checks.json"),ctx.work_rows[evidence]["source_urls"],{},chord_m(*a,*b))
        route = ctx.table("transport_routes")[-1]
        route.update(id="ROUTE-"+key+"-20261113-walk",route_date="2026-11-13",work_evidence_id="WORK-"+evidence,
            sample_scope="targeted_supplement_20261113",note="定向补查POI路线，非完整住宅×园区矩阵；不能直接与旧六园覆盖率混合")


def _fee_context(ctx):
    # 推定和历史收费保留数值及单位，但actual_charge始终为False，不计算净额。
    for key,metric,value,unit,year in [("F09","conditional_care_fee",995,"cny_per_person_month",2026),
        ("F10","historical_care_fee",995,"cny_per_person_month",2024),("F10","historical_meal_fee",20,"cny_per_person_day",2024)]:
        r=ctx.work_rows[key]
        ctx.table("education_fees").append(dict(id="WORK-"+key+"-"+metric,stage="kindergarten",campus_id=CORE[0],
            metric=metric,value=value,unit=unit,value_status="conditional_estimate" if key=="F09" else "historical_third_party",
            amount_relation="conditional" if key=="F09" else "reported",evidence_type=r["verification_status"],
            reference_period=r["applicable_year_or_period"],evidence_year=year,applicability=r["notes"],target_raw=r["object_name"],
            source_ids=r["source_ids"],source_path=r["input_file"],source_locator=r["source_locator"],
            verification_status=r["verification_status"],actual_charge=False,note="不得当作2026园方公示实价或家庭实付",work_evidence_id=r["id"]))
        ctx.table("fee_applicability").append(dict(id="FAP-WORK-"+key+"-"+metric,
            campus_id=CORE[0],fee_id="WORK-"+key+"-"+metric,
            applicability="历史或政策推定背景；不用于2026实际收费或净额计算"))
