# 数据字典与关联规则

本文件规定字段含义；每次构建的完整字段列表、Python值类型和空值情况见 [outputs/schemas.json](outputs/schemas.json)。所有派生CSV使用 UTF-8 BOM、LF换行，布尔值为 `true`/`false`，列表及嵌套对象使用JSON字符串。CSV空白表示未知、未取得或未适用到该记录，具体原因由状态字段说明；绝不自动填0。JSON报告保留原生 `null`。

## 一、表的粒度与主外键

所有表的主键为 `id`。不要按相似名称直接连接。

| 表 | 一行的含义 | 主要关联 | 数量口径 |
|---|---|---|---|
| `residences` | 一个住宅开发项目参考对象 | `preferred_position_id → positions.id` | 当前18个；不是18户家庭 |
| `education_campuses` | 一个独立园区或小学校区学段 | `institution_id → institutions.id`，位置另表 | 当前43条，不含初中；不是完整地域名录 |
| `institutions` | 一个机构参考或已记录的举办主体分组 | 校区经 `institution_id`引用 | 当前41个；无证据的同名园不合并 |
| `entity_crosswalk` | 一个命名空间下的原始对象ID到规范对象的对应 | `entity_id`或 `candidate_entity_id` | `namespace + source_record_id + entity_type`唯一 |
| `positions` | 一个来源及位置角色下的空间参照 | `entity_id → residence/campus` | 同一对象可有多个位置；不等于入口 |
| `housing_observations` | 一个指标、时间及来源下的住房数值摘录 | `residence_id`、`source_id` | 平台参考、挂牌、租赁、标示成交、政策租金分别保存 |
| `admission_rules` | 一个规则类别的2026年学段切片 | `source_ids → source_registry` | 条件与程序，不是资格判决 |
| `campus_admission_rules` | 园校与规则之间的有条件关联 | `campus_id`、`rule_id` | 不代表每类家庭都能申请该园校 |
| `admission_plans` | 一个机构/园校、招生类别、指标、年度的计划 | `subject_type + subject_id` | 班数、人数、业主及随机派位分开；共享计划只存一次 |
| `district_primary_points_plan` | 官方区级小学积分计划中的一所学校 | `source_id`、原表行号 | 10所、315人；不扩充地理校区样本 |
| `education_fees` | 一条政策基准、批复、历史值或当期采集状态 | 可有 `campus_id`，另有 `source_ids` | 不同费用项目、年龄、周期和证据类型不混合 |
| `fee_applicability` | 一项费用政策与园校的条件性对应 | `campus_id`、`fee_id` | 不计算家庭净缴费用 |
| `transport_routes` | 一个住宅POI到园校POI的某日单程步行模型记录 | 住宅、园校、原始位置、来源 | 39条保留记录；仅36条可用于综合连接 |
| `household_scenarios` | 一组构造家庭条件及可能申请路径 | 住宅、园校（可空）、来源 | 30种情境，非30户观察 |
| `walking_sensitivity` | 起点×样本集合×类别×步速情境×阈值 | 原交通ID、来源 | 648条模型组合，非648次测量 |
| `escort_scenarios` | 一条示例路线下的接送段数及费用情境 | 原交通ID、来源 | 12条构造情境 |
| `residence_cost_summary` | 一个住宅的可展示成本引用及缺失/冲突状态 | 住房观察ID、默认位置 | 冲突或多期值不平均、不取“最新” |
| `housing_education_links` | 一条合格路线与住宅成本、园校及规则的连接 | `route_id`、住宅、园校、规则和费用ID列表 | 36条；不是独立家庭样本，也不是额外的房价样本 |
| `accessibility_comparisons` | 一处住宅与一种示例申请渠道的路线比较 | 路线、基准路线、规则 | 9条；同一路线可对应不同渠道，不重复增加路线数 |
| `source_registry` | 一个已登记来源载体或仓库引用 | `canonical_source_id` | 载体数不是独立政策/研究数量 |
| `evidence_matrix` | 一个主要发现的证据链 | `supporting_data`为 `table:id`列表 | Finding → Data → Sources → Boundary → Limitation |
| `research_gaps` | 一个实体/问题的缺失、冲突或已退役任务 | `subject_id`、来源 | `retired_scope_erratum`不构成当前研究要求 |
| `verified_facts` | 一条被接受并追加的导入事实 | 原fact ID、输入CSV哈希及行号、来源 | 不代表本地重新完成了外部核验 |
| `import_quarantine` | 一条不能安全采用的导入行 | 原始整行JSON及拒绝原因 | 保留等待确认，不模糊匹配 |
| `admission_evidence` | 新增招生文本证据 | 规范实体、来源、适用时间 | 仅追加；不会自动重写既有规则或交通情境 |

## 二、共同字段

| 字段 | 含义及限制 |
|---|---|
| `id` | 稳定规范ID；记录级ID与物理实体ID不同 |
| `legacy_id` / `source_record_id` / `origin_legacy_id` / `destination_legacy_id` | 原命名空间的ID，保留以便定位旧表；脱离namespace不可直接连接 |
| `source_id` / `source_ids` | 来源登记中的ID或JSON列表，不是多个独立来源的自动计数 |
| `source_path` / `reference_path` / `source_locator` | 仓库输入路径、引用该外部来源的材料、原表行号/页码/字段位置；路径相对仓库根目录，`import:<fact_id>`表示导入记录 |
| `verification_status` / `provenance_status` | 证据取得及本地处理状态，不等同“所有事实已被独立确认” |
| `note` / `interpretation_boundary` | 适用范围、缺失及解释边界，必须随下游引用传递 |

## 三、实体与位置字段

- `stage`仅为 `primary` / `kindergarten`，与 `intake_grade` 的 `grade_1` / `small_class`分开。历史原文的 `original_scope`可能同时提到其他学段，但分析记录已切片，不纳入初中对象。
- `ownership`为 `public`、`education_department`、`private`、`other_department`；`organizer_raw`保留原词。`inclusive_status`保留普惠原字段，未记载为 `not_recorded`，不转换成false。
- `housing_description`是带证据限制的住房类型摘录，不是逐套不动产登记，也不是住户收入或阶层。
- `confidence`为 `high` / `medium` / `low`的人工对应等级，**不是概率**。`matched`仅表示同一参考对象的关联可采用，不代表同一入口或每项属性均已核实。
- `unresolved`的 `entity_id`为空，候选放在 `candidate_entity_id`；如K7旧名，不能使用候选ID偷偷加入综合分析。
- `institutions.linkage_status=documented_operator_group`表示仓库已有同一举办主体/园名多园区的记录，不代替法律主体登记；其他同名疑似关系保留各自对象。
- `position_role`区分 `residential_phase_reference`、`development_reference`、`campus_centroid`、`campus_reference`、`transport_origin_poi`、`transport_destination_poi`、`verified_gate`。
- `original_longitude`、`original_latitude`、`original_crs`保留原值。`longitude`、`latitude`统一为WGS84经纬度，`crs=EPSG:4326`，经度在前。`transform`指明identity或版本化GCJ迭代逆变换。
- GCJ数值往返检查仅检验算法实现；不证明实地定位精度。图件使用EPSG:32649米制投影，未把展示XY回填为经纬度。
- `gate_verified=false`为既有位置的默认状态。旧数据没有园校门实测。新增外部 `verified_gate`记录仍需保留其外部声明来源。
- 默认位置优先使用既有OSM参照，其次外部已声明核实的位置，再次已匹配实体的转换POI。相同角色的冲突外部坐标不进入默认位置；不同角色位置不平均。

## 四、住房、费用与时间

住房指标 `metric`：

| 值 | 单位 | 解释 |
|---|---|---|
| `market_reference_sale_cny_m2` | `cny_per_m2` | 平台小区参考值，不是登记成交 |
| `sale_ask_cny_m2` | `cny_per_m2` | 出售挂牌例证 |
| `rent_cny_month` | `cny_per_month` | 单条月租或平台月租汇总；依据 `evidence_type`区分 |
| `rent_cny_m2_month` | `cny_per_m2_month` | 有面积分母的租赁例证 |
| `platform_transaction_sale_cny_m2` | `cny_per_m2` | 平台标示成交，不是住建登记 |
| `policy_rent_cny_m2_month` | `cny_per_m2_month` | 指定房源与申请资格下的政策租金，不能替代市场租金 |

- `value`可空；已知政策零值保留0。`area_m2`来自原广告建筑面积，未取得时为空；`total_ask_cny`仅在有挂牌总价时换算，不补成交总价。
- `comparable_sale=false`用于猎德花园未核出售权利及天銮商住等不宜混排的记录。政策租金、平台成交等其他指标继续分开保存。
- `reference_period`保留原始价格/政策适用时间，可能为月份、日期、历史年份或原文有效期。`observed_on`是已知查询日，不补造交易日期；`evidence_year`是原证据所指年份，不统一改成2026。
- 来源登记中的 `document_date`、`publication_date`、`retrieved_at`各自独立。价格参考月份和成交日期不会自动充当网页发布日期；未知发布日期为空。
- `education_fees.value_status`区分 `known_policy_or_reported_value`、`unknown`、`not_collected`、`externally_reported_verified`等；`actual_charge`只标识园校已记载的当期公示/缴费记录，不表示观察到了某户家庭的总支付。
- `education_fees.amount_relation=lower_bound`如历史新闻中的7000元以上，不解释为精确实收费。
- `actual_charge=false`的政策基准、批复、条件减免和历史新闻不能填补当期实缴缺口。外部导入只有 `evidence_type=published_fee_schedule`或 `actual_receipt`的学费、保教、餐费条目可标记园校当期收费记录。
- F19/F20为有效期覆盖2026的批复，`evidence_year=2024`保留批复适用起点；实际下浮和补贴抵扣未知。F17为2020历史值，F18为2022诉求的后续报道。
- 每学期、每月、每天、每40分钟课时分开；没有月份/课次依据不年化，也不自动减去条件补贴。
- 同一住宅同一展示指标出现不同值或时期时，汇总值留空并标为 `conflicting_or_multiple_periods`。原观察全部保留，等待明确选样决定。

## 五、招生与交通

- 计划的 `subject_type`为 `institution`或 `campus`； `subject_id`按该类型连接。`metric=classes`的 `unit=class`，其他名额指标用 `person`。
- 幼儿园 `social_lottery_total`、`owner_children_places`、`remaining_random_places`彼此有包含关系，不能合计为额外供给，也不能计算中签率。
- `applicability`、`eligibility_text`、`conditions`需原样传给解释者。附近、地段对应、可申请渠道与实际录取为不同层次。
- `transport_routes.distance_m`、`duration_s`来自高德模型。`model_speed_mps=1.25`记录该批模型特征，不是儿童实测步速。公交时间/票价是另列的07:20成人模型；缺方案不是无公交服务。
- `analytical_eligible`表示能否加入本整合层的路线比较。长度异常或目标实体未确认均为false，原记录仍保留。
- `actual_trip_observed=false`、`actual_admission=unobserved`、`actual_commute=unobserved`不可改写成已观察结果。
- `additional_minutes`为示例渠道路线减地址对应基准路线，先按秒计算再换分钟。冼村小学只是一个列明志愿，不是实际分配，也没有证明它是最近可申请学校。
- `escort_scenarios`中的每周两段/四段、步速与票价均为构造情境；无家庭工时、真实接送安排或预算时，不解释为群体负担估计。

## 六、来源、证据与缺口

- `source_registry.availability`为 `archived`、`multipart_archive`、`reference_only`或 `unavailable`。哈希验证检查的是保存载体完整性，不代表每个来源中的事实均正确。
- `canonical_source_id`用于提示相同字节或规范URL的重复引用；通知与附件等同一文件链仍需要解释者判断独立性。
- `external_declared_verified`表示GPT Work输入声明已核实，本模块没有重新上网研究。其未提供本地原件时仍为 `reference_only`。
- `supporting_data`中的 `table:id`可直接定位到输出CSV的主键；证据矩阵的每项引用都经外键检查。
- `research_gaps.status`包括 `open`、`supplemented_requires_review`、`retired_scope_erratum`及 `archive_available_multipart`。历史G12已在新层退役，原缺口表不改动；历史G15初中分流不进入当前缺口任务。
- `research_gaps.occurrences`记录同一问题被登记的次数，避免重复事实冲突产生重复主键；所有冲突原始行仍分别保留在待核表，不合并其数值或作事实裁决。

## 七、推荐连接顺序

1. 从 `residences.id`和 `education_campuses.id`进入，各自用默认位置ID连接 `positions`。
2. 用 `transport_routes.residence_id/campus_id`建立案例路线关系，先筛 `analytical_eligible=true`。
3. 通过 `campus_admission_rules`与 `fee_applicability`连接规则和费用，保留一对多关系。
4. 住房数值从 `housing_observations`按指标与时间选择；快速展示可使用已保留冲突状态的 `residence_cost_summary`。
5. 如需已连接的一行一条路线视图，使用 `housing_education_links`，不要把规则/费用展开后对距离或房价再求和。
6. 报告引用从 `evidence_matrix`开始，逐条追踪数据ID、来源ID及解释边界。

上游来源与实体已被固定登记，下游不得按中文名称模糊连接、用候选位置覆盖正式对象、把同源副本当新增样本或将费用缺失填零。
