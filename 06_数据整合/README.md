# UCUG3801 研究数据整合

**最终交接入口：[四条核心发现简报](outputs/FINAL_EVIDENCE_BRIEF.md) · [审查响应](outputs/REVIEW_RESPONSE.md)。**

独立、离线、可追溯的数据整合层。仅分析幼儿园与小学，保留旧原件、报告、地图及海报的既有路径。已整合远端 `a3dc7c6` 的45条GPT Work补证；中文报告从[研究交接](outputs/HANDOFF.md)及[补证整合报告](outputs/补证整合报告.md)开始阅读。

## 运行

使用 Python 3.13。本模块核心数据处理只用标准库；完整图件环境按锁定依赖安装。

```bash
uv venv 06_数据整合/.venv --python python3.13
uv pip install --python 06_数据整合/.venv/bin/python -r 06_数据整合/requirements.txt
# 中文图件需要文泉驿正黑TrueType字体，版本见config/figure_font.json。
# 默认字体目录/usr/share/fonts/truetype/wqy，可用LIEDE_FONTS_DIR指定。
# 首次运行可记录所有现有工作文件；已存在的保护基线不会被覆盖。
06_数据整合/.venv/bin/python 06_数据整合/run.py protect
06_数据整合/.venv/bin/python 06_数据整合/run.py all
06_数据整合/.venv/bin/python 06_数据整合/run.py validate
```

`build`生成标准化表与证据矩阵；`all`同时生成综合图件。运行位置不受当前工作目录影响。

## 结构与数据流

```text
06_数据整合/
  config/          已登记输入哈希、人工实体对应、增补事实及导入模板
  src/             来源、实体、坐标、招生费用、交通、导入、分析与校验
  inbox/           后续补证 CSV 的不可变副本
  tests/           领域规则与导入回归测试
  outputs/         派生 CSV、来源与质量报告、图件及图件源数据
  .state/          仅本机的现有工作文件保护基线，不提交
```

现有研究文件 → 输入与来源哈希校验 → 实体对应与坐标规范化 → 招生、收费、住房与交通独立事实表 → 补证追加及冲突登记 → 综合分析与证据矩阵 → 校验 → 模块内输出。

交通复现脚本复制到系统临时目录，以 `--no-figure`运行。不会运行旧地图生成器或海报导出器。输出在独立临时目录完成校验后写入本模块；拒绝把输出指向其他组员目录。

## 使用边界

- 住宅是开发项目层对象，位置点另外保存角色。猎德花园五区点与交通海文路POI分别保留。
- 园区/校区不合并。机构总计划只保存一次，班数与人数及派位组成项分别保存。
- K7旧名已由官方同址及同一高德POI支持关联；D1/D2相关路线可连接，D3→K7的18米异常继续排除。配套范围和接送门仍未知。
- 原始GCJ-02与WGS84坐标同时保留，分析坐标为EPSG:4326；转换不能证明校门准确。
- 住房报价是仓库冻结摘录，不代表实时成交，也不是家庭收入。缺失不补零，不按相近小区代填。
- 补证按事实追加，不覆盖原表或自动替代冲突值；独立来源是否已归档另行标记。

## 交付入口

- [研究交接与证据包](outputs/HANDOFF.md)：给理论组、报告组和海报组的最短阅读入口。
- [图 A：样本定位附图](outputs/figures/figure_A_housing_education.png) · [图 B：双系列路线主图](outputs/figures/figure_B_admission_accessibility.png)。同目录另有可编辑SVG和PDF。
- [表 C：跨领域证据矩阵](outputs/table_C_evidence_matrix.md)及[CSV版](outputs/data/evidence_matrix.csv)。
- [字段字典与关联口径](DATA_DICTIONARY.md) · [GPT Work导入接口](IMPORT_VERIFIED_FACTS.md) · [图件论证与导出约定](FIGURE_CONTRACT.md)。
- [数据质量摘要](outputs/QUALITY_SUMMARY.md) · [完整自动检查](outputs/quality_report.json) · [缺失及冲突](outputs/data/research_gaps.csv)。
- [复现与图件核验记录](VERIFICATION.md)。

完整的标准化表在 `outputs/data/`，七张基础表及机构、位置、住房观察、计划、对应关系均有独立CSV。`outputs/schemas.json`给出本次全部列、值类型与空值情况。

## 自动检查与版本追溯

```bash
06_数据整合/.venv/bin/python -m unittest discover -s 06_数据整合/tests -v
06_数据整合/.venv/bin/python 06_数据整合/run.py validate
```

检查包括固定原件及输入哈希、原工作文件保护、实体和证据外键、学段范围、坐标转换、异常路线排除、机构计划去重、缺失与政策零值区别、旧交通脚本复现和生成物完整性。已知研究缺口单独记录，不以填值方式让检查“通过”。

每次构建的 `run_manifest.json`记录代码/配置/输入生成的 `data_version`及派生文件SHA-256。修改代码或导入事实后需要重建；`validate`也会发现过期或被手工改动的输出。保护基线已有时无需再次运行 `protect`。

本轮原格式补证保留在远端原路径，由 `src/liede_pipeline/work_evidence.py`显式适配，完整输出至 `work_evidence.csv`，不伪装成通用模板的 `verified`记录。新增内容包括K7别名对应、两园补定位、三条定向路线、南国花园五条数值观察及七条细分招生条件。历史收费与政策推定不进入实际收费。`inbox/`继续接收后续标准格式补证。

已有材料中的誉城苑政策租金作为带原报告出处和限制的本地注释保存，明确标为仓库报告转述，未重新联网核验。字段名、ID和枚举代码保留稳定英文接口，面向团队的报告和图注使用中文；按独立审查建议，主路线图使用英文双系列、不展示住房成本，定位附图使用中文。图件和证据包不代表家庭实证或全地区普查。


## 最终交接与字段迁移

- 联表41行改为证据索引：旧rule_ids、admission_condition_ids、fee_ids分别改为reference_rule_ids、reference_condition_ids、reference_fee_evidence_ids；住房单值移回观察表，不能计数“可申请/可负担校园”。
- 新增admission_channel_contexts，按住宅×园区×渠道×家庭条件列背景。金穗本园业主计划0和一般派位分开；所有个人资格均未知。
- 费用按政策、批复、公示、历史、推定、实缴等分层，挂接状态非空，家庭总净额不补零。
- 路线42条分39普通POI、2条K7旧名匹配补充、1条异常排除。图B只取六条双系列路线，港澳三行另列。
- 最终数据版本见outputs/run_manifest.json；最终Git合并记录见RELEASE_RECORD.md。原始材料、其他组员报告和海报不改动，旧版5101aa7可由Git读取。
