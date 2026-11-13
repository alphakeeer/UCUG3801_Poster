# GPT Work Verified Facts CSV 导入接口

新增事实放入本模块，不修改任何旧原件、报告或CSV。先复制 [空白模板](config/verified_facts_template.csv)，一行一个可核对的事实。

## 导入与重新生成

```bash
06_数据整合/.venv/bin/python 06_数据整合/run.py import-csv /absolute/path/verified_facts.csv
06_数据整合/.venv/bin/python 06_数据整合/run.py all
06_数据整合/.venv/bin/python 06_数据整合/run.py validate
```

`import-csv`检查CSV列与格式，将原字节保存为 `inbox/facts-<完整SHA256>.csv`。同一文件重复导入不会增加副本，不会覆盖不同内容。`all`逐行处理，接受的事实进入 `outputs/data/verified_facts.csv`，不安全的记录进入 `import_quarantine.csv`并登记研究缺口。

格式缺列或CSV错列会使构建停止；单行事实的未知实体、未核实状态、非法数值、单位错误或来源冲突会被隔离，其余既有证据仍可生成。不得将“构建通过”误读为所有补证行都已被采用；必须查看 `quarantine_count`及待核表。

## 必须保留的列

模板中所有列都需要存在；允许为空的值见下表。保存UTF-8 CSV，JSON值请交由表格软件或Python `csv.DictWriter`正确加引号。

| 列 | 填写方式 |
|---|---|
| `fact_id` | 全球唯一且稳定的事实ID，如 `GW-20261114-001`。内容修订使用新ID，不复用旧ID覆盖 |
| `subject_type` | `residence` / `campus` / `institution` / `rule` |
| `subject_id` | 必须用规范ID，查 `residences.csv`、`education_campuses.csv`等。名称不能代替ID |
| `predicate` | 使用下表支持的谓词 |
| `value` | 非负有限数字、完整WGS84位置JSON或文本；不以0表示未知 |
| `unit` | 数值及坐标必须用下表单位；文本可空 |
| `reference_period` | 事实实际适用年份、月份或日期；不要用核验日期替换历史年份 |
| `stage` | 园校事实必须与实体一致，填 `primary` / `kindergarten`；一般住宅事实可空 |
| `source_id` | 已登记的来源ID；新增来源可空并提供URL。不要占用与另一个URL绑定的ID |
| `source_url` | 新来源必须填；若已有source_id且不重复提供URL，可空。提供时必须与已登记ID一致 |
| `source_title` | 新来源必须填，已登记来源可空 |
| `source_locator` | 原件页码、表号、行号、条款或公示位置，必须填 |
| `evidence_type` | 如 `official_notice`、`published_fee_schedule`、`actual_receipt`、`platform_quote`、`field_observation`、`estimated`；不把估计写成实测 |
| `verification_status` | 外部事实采用时必须为 `verified`；pending等状态会保留在待核表 |
| `verified_on` | ISO日期 `YYYY-MM-DD`，是核验日，不是事实有效期 |
| `verified_by` | 核验者或工作流名，必须填；不要求居民姓名 |
| `notes` | 适用对象、附加收费、政策条件、证据限制；可以为空 |

## 当前支持的谓词

| predicate | subject_type | unit | 输出 |
|---|---|---|---|
| `housing_reference_price_cny_m2` | residence | `cny_per_m2` | 住房平台参考值 |
| `housing_rent_cny_month` | residence | `cny_per_month` | 月租记录 |
| `housing_rent_cny_m2_month` | residence | `cny_per_m2_month` | 有面积分母的单位租金 |
| `policy_rent_cny_m2_month` | residence | `cny_per_m2_month` | 资格限定政策租金，单独指标 |
| `tuition_cny_term` | campus | `cny_per_person_term` | 学费条目 |
| `care_fee_cny_month` | campus | `cny_per_person_month` | 保教费条目 |
| `meal_fee_cny_month` | campus | `cny_per_person_month` | 伙食费条目 |
| `subsidy_cny_term` | campus | `cny_per_person_term` | 条件补贴条目，不自动抵扣其他费用 |
| `coordinate_wgs84` | residence / campus | `degrees` | 追加位置及角色，不覆盖旧坐标 |
| `admission_note` | 任一已知subject_type | 可空 | 新增招生文本证据，不自动修改规则或情境 |
| `research_gap` | 任一已知subject_type | 可空 | 新增研究缺口 |

坐标的 `value`使用如下JSON结构：

```json
{"longitude": 113.33, "latitude": 23.12, "position_role": "campus_reference"}
```

上例仅说明格式，不是研究证据。可用角色见数据字典。这里只接收已明确为WGS84的数据；GCJ-02输入不能伪标成WGS84，应先由维护者增加保留原坐标的适配器。

## 对应与冲突处理

- 未知实体或只写名称：进入 `unresolved_entity_id`待核；维护者确认对象并补充registry/crosswalk后再处理，绝不自动模糊匹配。
- 当前registry针对现有18住宅、43园校建立。新设施首先需要维护者按同一机构/园区/学段规则登记，不通过导入CSV绕过身份核验。
- 同一fact_id、相同内容：只应用一次，记录忽略的副本数。
- 同一fact_id、不同内容：所有冲突版本均隔离，不采取先到先得。
- 同一住宅展示指标出现不同数值或时期：全部原观察保留，展示汇总留空并提示人工选择；不自动取最新、平均或更高置信来源。
- 同一实体同一位置角色的不同坐标：新位置只作冲突候选，既有默认位置不变。不同角色的位置继续分开。
- 新收费记录追加到政策与采集状态旁。只有公示或收据类型可标记当期收费记录；不能把estimated条目当已支付费用。
- 外部核验状态记为 `external_declared_verified`。本模块不会重复互联网研究；没有本地原件的来源仍标 `reference_only`。
- 原始文件及旧报告一直不变。整合层每次重生成有 `data_version`和输出哈希，已提交的v1结果可通过Git追溯。

不要在CSV中加入姓名、证件号、儿童身份或精确家庭住址；研究对象使用已登记的公开住宅项目、园校及匿名规则情境。
