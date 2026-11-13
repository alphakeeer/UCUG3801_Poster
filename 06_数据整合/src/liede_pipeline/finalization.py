"""独立审查后的语义修正；不覆盖上游摘录或推定真实家庭结果。"""

from .common import stable_id
from .coordinates import chord_m

WARNING_2025 = "https://www.thnet.gov.cn/attachment/7/7806/7806425/10240576.pdf"
HK_PRIMARY = "公示无异议后，按申请人积分排名从高到低依次安排至南国学校小学部，直至45个一年级计划名额用完；个体录取未观察"


def finalize_semantics(ctx):
    source = ctx.source_manager.reference(WARNING_2025,"2025小学细则中的2026兴国招生预警",
        "用户提供的Independent Research Review（审查5101aa7）","independent_review_reference")
    for year,doc_year,src,locator,status in [
        (2026,2025,source,"2025细则小学招生预警条款；沿用独立审查结论","review_supplied_original_not_retrieved"),
        (2027,2026,"E002","2026细则（五）招生预警，PDF第10—11页（印刷页9—10）","local_pdf_visual_check"),
    ]:
        ctx.table("capacity_notices").append(dict(id=f"NOTICE-XINGGUO-{year}",campus_id="CAP-P06",
            document_year=doc_year,target_intake_year=year,trigger="须结合取得房产时间等条件且实际报名超过计划时适用",
            actual_over_capacity_observed=None,actual_reassignment_observed=None,source_id=src,
            source_locator=locator,verification_status=status,note="预警不等于当年已经超额或真实家庭被改派"))
    for r in ctx.table("admission_rules"):
        r["association_role"]="general_policy_reference"
        if r["id"]=="RULE-P4-2026":
            r.update(eligibility_text=HK_PRIMARY,pathway="小学一年级按积分顺序安排至指定小学部，计划45人",
                original_scope="小学一年级",source_locator="E031一、学位情况（仅小学）；二（一）1招生录取",
                interpretation_boundary="不引入其他学段计划、志愿流程；排名与最终个人录取结果未观察")
    for r in ctx.table("campus_admission_rules"):
        r["applicability"]="general_rule_reference_only"
        r["note"]="仅供查找该园校相关通用规则，不认定任何住宅家庭符合条件"
    for r in ctx.table("education_campuses"):
        if r["id"]=="CAP-P08":
            r["source_locator"]="E002附件5小学地段条目；其他学段关系不用于当前证据包"
    _scenarios(ctx,source)
    _fees(ctx)
    _routes(ctx)
    _channel_contexts(ctx)


def _scenarios(ctx,warning_source):
    texts={
        "Tianhe_hukou_matching_full_home":"天河户籍、人户一致、完全产权、实际居住、学位未占用等材料均须核验；只作地段条件情境",
        "Guangzhou_hukou_eligible_renter":"穗籍、广州无房、唯一住所及有效备案等须核验；普通备案早于2025-09-01且租期至少至2028-08-31，天河户籍可按规定用另一组期限；统筹去向未知",
        "Non_Guangzhou_approved_policy_care":"政策性照顾类别及居住证明须核验；小学由区统筹，幼儿园按相应一般派位条件申请",
        "Non_Guangzhou_approved_migrant_points":"申请审核及公示、积分排名和志愿均须核验；冼村小学只是名单内一个志愿例，不是实际分配",
        "Eligible_HK_Macao_points":HK_PRIMARY,
        "Non_Guangzhou_no_public_channel_in_scope":"本情境未识别可用的政策照顾或普通积分公办渠道；民办学校仍须按当年简章核资格与费用",
        "Tianhe_hukou_eligible_owner":"符合年龄及天河户籍可按一般派位条件申请；配套业主优先须核当年具体园区、门牌、产权与学位使用，不按住宅名称认定",
        "Tianhe_hukou_renter_no_ownership_priority":"符合年龄及天河户籍可选一所教育部门办园参加一般随机派位；不取得配套业主优先",
        "Outside_Tianhe_hukou_no_policy_exception":"仅附近租住不能取得一般派位资格；其他办园主体须另核当年招生简章",
    }
    for r in ctx.table("household_scenarios"):
        r["conditions"]=texts[r["profile"]]
        r["individual_eligibility_verified"]=None
        r["warning_target_intake_year"]=None
        r["warning_document_year"]=None
        r["actual_over_capacity_observed"]=None
        if r["profile"]=="Eligible_HK_Macao_points":
            r["eligibility_status"]="rank_order_allocation_up_to_45_unobserved"
        if r["origin_legacy_id"]=="D2" and r["profile"]=="Tianhe_hukou_matching_full_home":
            r.update(warning_target_intake_year=2026,warning_document_year=2025)
            r["source_ids"].append(warning_source)
            r["conditions"]+="；2026兴国条件性预警来源为2025细则；2026细则预警指向2027，未观察2026实际超额"


def _fees(ctx):
    for r in ctx.table("education_fees"):
        key=r["id"]
        layer=("collection_status" if r["evidence_type"]=="collection_status" and r["value"] is None
            else "approved_school_standard" if key in {"FEE-F19","FEE-F20"}
            else "conditional_estimate" if r["value_status"]=="conditional_estimate" or r["evidence_type"]=="estimated"
            else "historical_quote" if key in {"FEE-F17","FEE-F18"} or r["value_status"]=="historical_third_party"
            else "household_payment" if r["evidence_type"]=="actual_receipt"
            else "current_published_charge" if r["actual_charge"]
            else "conditional_subsidy" if r["metric"]=="conditional_subsidy" or key=="FEE-F10"
            else "policy_standard")
        r.update(evidence_layer=layer,household_total_net_cost_cny=None,
            household_total_net_cost_observed=False,usable_for_affordability_count=False)
    fees={r["id"]:r for r in ctx.table("education_fees")}
    for r in ctx.table("fee_applicability"):
        fee=fees[r["fee_id"]]
        r["status"]=fee["evidence_layer"]+"_reference_only"
        r["evidence_layer"]=fee["evidence_layer"]
        r["association_role"]="fee_evidence_reference_only"
        r["usable_for_affordability_count"]=False
        r["note"]=r.get("note","") or r.get("applicability","")
        r["note"]+="；不代表本住宅家庭须付、已付或可负担的费用"


def _routes(ctx):
    positions={r["id"]:r for r in ctx.table("positions")}
    for r in ctx.table("transport_routes"):
        a,b=positions[r["origin_position_id"]],positions[r["destination_position_id"]]
        r["endpoint_chord_m"]=chord_m(a["longitude"],a["latitude"],b["longitude"],b["latitude"])
        length_ok=r["length_check_passed"] and r["distance_m"]+0.01>=r["endpoint_chord_m"]
        r["length_check_passed"]=length_ok
        if not length_ok:
            r.update(analytical_eligible=False,exclusion_reason="subchord_distance",review_quality="excluded_subchord_distance",analysis_role="excluded")
        elif r["destination_legacy_id"]=="K7":
            r.update(review_quality="legacy_name_address_matched_poi_gate_unverified",analysis_role="supplemental_with_label")
        else:
            r.update(review_quality="ordinary_poi_estimate_gate_unverified",analysis_role="ordinary_poi_estimate")
    for r in ctx.table("accessibility_comparisons"):
        if r["channel"]=="hk_macao_listed_channel":
            r["interpretation_boundary"]=HK_PRIMARY


def _channel_contexts(ctx):
    campuses={r["id"]:r for r in ctx.table("education_campuses")}
    assigned={"RES001":"CAP-P01","RES015":"CAP-P06","RES018":"CAP-P02"}
    for route in ctx.table("transport_routes"):
        if not route["analytical_eligible"]:
            continue
        campus=campuses[route["campus_id"]]
        if campus["stage"]=="kindergarten" and campus["ownership"]=="education_department":
            owner=next((p for p in ctx.table("admission_plans") if p["subject_id"]==campus["id"] and p["metric"]=="owner_children_places"),None)
            _context(ctx,route,"general_lottery","age_and_tianhe_hukou_or_policy_care","RULE-K1-2026",
                "conditional_pathway_reference","须核出生日期、户籍或政策性照顾材料；网上只选一园；不保证录取",owner)
            _context(ctx,route,"affiliated_owner_priority","qualifying_affiliated_owner","RULE-K1-2026",
                "not_available_in_published_2026_plan" if owner and owner["value"]==0 else "affiliated_address_and_documents_unverified",
                "该园区2026公布业主子女名额为0；符合一般条件者仍可走一般派位" if owner and owner["value"]==0 else
                "须核2026园区配套门牌、户籍、产权、学位占用和顺序；未确认本住宅属于覆盖范围",owner)
        elif campus["stage"]=="kindergarten":
            _context(ctx,route,"campus_specific_admission","campus_notice_required",
                "RULE-K2-2026" if campus["ownership"]=="other_department" else "RULE-K3-2026",
                "campus_notice_and_household_documents_unverified","举办部门或民办园按当年简章核验；不套教育部门办园统一派位")
        else:
            linked=assigned[route["residence_id"]]==campus["id"]
            _context(ctx,route,"address_linked","matching_full_home_and_hukou","RULE-P1-2026",
                "conditional_address_link_reference" if linked else "not_address_linked_in_reviewed_catchment_table",
                "核具体门牌、人户一致、完全产权、实际居住、学位占用及当年容量；不能推定真实家庭资格")
            _context(ctx,route,"migrant_points","approved_migrant_points_applicant","RULE-P3-2026",
                "listed_option_ranking_preferences_unverified" if campus["id"]=="CAP-P07" else "not_in_2026_public_points_plan",
                "冼村小学为名单内志愿例，需核积分排名与志愿；原四校未列入所核名单，不据此排除其他政策渠道")
            _context(ctx,route,"hk_macao_ranked","publicly_cleared_hk_macao_points_applicant","RULE-P4-2026",
                "rank_order_plan_individual_result_unobserved" if campus["id"]=="CAP-P02" else "not_designated_in_reviewed_hk_primary_plan",HK_PRIMARY)
    # 统筹去向未知，不能把统筹家庭复制为每个近邻校园的可申请者。
    for residence in assigned:
        for category in ["qualifying_tenant","qualifying_relocation_household"]:
            ctx.table("admission_channel_contexts").append(dict(id="CHANNEL-"+residence+"-"+category,
                residence_id=residence,campus_id="",route_id="",stage="primary",policy_year=2026,
                channel="district_coordination",household_category=category,rule_id="RULE-P1-2026",
                applicability_status="coordination_destination_unknown",requirements="核当年租赁或安置材料、户籍、实际居住等；最终统筹校园未知",
                published_owner_children_places=None,individual_eligibility_verified=None,
                actual_admission="unobserved",can_count_eligible_campuses=False,source_ids=["E002"]))


def _context(ctx,route,channel,category,rule,status,requirements,owner=None):
    allowed_conditions={"general_lottery":{"general_lottery"},"affiliated_owner_priority":{"affiliated_owner","owner_over_capacity","special_owner_sequence"}}
    ids=[r["id"] for r in ctx.table("admission_conditions") if r["rule_id"]==rule and
        (r["household_category"] in allowed_conditions[channel] if channel in allowed_conditions else True)]
    refs=next(r["source_ids"] for r in ctx.table("admission_rules") if r["id"]==rule)
    ctx.table("admission_channel_contexts").append(dict(id=stable_id("CHANNEL-",route["id"],channel),
        residence_id=route["residence_id"],campus_id=route["campus_id"],route_id=route["id"],stage="kindergarten" if rule.startswith("RULE-K") else "primary",
        policy_year=2026,channel=channel,household_category=category,rule_id=rule,
        applicability_status=status,requirements=requirements,rule_reference_condition_ids=ids,
        published_owner_children_places=owner["value"] if owner else None,plan_ids=[owner["id"]] if owner else [],
        affiliated_address_verified=None,household_documents_verified=None,individual_eligibility_verified=None,
        actual_admission="unobserved",can_count_eligible_campuses=False,source_ids=refs))
