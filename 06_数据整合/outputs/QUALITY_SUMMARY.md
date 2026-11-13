# 最终数据质量摘要

数据版本：`d6985fc1330d4db8652816874335016d73c8ecbdcbf5f5746c1f595f6a35e0c0`。构建检查404项，失败0项。

- 原输入和工作文件受保护，旧交通四张CSV在临时目录复算一致。
- 路线分组：{'ordinary_poi_estimate_gate_unverified': 39, 'legacy_name_address_matched_poi_gate_unverified': 2, 'excluded_subchord_distance': 1}；所有42条补算WGS84端点直距，D3→K7异常仍排除。
- 通用规则与费用仅供参考；渠道背景表单列，个人资格、家庭净支出均未知，不生成可申请或可负担园校计数。
- 金穗本园2026业主计划0与一般派位分开；收费类型和年份明确，不以缺失替代零。
- 当前102条质量追踪包括历史退役项；开放项按优先级为{'P0': 81, 'P1': 18}。不通过无限补资料追求空缺口表。
- 核对43园校/41机构、计划粒度、坐标和来源；原45条补证保留原核验标签与年份。
- 图A去价格色阶并分学段写定位分母；图B只绘六条双系列路线，不混住房成本或实际录取。

详细检查见 `quality_report.json`，字段见 `schemas.json`，输入/输出哈希见 `run_manifest.json`，限制见[最终简报](FINAL_EVIDENCE_BRIEF.md)。
