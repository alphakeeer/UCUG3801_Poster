"""最终交接材料：仅从规范数据和已核对的原规则生成。"""

import json
from collections import Counter


def write_handoff(ctx,destination,version,report):
    t=ctx.tables
    access=t["accessibility_comparisons"]
    by_key={(r["origin_legacy_id"],r["channel"]):r for r in access}
    lines=["# 最终核心证据简报","",f"数据版本：`{version}`。研究范围为猎德及相关周边的幼儿园小班、小学一年级；大班减免单列。","",
        "## 1．同一住址的不同招生渠道，可对应不同小学路线","",
        "|住宅起点|地段对应小学|单程分钟|冼村小学志愿例分钟|差值分钟|",
        "|---|---|---:|---:|---:|"]
    for origin,name,school in [("D1","猎德花园","猎德实验学校小学部"),("D2","中海璟晖华庭","体育东路小学兴国学校"),("D3","南国花园","南国学校小学部")]:
        a=by_key[origin,"address_linked_conditional"]; b=by_key[origin,"migrant_points_listed_example"]
        lines.append(f"|{name}|{school}|{a['walk_minutes']:.1f}|{b['walk_minutes']:.1f}|+{b['additional_minutes']:.1f}|")
    lines += ["",
        "来穗积分公办小学名单10所、315个一年级计划名额，原四所小学均未列入，冼村小学5人。南国花园两条指定路线166秒与1706秒，差1540秒，约25.7分钟。表中时间和差值分别从原始秒数计算后四舍五入，不能用已舍入分钟倒算。",
        "",
        "**使用边界：** 地段对应须满足完整家庭条件；冼村小学仅为可填报志愿例，未证明是最近可申请学校，更不是实际分配。两组都是高德POI到POI估算。港澳小学渠道公示后按积分排名安排至南国学校小学部，直到45名额用完；D3与地段目的地重合，补充表保留。",
        "",
        "数据：[九条渠道比较](data/accessibility_comparisons.csv)、[42条原路线](data/transport_routes.csv)。主图：[英文双系列路线图](figures/figure_B_admission_accessibility.png)，另有同名SVG/PDF；[中文图注](FIGURE_LEGENDS.md)。",
        "来源：[2026小学细则附件5](https://www.thnet.gov.cn/attachment/8/8016/8016210/10791180.pdf)、[积分名额原XLS](https://www.thnet.gov.cn/attachment/8/8040/8040292/10872346.xls)、[港澳指引二（一）](https://www.thnet.gov.cn/gzjg/qzf/qjyj/zsks/content/post_10833283.html)。",
        "",
        "## 2．住房通过资格材料和分配顺序发挥作用","",
        "符合条件的拆迁安置家庭，在地段生安排后优先考虑地段校，属于统筹。穗籍合格租户须核广州无房、唯一住所和备案等，统筹去向未知。一般备案早于2025-09-01、租期至少至2028-08-31；天河户籍可按规定适用早于2026-05-11、租期至少至2029-08-31的另一组条件。",
        "",
        "幼儿园业主/剩余随机计划分别为猎德园85/50、金穗本园0/45、花城园区23/45、K7为24/44。金穗本园该年业主计划为0，符合一般条件者仍可参加一般派位。其他园区的业主名额不能按近邻关系分配给住宅样本；K1/K6/K7的当年覆盖门牌仍缺。",
        "",
        "数据：[园区计划](data/admission_plans.csv)、[细分条件](data/admission_conditions.csv)、[住宅—园区—渠道适用背景](data/admission_channel_contexts.csv)。后者明确记录待核条件，不是家庭资格判决。",
        "来源：[小学细则附件9](https://www.thnet.gov.cn/attachment/8/8016/8016210/10791180.pdf)、[幼儿园方案第三、四部分](https://www.thnet.gov.cn/gzjg/qzf/qjyj/zsks/content/post_10777181.html)、[园区计划第36、52—54项](https://www.thnet.gov.cn/gzjg/qzf/qjyj/zsks/content/post_10815546.html)。",
        "",
        "## 3．幼儿园近距离供给对样本和假设步速敏感","",
        "原六园样本中，按高德基准，三个起点均有教育部门办园在10分钟内；按同一路线米数以1.00米/秒重算，只剩猎德花园，3/3变为1/3。补查海滨园后，南国花园到扩展后已测最近任一园，从388秒（约6.5分钟）变为238秒（约4.0分钟），海滨属于普惠性民办。",
        "",
        "**使用边界：** 只描述已测候选和假设步速，非全片区最近或可录取范围。D3→K7的18米短于约51.6米端点直距，继续排除，真实有效距离未知；D1/D2至K7两条旧名POI路线只能带标签作补充分析。",
        "数据：[原六园敏感性](data/walking_sensitivity.csv)、[路线质量及分组](data/transport_routes.csv)。来源：[2026民办园名录海滨条目](https://www.thnet.gov.cn/gzjg/qzf/qjyj/zsks/content/post_10815624.html)及归档高德返回。",
        "",
        "## 4．收费制度有差异，家庭可负担程度未知","",
        "公办小学免学费。新蕾、新昌批复学费分别8000元、8700元/生/学期，适用期覆盖2026学年；实收及补贴抵扣另核。核心四幼儿园的新小班当期保教费、餐费和净缴费仍缺。学前一年公办保教费减免及民办参照减免，不能套入新小班。",
        "",
        "数据：[费用证据层级](data/education_fees.csv)、[仅供参考的费用挂接](data/fee_applicability.csv)。政策、逐校批复、当期公示、历史、推定和家庭实缴分开；联表不能用于计算可负担园校数。",
        "来源：[公办义务教育收费](https://fgw.gz.gov.cn/ztzl/gzsfzggwzdlyxxgkzl/content/post_10506743.html)、[新蕾批复](https://fgw.gz.gov.cn/tzgg/ywgg/content/post_10414690.html)、[新昌批复](https://fgw.gz.gov.cn/gkmlpt/content/9/9758/post_9758311.html)、[学前减免问答](https://jyj.gz.gov.cn/gk/zfxxgkml/bmwj/qtwj/content/post_10516322.html)。",
        "",
        "## 共同局限与交付使用","",
        "三个住宅是目的性案例，无家庭收入、申请、录取、净费和真实接送联结。住房报价不是收入或支付能力；不作三住宅成本排序，不推断住房性质、房价资本化或学校隔离的因果效应。图A仅作位置背景：住宅5/18、幼儿园14/30、小学12/13，不编码价格，不推断设施聚集。",
        "",
        "兴国2026条件性预警出自2025细则；2026细则的相关预警针对2027。两者均非已观察的超额或改派，具体见[预警年份表](data/capacity_notices.csv)。2025原件本轮重取遇403，沿用用户提供独立审查的原件核对结论；2026扫描页及港澳指引已核对。",
        "",
        "完整证据链见[表C](table_C_evidence_matrix.md)，审查处置见[审查响应](REVIEW_RESPONSE.md)，复现入口 `../run.py all`。理论组可引用上述制度机制，报告组引用限定数据与来源，海报负责人直接使用双系列图并保留图注，无需修改已有海报文件。",""]
    (destination/"FINAL_EVIDENCE_BRIEF.md").write_text("\n".join(lines))
    quality=Counter(r["review_quality"] for r in t["transport_routes"])
    open_gaps=Counter(r["priority"] for r in ctx.gaps if r["status"]=="open")
    handoff=f"""# 最终研究证据包交接

数据版本：`{version}`。本版完成独立审查所需的准确性修正，仅包含小学与幼儿园；不新增家庭实证或全面资料收集。

## 三类负责人直接使用的入口

- 理论组：[四条核心发现简报](FINAL_EVIDENCE_BRIEF.md)，引用制度机制及限制，不作因果或群体结果推断。
- 报告组：[表C十二项证据链](table_C_evidence_matrix.md)、[审查修正](REVIEW_RESPONSE.md)及[来源登记](data/source_registry.csv)。
- 海报负责人：[英文双系列路线主图](figures/figure_B_admission_accessibility.png)、[不含价格色阶的定位附图](figures/figure_A_housing_education.png)及[图注](FIGURE_LEGENDS.md)。同名PDF/SVG可导入排版，不改动旧海报。

## 正确读取数据

`housing_education_links`共41行，**只供证据查找**。`reference_*`是相关通用资料，不是适用于该住宅家庭的已核规则或应缴费用。没有可申请或可负担计数，家庭净额留空。

`admission_channel_contexts`共{len(t['admission_channel_contexts'])}行，以住宅×园区×渠道×家庭类别条件说明适用背景；金穗本园业主栏按2026公布计划为0，一般派位单列；未知统筹去向不分配到近邻学校。所有个人资格和录取仍未观察，行数不代表家庭数。

费用表区分政策、批复、当期公示、历史、推定与家庭实缴；费用挂接均有明确状态。冻结表43条未采集不等于全部学校不存在官方标准；新蕾、新昌批复另列，不能计算家庭净额。

住宅18个、园校43个（幼儿园30、小学13），定位分别5/18、14/30及12/13。机构参考41个，校区不合并，班数、人数、总项及子项不混加。住房参考、挂牌、租金和平台标示成交仍全部保留，不混为价格梯度或收入。

42条路线保留，41条可关联：39条普通POI估算、2条旧名地址匹配的K7补充路线、1条D3→K7长度异常排除。主图6行、6条独立路线；补充港澳3行；总9行对应8条独立路线。原六园敏感性与扩展已测候选分开。

## 修正与保留范围

资格/费用误读、金穗0名额、路线质量、图示混合住房报价、预警年份、港澳小学程序和字典旧数量已修正。未修复或补造的真实缺口为核心园区当年配套门牌与费用、K7实际门点和有效D3路线、家庭录取、预算和接送。

## 复现和版本

运行 `../run.py all`、`../run.py validate`以及 `python -m unittest discover -s ../tests -q`。本次构建检查{report['check_count']}项、失败{report['failure_count']}项；输出与代码/数据版本绑定，完整复现记录见[核验记录](../VERIFICATION.md)。通用补证接口见[导入说明](../IMPORT_VERIFIED_FACTS.md)。原183份输入与其他组员工作继续受哈希保护。

旧原件和研究报告均保留；历史整合版本可通过Git `5101aa7`查阅。最终PR、合并提交和数据版本记录于模块根目录的发布记录，不通过手工改动派生CSV填写发布元数据。
"""
    (destination/"HANDOFF.md").write_text(handoff)
    (destination/"QUALITY_SUMMARY.md").write_text(f"""# 最终数据质量摘要

数据版本：`{version}`。构建检查{report['check_count']}项，失败{report['failure_count']}项。

- 原输入和工作文件受保护，旧交通四张CSV在临时目录复算一致。
- 路线分组：{dict(quality)}；所有42条补算WGS84端点直距，D3→K7异常仍排除。
- 通用规则与费用仅供参考；渠道背景表单列，个人资格、家庭净支出均未知，不生成可申请或可负担园校计数。
- 金穗本园2026业主计划0与一般派位分开；收费类型和年份明确，不以缺失替代零。
- 当前{len(ctx.gaps)}条质量追踪包括历史退役项；开放项按优先级为{dict(open_gaps)}。不通过无限补资料追求空缺口表。
- 核对43园校/41机构、计划粒度、坐标和来源；原45条补证保留原核验标签与年份。
- 图A去价格色阶并分学段写定位分母；图B只绘六条双系列路线，不混住房成本或实际录取。

详细检查见 `quality_report.json`，字段见 `schemas.json`，输入/输出哈希见 `run_manifest.json`，限制见[最终简报](FINAL_EVIDENCE_BRIEF.md)。
""")
    decisions=json.loads((ctx.module/"config/final_review_decisions.json").read_text())
    response=["# 独立研究审查响应","","审查基准：`5101aa7ca61e0d2ddeff85a8209d9cf126a33508`，用户提供的GPT Work Independent Research Review。","",
        f"修正数据版本：`{version}`。不更改原研究资料或其他组员文件。","",
        "|问题|处置|验收位置|","|---|---|---|"]
    response += [f"|{r['issue']}|{r['resolution']}|{r['verification']}|" for r in decisions["decisions"]]
    response += ["","2025细则本轮下载返回403，来源登记为仅引用并标明沿用独立审查；2026归档PDF第10页的2027预警及港澳小学指引已核对。没有将无法重取原件改标为本地已归档。","",
        "可保留的局限：目的性样本与定位不均、门点未实测、配套范围未取得、净费用和家庭结果未观察。这些限制随最终简报和图注交接，不再扩展采集。",""]
    (destination/"REVIEW_RESPONSE.md").write_text("\n".join(response))
