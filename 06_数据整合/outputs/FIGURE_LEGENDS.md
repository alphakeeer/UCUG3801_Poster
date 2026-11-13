# 中文图注与图件源数据

## 图 A｜住房与幼儿园、小学的空间分布

离线OSM参照图叠加已定位住宅及园校候选子集。住宅蓝色深浅表示归档平台参考价，单位万元/平方米，参考月份不同；不是登记成交，也不用于家庭收入分类。白色表示参考价缺失或不可比，猎德花园菱形为五区参照点，与海文路交通起点分开。租金例证另用元/平方米/月，不按不同面积、日期的挂牌计算小区均价。南国花园有两条新增整租例证，但小区参考价仍缺失。

园校形状区分小学与幼儿园，颜色区分办学类别。空心表示经过GCJ-02到WGS84转换的园校POI；灰叉为未确认候选，不计入已接受位置。K7旧地图别名已由2026官方地址与同一POI支持关联，实际园门和配套范围仍未核。华文为国企办园、海滨为普惠性民办，均为原有候选的补充定位。图未绘房价插值面，未推断学校质量、官方服务边界或因果关系。底图署名：© OpenStreetMap贡献者，ODbL。

源数据：`figure_source_data/figure_A_housing.csv`、`figure_A_campuses.csv`、`figure_A_unresolved.csv`，含规范ID与来源引用。原值及位置角色另见 `data/housing_observations.csv`、`data/positions.csv`、`data/work_evidence.csv`和 `data/source_registry.csv`。

## 图 B｜住房背景、招生渠道与步行可达性

九条住宅—申请渠道比较对应三个目的性案例起点。地址对应小学须核完整资格；拆迁安置及合格租户分别依其条件进入统筹，去向未观察。冼村小学只是一个积分名单内志愿例，不代表实际录取或已证明的最近可申请校。南国学校小学部另列港澳渠道。住房标签为不同类型的背景证据，不能解释为家庭收入。南国花园两条整租挂牌分别为2026-09-20与2026-11-10的个案，不合成均价。

时间为2026-11-12高德POI到POI单程模型估算，实际接送门及通学没有实测。11月13日新增三条幼儿园路线另存，未改变本图九条小学比较和原六园敏感性分母。南国花园至海滨园298米、238秒约4.0分钟，仅为扩展已测候选的最近值，不推断整个地区或实际可录取范围。没有总体统计检验、误差条或置信区间。

源数据：`figure_source_data/figure_B_comparisons.csv`和 `figure_B_housing_context.csv`，经路线、住房观察、住宅和规则ID连接到 `data/transport_routes.csv`、`data/housing_observations.csv`、`data/admission_rules.csv`、`data/admission_conditions.csv`和 `data/source_registry.csv`。
