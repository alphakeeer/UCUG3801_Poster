# 独立研究审查响应

审查基准：`5101aa7ca61e0d2ddeff85a8209d9cf126a33508`，用户提供的GPT Work Independent Research Review。

修正数据版本：`d6985fc1330d4db8652816874335016d73c8ecbdcbf5f5746c1f595f6a35e0c0`。不更改原研究资料或其他组员文件。

|问题|处置|验收位置|
|---|---|---|
|通用规则被误读为住宅家庭资格|联表重命名reference_*并仅作证据索引；住宅×园区×渠道另表，资格未知不计数|admission_channel_contexts；reference_links_do_not_decide_eligibility测试|
|金穗本园2026业主名额为0|一般派位与业主渠道分开，业主渠道明确该年公布计划0，不赋予邻近住宅优先|K5_zero_owner_plan测试|
|历史或推定费用挂接状态为空|费用增加evidence_layer；挂接状态全部显式标为reference_only，净额不填|fee_layers_never_imply_affordability测试|
|图B混用住房报价；图A定位偏样与价格色阶|双系列英文路线主图，无住房数值；定位图无价格编码，按学段列分母；旧P03候选仅源表保留|FIGURE_LEGENDS；图件源数据与PNG/PDF核验|
|K7已关联但F08理由仍混含身份未确认|F08改为长度异常；42条明确39普通、2旧名匹配补充、1异常排除|route_quality_strata测试|
|兴国容量预警年份混淆|2025文件针对2026，2026文件针对2027；实际超额和改派未知|capacity_notices；warning_years_and_unobserved_outcomes测试|
|港澳小学安排被写成其他学段志愿逻辑|只保留公示后积分顺序安排至南国小学部、45人封顶；个人结果未观察|HK_primary_allocation_not_junior_preferences测试|
|字典39/36旧数量与当前42/41不一致|更新粒度、字段迁移、路线分组及主图6路线/补充3行/全部8独立路线|DATA_DICTIONARY；路线去重与外键检查|
|配套范围、核心园实价、实际门点与家庭结果缺失|保留限定研究局限，不补值、不无限扩展采集|FINAL_EVIDENCE_BRIEF及research_gaps|

2025细则本轮下载返回403，来源登记为仅引用并标明沿用独立审查；2026归档PDF第10页的2027预警及港澳小学指引已核对。没有将无法重取原件改标为本地已归档。

可保留的局限：目的性样本与定位不均、门点未实测、配套范围未取得、净费用和家庭结果未观察。这些限制随最终简报和图注交接，不再扩展采集。
