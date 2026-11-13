from .common import EDUCATION, Context, ids, number, stable_id


def build_policies(ctx: Context):
    raw_rules = ctx.csv(EDUCATION/"数据/招生渠道与家庭类别.csv")
    rules = {}
    for r in raw_rules:
        if r["rule_id"].startswith("J"):
            continue
        stage = "kindergarten" if r["rule_id"].startswith("K") else "primary"
        key = "RULE-"+r["rule_id"]+"-2026"
        rules[r["rule_id"]] = key
        ctx.table("admission_rules").append(dict(id=key,legacy_id=r["rule_id"],stage=stage,
            intake_grade="small_class" if stage=="kindergarten" else "grade_1",
            policy_year=2026,eligibility_text=r["eligibility"],pathway=r["path"],
            original_scope=r["stage"],source_ids=ids(r["source_id"]),source_locator=r["locator"],
            verification_status="repository_policy_extract",actual_admission="unobserved",
            interpretation_boundary=r["limitations"]+"；原来源如覆盖多学段，本记录只取保留学段"))
    ctx.rule_ids = rules
    for r in ctx.education_raw:
        for rule in ids(r.get("access_rule",r.get("access_rules",""))):
            if rule in rules:
                ctx.table("campus_admission_rules").append(dict(id=stable_id("CR-",r["record_id"],rule),
                    campus_id="CAP-"+r["record_id"],rule_id=rules[rule],
                    applicability="conditional_general_or_listed_channel",policy_year=2026,
                    note="关联规则不等于认定资格或实际录取"))
    campus_by_legacy = {r["legacy_id"]:r for r in ctx.table("education_campuses")}
    for n,r in enumerate(ctx.csv(EDUCATION/"数据/研究点位招生计划.csv"),2):
        if "初中" in r["entry_grade"]:
            continue
        campus = campus_by_legacy.get(r["target_id"])
        institution = "INS-"+r["target_id"] if r["target_id"].startswith("SCH-") else ""
        if not campus and not institution:
            continue
        ctx.table("admission_plans").append(dict(id=stable_id("PLAN-","primary",r["target_id"],r["plan_category"],r["source_id"],r["locator"]),
            subject_type="institution" if institution else "campus",subject_id=institution or campus["id"],
            stage="primary",intake_grade="grade_1",policy_year=2026,
            metric="classes" if r["unit"]=="班" else "intake_places",value=number(r["amount"]),
            unit="class" if r["unit"]=="班" else "person",plan_category=r["plan_category"],
            source_id=r["source_id"],source_locator=r["locator"],
            source_path=str(EDUCATION/"数据/研究点位招生计划.csv"),
            note=r["note"]+"；重叠计划不相加，机构总额不擅自下分校区"))
    for r in ctx.education_raw:
        if not r["record_id"].startswith("E"):
            continue
        for field,metric,unit in [("planned_classes","classes","class"),
                ("social_lottery_total","social_lottery_total","person"),
                ("owner_children","owner_children_places","person"),
                ("remaining_random_lottery","remaining_random_places","person")]:
            value = number(r.get(field))
            if value is None:
                continue
            ctx.table("admission_plans").append(dict(id=stable_id("PLAN-",r["record_id"],metric),
                subject_type="campus",subject_id="CAP-"+r["record_id"],stage="kindergarten",
                intake_grade="small_class",policy_year=2026,metric=metric,value=value,unit=unit,
                plan_category=metric,source_id=r["source_id"],source_locator=f"HTML row {r['html_row']}; {field}",
                source_path=str(EDUCATION/"数据/猎德及周边幼儿园候选.csv"),
                note=r.get("lottery_relationship","")+"；组成项与总量分别保存，非中签概率"))
    # Keep the district total as one observation. The overlapping transport CSV
    # is used for validation, rather than adding ten schools to the campus sample.
    primary_plan = [r for r in ctx.csv(EDUCATION/"数据/2026积分学位分学校分学段.csv")
                    if r["stage"]=="小学" and r["source_id"]=="E030-A001"]
    for r in primary_plan:
        ctx.table("district_primary_points_plan").append(dict(id="POINTS-"+r["source_row"],
            school_name=r["school"],value=number(r["plan"]),unit="person",policy_year=2026,
            source_id=r["source_id"],source_locator="Sheet1 row "+r["source_row"],
            note="区级渠道名额表，不扩充地理校区样本"))
    private_names = {r["name"]:r for r in ctx.table("education_campuses") if r["ownership"]=="private" and r["stage"]=="primary"}
    for r in ctx.csv(EDUCATION/"数据/2026积分学位分学校分学段.csv"):
        if r["stage"]!="小学" or r["source_id"]!="E030-A003" or r["school"] not in private_names:
            continue
        campus = private_names[r["school"]]
        ctx.table("admission_plans").append(dict(id=stable_id("PLAN-",r["source_id"],r["source_row"],"primary"),
            subject_type="campus",subject_id=campus["id"],stage="primary",intake_grade="grade_1",policy_year=2026,
            metric="maximum_channel_places",value=number(r["plan"]),unit="person",
            plan_category="private_points_school_maximum",source_id=r["source_id"],
            source_locator="Sheet3 row "+r["source_row"],source_path=str(EDUCATION/"数据/2026积分学位分学校分学段.csv"),
            note="受全区民办小学248人总额约束；上限不是实际分配量，各校上限不相加；只按官方准确名称对应。"))
    _fees(ctx, campus_by_legacy)


def _fees(ctx, campuses):
    path = EDUCATION/"数据/收费政策与历史价格.csv"
    for r in ctx.csv(path):
        if r["fee_id"] in {"F11","F21"}:
            continue
        stage = "kindergarten" if r["fee_id"] in {"F01","F02","F03","F04","F05","F17","F18"} else "primary"
        campus = {"F17":"CAP-E006-080","F19":"CAP-P13","F20":"CAP-P12"}.get(r["fee_id"],"")
        value = number(r["amount"])
        ctx.table("education_fees").append(dict(id="FEE-"+r["fee_id"],stage=stage,campus_id=campus,
            metric=r["item"],value=value,unit=r["unit"],
            value_status="unknown" if value is None else "known_policy_or_reported_value",
            amount_relation="lower_bound" if r["fee_id"]=="F18" else "stated",
            evidence_type=r["evidence_type"],reference_period=r["effective_period"],
            evidence_year=2020 if r["fee_id"]=="F17" else 2022 if r["fee_id"]=="F18" else
                2024 if r["fee_id"] in {"F01","F02","F05","F08","F09","F19","F20"} else
                2025 if r["fee_id"] in {"F03","F04","F12","F13","F14","F15","F16"} else 2026,
            applicability=r["eligibility"],target_raw=r["target"],
            source_ids=ids(r["source_id"]),source_path=str(path),source_locator=r["locator"],
            verification_status="repository_policy_or_historical_extract",actual_charge=False,
            note=r["limitations"]+"；仅适用于保留学段，不代表已观察的家庭缴费"))
    status_path = EDUCATION/"数据/逐校收费核验状态.csv"
    local_source = ctx.source_manager.archive_local(str(status_path),"园校收费采集状态","curated_status_table")
    for r in ctx.csv(status_path):
        if r["record_id"] not in campuses:
            continue
        campus = campuses[r["record_id"]]
        value = number(r["published_2026_tuition_amount"])
        ctx.table("education_fees").append(dict(id="FEE-ACTUAL-"+r["record_id"],stage=campus["stage"],
            campus_id=campus["id"],metric="published_2026_tuition_or_care_fee",value=value,
            unit=r["unit"],value_status="not_collected" if value is None else "published",
            amount_relation="unknown" if value is None else "stated",evidence_type="collection_status",
            reference_period="2026",evidence_year=2026,applicability="逐园校公示收费",
            target_raw=r["name"],source_ids=[local_source],source_path=str(status_path),
            source_locator=r["record_id"],verification_status="not_collected" if value is None else "repository_extract",
            actual_charge=value is not None,note=r["missing"]+"；空白不是零；法定学费与实际总支出分开"))
        for fee in (["FEE-F06","FEE-F07"] if campus["stage"]=="primary" and campus["ownership"]!="private" else []):
            ctx.table("fee_applicability").append(dict(id=stable_id("FA-",campus["id"],fee),
                campus_id=campus["id"],fee_id=fee,status="statutory_ordinary_tuition_or_miscellaneous",
                note="无法确定餐费、交通或课后服务总额"))
        fee = {"P12":"FEE-F20","P13":"FEE-F19"}.get(r["record_id"])
        if fee:
            ctx.table("fee_applicability").append(dict(id=stable_id("FA-",campus["id"],fee),
                campus_id=campus["id"],fee_id=fee,status="approved_standard_conditions_apply",
                note="批复金额可能与实际缴费、补贴抵扣不同"))
