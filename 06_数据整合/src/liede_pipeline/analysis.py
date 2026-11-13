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
                    "存在多个数值或时期，需明确选样后才能展示单值",
                    "逐条核对观察ID；不自动平均、选最新值或优先来源",
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
            note="目的性样本；房价不等于家庭收入；平台月租汇总缺少逐套面积分母"))
    costs = {r["residence_id"]:r for r in ctx.table("residence_cost_summary")}
    campuses = {r["id"]:r for r in ctx.table("education_campuses")}
    for route in ctx.table("transport_routes"):
        if not route["analytical_eligible"]:
            continue
        campus = campuses[route["campus_id"]]
        cost = costs[route["residence_id"]]
        rule_ids = [r["rule_id"] for r in ctx.table("campus_admission_rules") if r["campus_id"]==campus["id"]]
        ctx.table("housing_education_links").append(dict(id="LINK-"+route["id"],
            residence_id=route["residence_id"],campus_id=campus["id"],institution_id=campus["institution_id"],
            stage=campus["stage"],ownership=campus["ownership"],route_id=route["id"],
            walk_minutes=route["duration_s"]/60,distance_m=route["distance_m"],
            sale_reference_cny_m2=cost["sale_reference_cny_m2"],sale_status=cost["sale_status"],
            sale_observation_ids=cost["sale_observation_ids"],rent_cny_month=cost["rent_cny_month"],
            rent_cny_m2_month=cost["rent_cny_m2_month"],
            rule_ids=rule_ids,
            admission_condition_ids=[r["id"] for r in ctx.table("admission_conditions") if r["rule_id"] in rule_ids],
            admission_evidence_ids=[r["id"] for r in ctx.table("admission_evidence") if r["subject_id"] in [campus["id"],route["residence_id"],*rule_ids]],
            fee_ids=[r["fee_id"] for r in ctx.table("fee_applicability") if r["campus_id"]==campus["id"]],
            eligibility="not_determined_by_distance",actual_admission="unobserved",
            note="路线使用独立POI端点，不使用住房图默认点；不是家庭观察"))
    _gaps(ctx)
    _evidence(ctx)


def _gaps(ctx):
    for r in ctx.table("residences"):
        if not r["preferred_position_id"]:
            ctx.gap("RESIDENCE_POSITION_MISSING","P0",r["id"],"尚无可采用的住宅参照坐标",
                    "补充来源及位置角色明确的坐标，不借用相近小区点位")
        if not r["has_housing_sample"]:
            ctx.gap("HOUSING_SAMPLE_MISSING","P0",r["id"],"交通研究有该住宅，但原冻结住房样本未收录；新增挂牌例证另表保留",
                    "仍需同口径参考价、可复核成交或租金汇总；个案挂牌不能填补这些缺项",
                    status="supplemented_requires_review" if any(o["residence_id"]==r["id"] for o in ctx.table("housing_observations")) else "open")
    for r in ctx.table("education_campuses"):
        if not r["preferred_position_id"]:
            ctx.gap("CAMPUS_POSITION_MISSING","P0",r["id"],"尚无可采用的园校参照坐标",
                    "核实园区身份和位置；保留未确认候选",[r["source_id"]])
        ctx.gap("ACTUAL_FEE_MISSING","P0",r["id"],"原冻结采集状态表缺少2026园区学费或保教费公示金额",
            "需当年逐园收费表及必要附加项目；补证另行保留来源，不推定家庭实付",[r["source_id"]],
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
            "两个社区比较要求已勘误；旧任务仅为追溯保留" if r["gap_id"]=="G12" else r["needed_evidence"],ids(r["source_id"]),status)
    ctx.gap("HOUSING_HASH_LINE_ENDINGS","P1","housing_csv",
        "旧报告哈希与CRLF表示一致，当前检出使用LF换行",
        "保留两种字节哈希解释；当前输入登记固定检出字节，不改写原件")
    ctx.gap("SOURCE_COVERAGE","P1","commercial_housing_quotes",
        "部分商业报价仅有仓库摘录，缺少外部原始响应归档",
        "补充有出处的原件或字段快照；保留报价类型及时间定义")
    ctx.gap("NO_OUTCOME_DATA","P1","all_household_scenarios",
        "没有已观察的家庭录取、预算或真实通学联结资料",
        "制度路径和模型负担须与实际结果分开")


def _evidence(ctx):
    def add(key, finding, references, sources, boundary, limitation, kind):
        ctx.table("evidence_matrix").append(dict(id=key,finding=finding,supporting_data=references,
            source_ids=sorted(set(sources)),evidence_kind=kind,
            interpretation_boundary=boundary,limitation=limitation))
    campuses = ctx.table("education_campuses")
    mapped = [r for r in campuses if r["preferred_position_id"]]
    add("F01",f"{len(campuses)}条园校候选中，{len(mapped)}条有可采用的地图参照位置",
        [citation("education_campuses",r["id"]) for r in campuses]+[citation("positions",r["preferred_position_id"]) for r in mapped],
        [r["source_id"] for r in campuses]+[r["source_id"] for r in ctx.table("positions") if r["id"] in {c["preferred_position_id"] for c in mapped}],"只描述候选集合的定位覆盖，不代表猎德全量普查",
        "接送门未确认，地域选样仍不完整","record_coverage")
    prices = ctx.table("housing_observations")
    add("F02","住房成本证据包含平台参考价、出售挂牌、租金及平台标示成交，指标分别保留",
        [citation("housing_observations",r["id"]) for r in prices],
        [r["source_id"] for r in prices],"不混合指标、时期、普通住宅与权属未核产品",
        "目的性样本、页面快照不完整；房价不是家庭收入","archived_quotations")
    access = ctx.table("accessibility_comparisons")
    selected = next(r for r in access if r["origin_legacy_id"]=="D3" and r["channel"]=="migrant_points_listed_example")
    add("F03",f"南国花园：积分志愿例的单程模型步行时间比地址对应小学多{selected['additional_minutes']:.2f}分钟",
        [citation("accessibility_comparisons",selected["id"]),citation("transport_routes",selected["route_id"])],
        selected["source_ids"],"只比较一个名单内志愿例，不代表分配结果或最近可申请学校",
        "POI路线、校门未核，没有家庭实际分配观察","derived_case_comparison")
    add("F04","除物理距离外，申请渠道还取决于户籍、住房及其他家庭资格条件",
        [citation("admission_rules",r["id"]) for r in ctx.table("admission_rules")],
        [s for r in ctx.table("admission_rules") for s in r["source_ids"]],
        "规则为有条件路径，不是对真实家庭的资格认定",
        "配套住宅名单、具体门牌和证明材料仍需核验","policy_extract")
    actual = [r for r in ctx.table("education_fees") if r["id"].startswith("FEE-ACTUAL-")]
    add("F05",f"原冻结表{len(actual)}条园校状态均缺2026收费公示；政策、批复、历史及推定值另存",
        [citation("education_fees",r["id"]) for r in ctx.table("education_fees")],
        [s for r in ctx.table("education_fees") for s in r["source_ids"]],
        "未知缴费不当作零，不据此计算家庭净支出",
        "餐费、保教费、年龄、补助资格和抵扣项目均未完整联结","collection_status_and_policy")
    sensitivity = [r for r in ctx.table("walking_sensitivity") if r["coverage"]=="original_6" and
        r["category"]=="public_kindergartens" and r["threshold_min"]==10 and r["scenario"] in {"amap_baseline","slower_1.00"}]
    counts = {s:sum(r["sample_count"]>0 for r in sensitivity if r["scenario"]==s) for s in {"amap_baseline","slower_1.00"}}
    add("F06",f"原六园样本中，10分钟内有教育部门办园的起点从高德基准{counts['amap_baseline']}/3变为1.00米/秒情境下{counts['slower_1.00']}/3",
        [citation("walking_sensitivity",r["id"]) for r in sensitivity],
        [r["source_id"] for r in sensitivity],"步速情境敏感性，不是儿童实测步速或人口覆盖率",
        "限制于原六园样本，未计校门等待；新补查不并入原样本分母","constructed_sensitivity")
    plan = next(r for r in ctx.table("admission_plans") if r["subject_id"]=="INS-SCH-TH1")
    add("F07","天河第一小学的7班计划属于机构总量；两个校区分别保留但不重复计算计划",
        [citation("admission_plans",plan["id"]),citation("education_campuses","CAP-P04"),citation("education_campuses","CAP-P05")],
        [plan["source_id"]],"未将机构总计划下分到具体校区",
        "没有取得校区分配量","aggregation_boundary")
    invalid = [r for r in ctx.table("transport_routes") if not r["analytical_eligible"]]
    add("F08",f"{len(invalid)}条原路线因长度异常或身份未确认排除出综合分析，原记录保留",
        [citation("transport_routes",r["id"]) for r in invalid],
        [r["source_id"] for r in invalid],"保存原件不等于允许进入分析",
        "K7身份已由WORK-G01支持关联；D3→K7的18米异常和实际接送门仍未解决","quality_control")
    work = ctx.table("work_evidence")
    add("F09","本轮45条补证完整保留原核验标签；历史线索、推定、未核实项不提升为当期实测事实",
        [citation("work_evidence",r["id"]) for r in work],
        [s for r in work for s in r["source_ids"]+r["snapshot_source_ids"]],
        "本流水线核对仓库字节、字段和明确对应，沿用GPT Work的外部核验声明",
        "多数新外部网址未附完整原件；原文可用性见来源表","supplement_provenance")
    new_housing = [r for r in prices if r["id"].startswith("WORK-H")]
    add("F10","南国花园补入两条整租：7500元/108.58平方米、5800元/80平方米；另有582万元/107.44平方米出售挂牌",
        [citation("housing_observations",r["id"]) for r in new_housing],
        [r["source_id"] for r in new_housing],
        "仅为不同日期的个案挂牌，出售挂牌单价54170元/平方米；不合成小区均价",
        "同口径小区参考价、可复核成交、合同租金与整租均价仍缺失；详情页复开不稳定","individual_listings")
    routes = [r for r in ctx.table("transport_routes") if r.get("sample_scope")=="targeted_supplement_20261113"]
    add("F11","定向补查显示南国花园至海滨园298米、238秒；该民办园可改变已测任一园最近值",
        [citation("transport_routes",r["id"]) for r in routes]+[citation("education_campuses","CAP-E005-032"),citation("education_campuses","CAP-E006-072")],
        [r["source_id"] for r in routes]+[s for r in work if r["original_evidence_id"] in {"G04","G05"} for s in r["source_ids"]],
        "原六园样本约6.5分钟的最近值继续按原样本解释；新已测候选约4.0分钟，非全片区最短",
        "只补三条路线，非完整矩阵；华文为国企办园，不套教育部门办园派位；园门未实测","targeted_route_extension")
    conditions = ctx.table("admission_conditions")
    add("F12","新增小学安置户优先统筹、租户两组备案期限及幼儿园业主顺序条件，均与实际录取分开",
        [citation("admission_conditions",r["id"]) for r in conditions],
        [s for r in conditions for s in r["source_ids"]],
        "只补充2026制度条件；住宅名称、租盘或历史配套关系不能替代家庭材料",
        "K1/K6/K7当年覆盖楼栋、核心园区新小班收费和家庭最终结果仍未取得","policy_conditions")
