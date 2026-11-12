# 猎德教育资源交通可达性调查

UCUG3801 · Social Inequality and Social Mobility · 两轮综合 · 2026 年 11 月 12 日

本报告比较猎德花园、中海璟晖华庭和南国花园三个住宅样本到附近小学及幼儿园的路线，并用招生地段、办园类型与收费政策解释可步行到达的设施如何转化为家庭可使用的教育选择。三个样本均可在 9 分钟内步行到至少一个公办样本园区，交通差异主要随目的地改变。本研究的证据范围是地图规划与官方资料。

## 主要发现

1. **三个样本点附近都有步行可达的幼儿园。** 到六处样本中最近园区的估计用时为 **3.6–6.5 分钟**，到最近公办园区为 **3.6–8.6 分钟**。但跨片区到同一所园可能远得多。例如，中海璟晖华庭到万锦幼儿园是 **269 米／3.6 分钟**，南国花园到同一园是 **2,204 米／29.4 分钟**。
2. **三个住宅的地段对应小学均是各自四所样本小学中最近的一所。** 猎德花园到猎德实验小学部为 **5.9 分钟**，中海璟晖华庭到兴国小学为 **10.1 分钟**，南国花园到南国学校小学部为 **2.8 分钟**。三者的地址对应关系有 2026 年招生地段依据，家庭资格仍需核验。[天河区招生文件，附件 5 第 18、55、56 行](https://www.thnet.gov.cn/attachment/8/8016/8016210/10791180.pdf)
3. **住宅性质无法给出统一的交通排序。** 回迁住宅猎德花园离猎德幼儿园最近，两处商品住宅分别离万锦和力迅上筑幼儿园最近。只看公办园，猎德花园的最近路线较短，两个商品住宅样本约为 8.5–8.6 分钟。把目的地固定在东侧的海明小学，南国花园反而有最短路线。
4. **步行范围内的供给数量不等于可负担、可申请的学位。** 10 分钟内分别有 **1、3、2 个样本园区**，每个住宅点均有 **1 个公办样本园区**。六处园区均未取得可核验的 2026 年园区级小班或中班具体收费公示。教育部门办园的小班派位和业主子女优先条件会进一步改变可申请的选项。[2026 年公办园派位计划](https://www.thnet.gov.cn/gzjg/qzf/qjyj/zsks/content/post_10815546.html) · [2026 年幼儿园招生方案](https://www.thnet.gov.cn/gzjg/qzf/qjyj/zsks/content/post_10777181.html)

## 研究范围和证据口径

| 轮次 | 研究范围 | 路线查询 |
|---|---|---|
| 第一轮 | 3 个住宅点、4 所小学、6 个幼儿园园区。对 4 所小学和其中 2 所幼儿园算路。 | 12 条小学路线、6 条幼儿园路线，保留未设出发时间的公共交通估算。 |
| 第二轮 | 复查 13 个地点编号与坐标，核对招生地段、园区类别、收费依据与公交站更名。 | 新增 12 条幼儿园路线，补齐 30 条路线。以周四 07:20 出发复查全部组合的公交。 |

两轮的点位和路线均保存在数据集中。[第一轮原始 JSON](data/round-1/liede-transport-accessibility-2026.json) 按原文件字节归档。[第二轮完整 JSON](data/round-2/liede-accessibility-round-2.json) 保留第一轮的路线字段，并为每条路线增列早间公交结果。地图起终点是住宅与园校的地点标记（POI）。步行米数是高德路网长度，分钟是高德估计的单程时间。10、15、20 分钟阈值用原始秒数计算，包含恰好等于阈值的路线。地图只展示样本点，不划定行政边界、服务区或招生边界。[高德路线规划说明](https://lbs.amap.com/api/webservice/guide/api/direction)

- **官方文件**提供园校分类、地址或招生地段、学位计划、公交站改名范围和票务规则。
- **高德估算**提供地图点位、步行线路及时间、公交线路与规划时间。公交网页显示的票价单列为平台报价。
- **现场证据缺口**包括实际使用的住宅行人门、园校接送门、过街等待、临时封闭、早间等车及车上拥挤。本报告不把任一线路标为已实测。

## 样本地点

13 个点位沿用第一轮高德编号，坐标复查一致。地址差异及行人出入口的核查状态见下文。
样本选取用于空间比较，课程最终社区比较对象仍由小组按教学要求确定。

| 编号 | 地点 | 类型 | 地址 |
|---|---|---|---|
| D1 | [猎德花园](https://ditu.amap.com/place/B0FFFQLHZ6) | 回迁住宅 | 珠江新城海文路1–53号 |
| D2 | [中海璟晖华庭](https://ditu.amap.com/place/B00140TYWA) | 商品住宅（含商业） | 猎德大道31号 |
| D3 | [南国花园](https://ditu.amap.com/place/B00140UF9T) | 商品住宅 | 珠江新城平月路 |
| S1 | [广州市天河中学猎德实验学校小学部](https://ditu.amap.com/place/B0FFF3UT6N) | 公办九年一贯制学校小学部 | 海清路海定街1号 |
| S2 | [广州市天河区体育东路小学海明学校](https://ditu.amap.com/place/B0FFFRHN58) | 公办小学 | 上筑街2号 |
| S3 | [广州市天河区体育东路小学兴国学校](https://ditu.amap.com/place/B00140TZ2K) | 公办小学 | 兴国路26号 |
| S4 | [广州市南国学校小学部](https://ditu.amap.com/place/B00141IKVW) | 公办九年一贯制学校小学部 | 平月路200号 |
| K1 | [广州市天河区珠江新城猎德幼儿园](https://ditu.amap.com/place/B0FFF3USY7) | 教育部门办幼儿园 | 海月路33号 |
| K2 | [广州市天河区万锦幼儿园](https://ditu.amap.com/place/B0FFGY5J2S) | 普惠性民办幼儿园 | 猎德大道31号之六 |
| K3 | [广州市天河区佐治亚幼儿园](https://ditu.amap.com/place/B0FFG8FWWZ) | 普惠性民办幼儿园 | 金穗路68号 |
| K4 | [广州市天河区力迅上筑幼儿园](https://ditu.amap.com/place/B00140UR2W) | 普惠性民办幼儿园 | 上筑街1号 |
| K5 | [广州市天河区金穗幼儿园](https://ditu.amap.com/place/B0FFF3V19U) | 教育部门办幼儿园 | 金穗路73号 |
| K6 | [广州市天河区金穗幼儿园花城园区](https://ditu.amap.com/place/B0FFL64EY3) | 教育部门办幼儿园 | 平江路9号 |

## 交通数据与海报材料

- [Figure 1 · Educational accessibility in Liede](figures/figure-1-educational-accessibility-map.png)
- [Figure 2 · Walking access to kindergartens](figures/figure-2-kindergarten-walking-access.png)
- [Figure 3 · Walking access to catchment primary schools](figures/figure-3-primary-school-walking-access.png)
- [第二轮 JSON 数据与线路复查记录](data/round-2/liede-accessibility-round-2.json)

### Table 1 · Complete residential-to-kindergarten routes

**查询与模式。** 步行查询日期为 2026 年 11 月 12 日。公交用高德网页版模拟同日（周四）07:20 出发。30 条住宅—园校组合中，20 条返回可读公交方案，10 条显示无方案，0 条未获取。18 条幼儿园组合中有 12 条返回方案。表列高德推荐列表中第一条可读乘车方案，预计到达由出发时刻加页面显示时长计算。表中路口和道路为现场核查位置。票价按网页单次规划显示值记录。[高德网页规划帮助](https://www.amap.com/ssr/doc/route-plan)

| Residence | Kindergarten | Walk m / min | Transit · boarding → alighting | Transit min / ETA | Fare | Transfers | Road junctions to check | Amap · 12 Nov 2026 |
|---|---|---:|---|---:|---:|---:|---|---|
| Liede Garden | K1 Liede | 273 / 3.6 | 未返回方案 | — | — | — | 海文路—海月路 | [Walk](https://uri.amap.com/navigation?from=113.336127,23.113409&to=113.337456,23.114648&mode=walk&src=liede-fieldwork) · [Transit](https://ditu.amap.com/ssr/dir?fname=%E7%8C%8E%E5%BE%B7%E8%8A%B1%E5%9B%AD&flat=23.113409&flon=113.336127&dname=%E5%B9%BF%E5%B7%9E%E5%B8%82%E5%A4%A9%E6%B2%B3%E5%8C%BA%E7%8F%A0%E6%B1%9F%E6%96%B0%E5%9F%8E%E7%8C%8E%E5%BE%B7%E5%B9%BC%E5%84%BF%E5%9B%AD&dlat=23.114648&dlon=113.337456&type=1&policy=0&dateTime=2026-11-12%7C07-20) |
| Liede Garden | K2 Wanjin | 1,517 / 20.2 | 777路 · 临江大道 → 猎德 | 26 / 07:46 | ¥2 | 0 | 猎德大道—花城大道，金穗路辅路 | [Walk](https://uri.amap.com/navigation?from=113.336127,23.113409&to=113.332259,23.121804&mode=walk&src=liede-fieldwork) · [Transit](https://ditu.amap.com/ssr/dir?fname=%E7%8C%8E%E5%BE%B7%E8%8A%B1%E5%9B%AD&flat=23.113409&flon=113.336127&dname=%E5%B9%BF%E5%B7%9E%E5%B8%82%E5%A4%A9%E6%B2%B3%E5%8C%BA%E4%B8%87%E9%94%A6%E5%B9%BC%E5%84%BF%E5%9B%AD&dlat=23.121804&dlon=113.332259&type=1&policy=0&dateTime=2026-11-12%7C07-20) |
| Liede Garden | K3 Zuozhiya | 1,698 / 22.6 | 293路 · 临江大道 → 冼村路中 | 28 / 07:48 | ¥2 | 0 | 猎德大道—花城大道，兴盛路—兴盛直街 | [Walk](https://uri.amap.com/navigation?from=113.336127,23.113409&to=113.329152,23.122236&mode=walk&src=liede-fieldwork) · [Transit](https://ditu.amap.com/ssr/dir?fname=%E7%8C%8E%E5%BE%B7%E8%8A%B1%E5%9B%AD&flat=23.113409&flon=113.336127&dname=%E5%B9%BF%E5%B7%9E%E5%B8%82%E5%A4%A9%E6%B2%B3%E5%8C%BA%E4%BD%90%E6%B2%BB%E4%BA%9A%E5%B9%BC%E5%84%BF%E5%9B%AD&dlat=23.122236&dlon=113.329152&type=1&policy=0&dateTime=2026-11-12%7C07-20) |
| Liede Garden | K4 Lixun Shangzhu | 884 / 11.8 | 138路 · 临江大道 → 马场路南 | 20 / 07:40 | ¥2 | 0 | 海文路—海月路，海风路—海风横街 | [Walk](https://uri.amap.com/navigation?from=113.336127,23.113409&to=113.341996,23.115182&mode=walk&src=liede-fieldwork) · [Transit](https://ditu.amap.com/ssr/dir?fname=%E7%8C%8E%E5%BE%B7%E8%8A%B1%E5%9B%AD&flat=23.113409&flon=113.336127&dname=%E5%B9%BF%E5%B7%9E%E5%B8%82%E5%A4%A9%E6%B2%B3%E5%8C%BA%E5%8A%9B%E8%BF%85%E4%B8%8A%E7%AD%91%E5%B9%BC%E5%84%BF%E5%9B%AD&dlat=23.115182&dlon=113.341996&type=1&policy=0&dateTime=2026-11-12%7C07-20) |
| Liede Garden | K5 Jinsui | 1,467 / 19.6 | 777路 · 临江大道 → 猎德 | 31 / 07:51 | ¥2 | 0 | 猎德大道—花城大道，金穗路辅路—海御直街 | [Walk](https://uri.amap.com/navigation?from=113.336127,23.113409&to=113.334724,23.123746&mode=walk&src=liede-fieldwork) · [Transit](https://ditu.amap.com/ssr/dir?fname=%E7%8C%8E%E5%BE%B7%E8%8A%B1%E5%9B%AD&flat=23.113409&flon=113.336127&dname=%E5%B9%BF%E5%B7%9E%E5%B8%82%E5%A4%A9%E6%B2%B3%E5%8C%BA%E9%87%91%E7%A9%97%E5%B9%BC%E5%84%BF%E5%9B%AD&dlat=23.123746&dlon=113.334724&type=1&policy=0&dateTime=2026-11-12%7C07-20) |
| Liede Garden | K6 Jinsui · Huacheng | 1,500 / 20.0 | 777路 · 临江大道 → 花城大道站 | 26 / 07:46 | ¥2 | 0 | 海文路—平月路，平江路 | [Walk](https://uri.amap.com/navigation?from=113.336127,23.113409&to=113.347319,23.116220&mode=walk&src=liede-fieldwork) · [Transit](https://ditu.amap.com/ssr/dir?fname=%E7%8C%8E%E5%BE%B7%E8%8A%B1%E5%9B%AD&flat=23.113409&flon=113.336127&dname=%E5%B9%BF%E5%B7%9E%E5%B8%82%E5%A4%A9%E6%B2%B3%E5%8C%BA%E9%87%91%E7%A9%97%E5%B9%BC%E5%84%BF%E5%9B%AD%E8%8A%B1%E5%9F%8E%E5%9B%AD%E5%8C%BA&dlat=23.11622&dlon=113.347319&type=1&policy=0&dateTime=2026-11-12%7C07-20) |
| Zhonghai Jinghui Huating | K1 Liede | 1,361 / 18.1 | 138路 · 兴盛路口 → 临江大道 | 31 / 07:51 | ¥2 | 0 | 猎德大道辅路—花城大道，海月路 | [Walk](https://uri.amap.com/navigation?from=113.332723,23.121608&to=113.337456,23.114648&mode=walk&src=liede-fieldwork) · [Transit](https://ditu.amap.com/ssr/dir?fname=%E4%B8%AD%E6%B5%B7%E7%92%9F%E6%99%96%E5%8D%8E%E5%BA%AD&flat=23.121608&flon=113.332723&dname=%E5%B9%BF%E5%B7%9E%E5%B8%82%E5%A4%A9%E6%B2%B3%E5%8C%BA%E7%8F%A0%E6%B1%9F%E6%96%B0%E5%9F%8E%E7%8C%8E%E5%BE%B7%E5%B9%BC%E5%84%BF%E5%9B%AD&dlat=23.114648&dlon=113.337456&type=1&policy=0&dateTime=2026-11-12%7C07-20) |
| Zhonghai Jinghui Huating | K2 Wanjin | 269 / 3.6 | 未返回方案 | — | — | — | 内部路段，反向经金穗路辅路 | [Walk](https://uri.amap.com/navigation?from=113.332723,23.121608&to=113.332259,23.121804&mode=walk&src=liede-fieldwork) · [Transit](https://ditu.amap.com/ssr/dir?fname=%E4%B8%AD%E6%B5%B7%E7%92%9F%E6%99%96%E5%8D%8E%E5%BA%AD&flat=23.121608&flon=113.332723&dname=%E5%B9%BF%E5%B7%9E%E5%B8%82%E5%A4%A9%E6%B2%B3%E5%8C%BA%E4%B8%87%E9%94%A6%E5%B9%BC%E5%84%BF%E5%9B%AD&dlat=23.121804&dlon=113.332259&type=1&policy=0&dateTime=2026-11-12%7C07-20) |
| Zhonghai Jinghui Huating | K3 Zuozhiya | 567 / 7.6 | 未返回方案 | — | — | — | 金穗路辅路，兴盛直街 | [Walk](https://uri.amap.com/navigation?from=113.332723,23.121608&to=113.329152,23.122236&mode=walk&src=liede-fieldwork) · [Transit](https://ditu.amap.com/ssr/dir?fname=%E4%B8%AD%E6%B5%B7%E7%92%9F%E6%99%96%E5%8D%8E%E5%BA%AD&flat=23.121608&flon=113.332723&dname=%E5%B9%BF%E5%B7%9E%E5%B8%82%E5%A4%A9%E6%B2%B3%E5%8C%BA%E4%BD%90%E6%B2%BB%E4%BA%9A%E5%B9%BC%E5%84%BF%E5%9B%AD&dlat=23.122236&dlon=113.329152&type=1&policy=0&dateTime=2026-11-12%7C07-20) |
| Zhonghai Jinghui Huating | K4 Lixun Shangzhu | 1,660 / 22.1 | Metro L5 · 猎德 (C口) → 潭村 (A口) | 29 / 07:49 | ¥2 | 0 | 猎德大道—花城大道，海风路 | [Walk](https://uri.amap.com/navigation?from=113.332723,23.121608&to=113.341996,23.115182&mode=walk&src=liede-fieldwork) · [Transit](https://ditu.amap.com/ssr/dir?fname=%E4%B8%AD%E6%B5%B7%E7%92%9F%E6%99%96%E5%8D%8E%E5%BA%AD&flat=23.121608&flon=113.332723&dname=%E5%B9%BF%E5%B7%9E%E5%B8%82%E5%A4%A9%E6%B2%B3%E5%8C%BA%E5%8A%9B%E8%BF%85%E4%B8%8A%E7%AD%91%E5%B9%BC%E5%84%BF%E5%9B%AD&dlat=23.115182&dlon=113.341996&type=1&policy=0&dateTime=2026-11-12%7C07-20) |
| Zhonghai Jinghui Huating | K5 Jinsui | 640 / 8.5 | 未返回方案 | — | — | — | 金穗路辅路—海御直街 | [Walk](https://uri.amap.com/navigation?from=113.332723,23.121608&to=113.334724,23.123746&mode=walk&src=liede-fieldwork) · [Transit](https://ditu.amap.com/ssr/dir?fname=%E4%B8%AD%E6%B5%B7%E7%92%9F%E6%99%96%E5%8D%8E%E5%BA%AD&flat=23.121608&flon=113.332723&dname=%E5%B9%BF%E5%B7%9E%E5%B8%82%E5%A4%A9%E6%B2%B3%E5%8C%BA%E9%87%91%E7%A9%97%E5%B9%BC%E5%84%BF%E5%9B%AD&dlat=23.123746&dlon=113.334724&type=1&policy=0&dateTime=2026-11-12%7C07-20) |
| Zhonghai Jinghui Huating | K6 Jinsui · Huacheng | 2,138 / 28.5 | Metro L5 · 猎德 (C口) → 潭村 (B口) | 23 / 07:43 | ¥2 | 0 | 猎德大道—花城大道，平江路 | [Walk](https://uri.amap.com/navigation?from=113.332723,23.121608&to=113.347319,23.116220&mode=walk&src=liede-fieldwork) · [Transit](https://ditu.amap.com/ssr/dir?fname=%E4%B8%AD%E6%B5%B7%E7%92%9F%E6%99%96%E5%8D%8E%E5%BA%AD&flat=23.121608&flon=113.332723&dname=%E5%B9%BF%E5%B7%9E%E5%B8%82%E5%A4%A9%E6%B2%B3%E5%8C%BA%E9%87%91%E7%A9%97%E5%B9%BC%E5%84%BF%E5%9B%AD%E8%8A%B1%E5%9F%8E%E5%9B%AD%E5%8C%BA&dlat=23.11622&dlon=113.347319&type=1&policy=0&dateTime=2026-11-12%7C07-20) |
| Nanguo Garden | K1 Liede | 916 / 12.2 | 138路 · 马场路南 → 临江大道 | 22 / 07:42 | ¥2 | 0 | 海月路 | [Walk](https://uri.amap.com/navigation?from=113.344585,23.114459&to=113.337456,23.114648&mode=walk&src=liede-fieldwork) · [Transit](https://ditu.amap.com/ssr/dir?fname=%E5%8D%97%E5%9B%BD%E8%8A%B1%E5%9B%AD&flat=23.114459&flon=113.344585&dname=%E5%B9%BF%E5%B7%9E%E5%B8%82%E5%A4%A9%E6%B2%B3%E5%8C%BA%E7%8F%A0%E6%B1%9F%E6%96%B0%E5%9F%8E%E7%8C%8E%E5%BE%B7%E5%B9%BC%E5%84%BF%E5%9B%AD&dlat=23.114648&dlon=113.337456&type=1&policy=0&dateTime=2026-11-12%7C07-20) |
| Nanguo Garden | K2 Wanjin | 2,204 / 29.4 | Metro L5 · 潭村 (A口) → 猎德 (D口) | 30 / 07:50 | ¥2 | 0 | 花城大道—猎德大道，金穗路辅路 | [Walk](https://uri.amap.com/navigation?from=113.344585,23.114459&to=113.332259,23.121804&mode=walk&src=liede-fieldwork) · [Transit](https://ditu.amap.com/ssr/dir?fname=%E5%8D%97%E5%9B%BD%E8%8A%B1%E5%9B%AD&flat=23.114459&flon=113.344585&dname=%E5%B9%BF%E5%B7%9E%E5%B8%82%E5%A4%A9%E6%B2%B3%E5%8C%BA%E4%B8%87%E9%94%A6%E5%B9%BC%E5%84%BF%E5%9B%AD&dlat=23.121804&dlon=113.332259&type=1&policy=0&dateTime=2026-11-12%7C07-20) |
| Nanguo Garden | K3 Zuozhiya | 2,385 / 31.8 | Metro L5 · 潭村 (A口) → 猎德 (D口) | 31 / 07:51 | ¥2 | 0 | 花城大道—猎德大道辅路，兴盛路—兴盛直街 | [Walk](https://uri.amap.com/navigation?from=113.344585,23.114459&to=113.329152,23.122236&mode=walk&src=liede-fieldwork) · [Transit](https://ditu.amap.com/ssr/dir?fname=%E5%8D%97%E5%9B%BD%E8%8A%B1%E5%9B%AD&flat=23.114459&flon=113.344585&dname=%E5%B9%BF%E5%B7%9E%E5%B8%82%E5%A4%A9%E6%B2%B3%E5%8C%BA%E4%BD%90%E6%B2%BB%E4%BA%9A%E5%B9%BC%E5%84%BF%E5%9B%AD&dlat=23.122236&dlon=113.329152&type=1&policy=0&dateTime=2026-11-12%7C07-20) |
| Nanguo Garden | K4 Lixun Shangzhu | 485 / 6.5 | 未返回方案 | — | — | — | 平月路，另有未命名段 | [Walk](https://uri.amap.com/navigation?from=113.344585,23.114459&to=113.341996,23.115182&mode=walk&src=liede-fieldwork) · [Transit](https://ditu.amap.com/ssr/dir?fname=%E5%8D%97%E5%9B%BD%E8%8A%B1%E5%9B%AD&flat=23.114459&flon=113.344585&dname=%E5%B9%BF%E5%B7%9E%E5%B8%82%E5%A4%A9%E6%B2%B3%E5%8C%BA%E5%8A%9B%E8%BF%85%E4%B8%8A%E7%AD%91%E5%B9%BC%E5%84%BF%E5%9B%AD&dlat=23.115182&dlon=113.341996&type=1&policy=0&dateTime=2026-11-12%7C07-20) |
| Nanguo Garden | K5 Jinsui | 1,997 / 26.6 | 40路 · 马场路南 → 珠江公园南门 | 30 / 07:50 | ¥2 | 0 | 平月路—马场路，金穗路—海乐路 | [Walk](https://uri.amap.com/navigation?from=113.344585,23.114459&to=113.334724,23.123746&mode=walk&src=liede-fieldwork) · [Transit](https://ditu.amap.com/ssr/dir?fname=%E5%8D%97%E5%9B%BD%E8%8A%B1%E5%9B%AD&flat=23.114459&flon=113.344585&dname=%E5%B9%BF%E5%B7%9E%E5%B8%82%E5%A4%A9%E6%B2%B3%E5%8C%BA%E9%87%91%E7%A9%97%E5%B9%BC%E5%84%BF%E5%9B%AD&dlat=23.123746&dlon=113.334724&type=1&policy=0&dateTime=2026-11-12%7C07-20) |
| Nanguo Garden | K6 Jinsui · Huacheng | 642 / 8.6 | 未返回方案 | — | — | — | 平月路—平苑街，平江路 | [Walk](https://uri.amap.com/navigation?from=113.344585,23.114459&to=113.347319,23.116220&mode=walk&src=liede-fieldwork) · [Transit](https://ditu.amap.com/ssr/dir?fname=%E5%8D%97%E5%9B%BD%E8%8A%B1%E5%9B%AD&flat=23.114459&flon=113.344585&dname=%E5%B9%BF%E5%B7%9E%E5%B8%82%E5%A4%A9%E6%B2%B3%E5%8C%BA%E9%87%91%E7%A9%97%E5%B9%BC%E5%84%BF%E5%9B%AD%E8%8A%B1%E5%9F%8E%E5%9B%AD%E5%8C%BA&dlat=23.11622&dlon=113.347319&type=1&policy=0&dateTime=2026-11-12%7C07-20) |

「未返回方案」表示网页返回空方案，「未获取」表示本轮未取得可读结果。点开链接可复查同一对坐标及出发时间，动态规划可能发生变化。原有及新增的未限定时段公交方案、网页备选方案和逐段记录均见 JSON。

例如，猎德花园至兴国小学的第一轮公交估算为约 25.6 分钟，第二轮早间网页方案为 23 分钟。这两组结果来自不同查询设置，均保留在对应记录中，适合核对方案和估算差异。

### 最近幼儿园和最近公办园区

最近按步行路网距离排序，仅在六个园区内比较。公办采用天河区教育局 2026 年「教育部门办幼儿园」名单，含猎德幼儿园、金穗幼儿园及其花城园区。万锦、佐治亚、力迅上筑为 2026 年名录列出的普惠性民办园。[教育部门办园名单](https://www.thnet.gov.cn/gzjg/qzf/qjyj/zsks/content/post_10815546.html) · [民办园名单](https://www.thnet.gov.cn/gzjg/qzf/qjyj/zsks/content/post_10815624.html)

| 住宅样本 | 最近样本园区 | 米 / 分钟 | 最近公办样本园区 | 米 / 分钟 |
|---|---|---:|---|---:|
| 猎德花园 | 珠江新城猎德幼儿园 | 273 / 3.6 | 珠江新城猎德幼儿园 | 273 / 3.6 |
| 中海璟晖华庭 | 万锦幼儿园 | 269 / 3.6 | 金穗幼儿园 | 640 / 8.5 |
| 南国花园 | 力迅上筑幼儿园 | 485 / 6.5 | 金穗幼儿园花城园区 | 642 / 8.6 |

### 10、15、20 分钟内的园区与费用证据

广州市政府定价规定全日制公办规范园保教费 **823 元／生／月**，示范园 **995 元／生／月**。本轮未取得六处样本的当年园区收费公示或可用于确认具体标准的完整等级资料，无法核实每园小中班实收费、伙食费和总费用。普惠性民办园按协议和指导标准收费，具体实收仍需公示。另可按市教育局政策确认公办园在读且符合学前一年减免条件的幼儿保教费为 **0 元**，伙食及其他费用另计。民办园参照同类公办园减免，超过减免标准的部分可能仍需缴纳。[广州幼儿园收费通知](https://fgw.gz.gov.cn/gkmlpt/content/9/9577/post_9577385.html) · [广州市学前一年保教费减免说明](https://jyj.gz.gov.cn/gk/zfxxgkml/bmwj/qtwj/content/post_10516322.html)

| 住宅样本 | 全部样本园区（≤10 / 15 / 20 分钟） | 公办园区（同左阈值） | 小中班当年园区级收费金额已核实 | 符合学前一年政策时保教费为 0 的公办园区 |
|---|---:|---:|---:|---:|
| 猎德花园 | 1 / 2 / 4 | 1 / 1 / 3 | 0 / 0 / 0 | 1 / 1 / 3 |
| 中海璟晖华庭 | 3 / 3 / 4 | 1 / 1 / 2 | 0 / 0 / 0 | 1 / 1 / 2 |
| 南国花园 | 2 / 3 / 3 | 1 / 2 / 2 | 0 / 0 / 0 | 1 / 2 / 2 |

小中班栏的 0 表示未核实到收费金额。条件性免保教费栏统计已经入园并适用政策时的园区数，无法据此判断全部家庭可负担或可获得的学位。

### Table 2 · Walking access to sampled primary schools

单元格为单程步行 **米 / 分钟**，粗体为 2026 年招生地段支持的住宅—小学地址对应。每个粗体单元格也是该行最短的样本路线。[天河区 2026 年招生工作细则，附件 5](https://www.thnet.gov.cn/attachment/8/8016/8016210/10791180.pdf)

| Residence | S1 Liede Experimental | S2 Haiming Primary | S3 Xingguo Primary | S4 Nanguo School |
|---|---:|---:|---:|---:|
| Liede Garden | **443 / 5.9** [↗](https://uri.amap.com/navigation?from=113.336127,23.113409&to=113.337457,23.115805&mode=walk&src=liede-fieldwork) | 950 / 12.7 [↗](https://uri.amap.com/navigation?from=113.336127,23.113409&to=113.342561,23.115197&mode=walk&src=liede-fieldwork) | 1,330 / 17.7 [↗](https://uri.amap.com/navigation?from=113.336127,23.113409&to=113.331236,23.119408&mode=walk&src=liede-fieldwork) | 1,406 / 18.8 [↗](https://uri.amap.com/navigation?from=113.336127,23.113409&to=113.344261,23.116251&mode=walk&src=liede-fieldwork) |
| Zhonghai Jinghui Huating | 1,354 / 18.1 [↗](https://uri.amap.com/navigation?from=113.332723,23.121608&to=113.337457,23.115805&mode=walk&src=liede-fieldwork) | 1,722 / 23.0 [↗](https://uri.amap.com/navigation?from=113.332723,23.121608&to=113.342561,23.115197&mode=walk&src=liede-fieldwork) | **756 / 10.1** [↗](https://uri.amap.com/navigation?from=113.332723,23.121608&to=113.331236,23.119408&mode=walk&src=liede-fieldwork) | 1,986 / 26.5 [↗](https://uri.amap.com/navigation?from=113.332723,23.121608&to=113.344261,23.116251&mode=walk&src=liede-fieldwork) |
| Nanguo Garden | 1,060 / 14.1 [↗](https://uri.amap.com/navigation?from=113.344585,23.114459&to=113.337457,23.115805&mode=walk&src=liede-fieldwork) | 487 / 6.5 [↗](https://uri.amap.com/navigation?from=113.344585,23.114459&to=113.342561,23.115197&mode=walk&src=liede-fieldwork) | 2,017 / 26.9 [↗](https://uri.amap.com/navigation?from=113.344585,23.114459&to=113.331236,23.119408&mode=walk&src=liede-fieldwork) | **207 / 2.8** [↗](https://uri.amap.com/navigation?from=113.344585,23.114459&to=113.344261,23.116251&mode=walk&src=liede-fieldwork) |

| 住宅样本 | 地址层面对应小学 | 招生地段依据 | 早间公交复查 |
|---|---|---|---|
| 猎德花园 | 猎德实验学校小学部 | 第 56 行列出原猎德村范围及猎德小区，需以具体门牌核对。 | 未返回方案。[高德](https://ditu.amap.com/ssr/dir?fname=%E7%8C%8E%E5%BE%B7%E8%8A%B1%E5%9B%AD&flat=23.113409&flon=113.336127&dname=%E5%B9%BF%E5%B7%9E%E5%B8%82%E5%A4%A9%E6%B2%B3%E4%B8%AD%E5%AD%A6%E7%8C%8E%E5%BE%B7%E5%AE%9E%E9%AA%8C%E5%AD%A6%E6%A0%A1%E5%B0%8F%E5%AD%A6%E9%83%A8&dlat=23.115805&dlon=113.337457&type=1&policy=0&dateTime=2026-11-12%7C07-20) |
| 中海璟晖华庭 | 兴国小学 | 第 18 行点名中海璟晖华庭。 | 未返回方案。[高德](https://ditu.amap.com/ssr/dir?fname=%E4%B8%AD%E6%B5%B7%E7%92%9F%E6%99%96%E5%8D%8E%E5%BA%AD&flat=23.121608&flon=113.332723&dname=%E5%B9%BF%E5%B7%9E%E5%B8%82%E5%A4%A9%E6%B2%B3%E5%8C%BA%E4%BD%93%E8%82%B2%E4%B8%9C%E8%B7%AF%E5%B0%8F%E5%AD%A6%E5%85%B4%E5%9B%BD%E5%AD%A6%E6%A0%A1&dlat=23.119408&dlon=113.331236&type=1&policy=0&dateTime=2026-11-12%7C07-20) |
| 南国花园 | 南国学校小学部 | 第 55 行列出指定边界内的南国花园。 | 未返回方案。[高德](https://ditu.amap.com/ssr/dir?fname=%E5%8D%97%E5%9B%BD%E8%8A%B1%E5%9B%AD&flat=23.114459&flon=113.344585&dname=%E5%B9%BF%E5%B7%9E%E5%B8%82%E5%8D%97%E5%9B%BD%E5%AD%A6%E6%A0%A1%E5%B0%8F%E5%AD%A6%E9%83%A8&dlat=23.116251&dlon=113.344261&type=1&policy=0&dateTime=2026-11-12%7C07-20) |

地段表确定地址层面的报名对应，最终资格由申请类别、户籍或政策性条件、住房材料和实际审核决定。三条对口路线的步行里程与时间均复查一致。其余 9 条小学路线的早间公交结果及未限定时段备选方案见 JSON。

## 路线与资料可靠性核查

**地址与点位。** 13 个高德 POI 编号复查所得坐标均与第一轮一致，这说明位置记录可复现。4 所小学的办学阶段和 6 处幼儿园的园区地址按区教育局文件核对。猎德实验学校是九年一贯制，使用高德全校点，分类标签显示中学。南国学校按高德小学部点位取平月路 200 号，教育局学校总表登记的是全校平月路 202 号。地图检索有小学部南门旁商户线索，未据此认定早上实际使用的门。金穗幼儿园本园与花城园区为同一园名下两个地址，按两个可到达园区计数。[小学名录](https://www.thnet.gov.cn/zwgk/ggqsydwxxgkzl/jyly/xx/content/post_8724023.html) · [九年一贯制学校名录](https://www.thnet.gov.cn/zwgk/ggqsydwxxgkzl/jyly/jnygzxx/content/post_8724037.html) · [南国学校小学部高德点](https://ditu.amap.com/place/B00141IKVW) · [小学部南门旁商户线索](https://ditu.amap.com/place/B0FFK71MCV) · [公办园名录与园区地址](https://www.thnet.gov.cn/gzjg/qzf/qjyj/zsks/content/post_10815546.html) · [民办园名录](https://www.thnet.gov.cn/gzjg/qzf/qjyj/zsks/content/post_10815624.html)

**出入口。** 猎德花园使用海文路 7 号住宅点，路径接入海文路附近支路。中海璟晖华庭使用猎德大道 31 号住宅点，搜索中也有停车出入口，不能用作已核实人行门。南国花园使用平月路住宅点，北门旁商户提供可核查线索。小学和幼儿园均以园校点位为终点。校址与图钉相符仍需现场确认开放出入口。[猎德花园地址与回迁性质](https://renda.thnet.gov.cn/renda/liede/202009/22499b2d8da646d4b1900f789a84b0db.shtml) · [中海住宅开发规划](https://ghzyj.gz.gov.cn/ywpd/cxgh/ghxkgsgb/phgbnew/ghyshgzls/content/post_7699927.html) · [南国花园北门旁商户线索](https://ditu.amap.com/place/B0FFFFKK9O)

**绕行及通行条件。** 30 条路线的步行分段距离加总与高德路线总长相符（允许米级舍入）。进一步筛查路网长度明显高于图钉间距离的路线，结果用于选取核查对象，所有可达性指标仍使用路网距离。三条地段对应小学路线复算一致。中海 → 万锦正反向均为 269 米，应检查小区内部是否有可合法通行的人行捷径。猎德花园 → 金穗本园正反向均为 1,467 米，去花城园区正向 1,500 米、反向 1,499 米。经过花城大道与猎德大道、海风路或平江路的路线可用于核查过街条件。金穗花城园区的正向路线恰好 **20 分钟**，入口或等待时间变动即可改变其阈值归类。[中海至万锦步行规划](https://uri.amap.com/navigation?from=113.332723,23.121608&to=113.332259,23.121804&mode=walk&src=liede-fieldwork)

**公交时效和站名。** 市交通运输局 2026 年 10 月 30 日公告列明，**花城大道上的东行**公交猎德站列入改名计划，新名为花城大道（兴国路口）站，11 月 7 日起分批实施。第一轮将部分高德返回的「猎德」直接关联到该东行站，第二轮保留地图原名并限定官方改名范围。高德记录缺少可用于逐条对照的站台编号，环线方向应以实际站牌为准。另查到官方 777 路环线调整记录，涉及潭村方向的路段和站点。2026 年 11 月的网页规划结果可用于当前线路核对，到站时刻和班次可靠性仍需观测。部分地铁方案使用潭村 A 或 B 口，广州地铁无障碍指引将潭村 D 口列为地面至站厅的无障碍出入口，选用该入口可能改变步行部分。[广州地铁无障碍乘车指引](https://www.gz.gov.cn/attachment/7/7792/7792275/10648239.pdf)[2026 年公交更名公告，第 44 行](https://jtj.gz.gov.cn/zwgg/ywgg/ggjt/gjxldzgg/content/post_11079212.html) · [777 路调整公告](https://jtj.gz.gov.cn/zwgg/ywgg/ggjt/gjxldzgg/content/post_10396011.html) · [线路调整公告目录](https://jtj.gz.gov.cn/zwgg/ywgg/ggjt/gjxldzgg/)

## 社会学解释

**Q1 · 小学和幼儿园的差异有多大？** 就各住宅样本到地段对应小学而言，最大与最小相差 549 米、约 7.3 分钟，三个地点都有相对短的步行路线。固定比较同一所小学，差异会放大。例如，到南国学校小学部的样本路线从 207 米到 1,986 米。最近公办幼儿园的差距约 5 分钟，到同一远端幼儿园的差距则可能超过 20 分钟。海报宜同时报告最近选项和同一目的地的差异。

**Q2 · 回迁和商品住宅是否表现一致？** 排序随园校位置变化。猎德花园在西南侧的猎德园校附近，中海在西北侧的万锦和兴国小学附近，南国花园靠近东侧的南国学校和力迅上筑。这体现了样本的**空间不平等（spatial inequality）**，即设施分布与住宅位置使同一目的地具有不同出行成本。样本只有一个回迁住宅点和两个商品住宅点，不能把排序推广到两类住房居民。

**Q3 · 最近与有资格申请的学校之间有什么差异？** 三个样本的最近小学与地址对应小学在本研究中重合。南国花园至海明小学也只有 6.5 分钟，但南国花园列在南国学校的地段，不能把两所学校都计为该地址的地段对口选择。幼儿园按办园类型比较时，中海从最近任一园到最近公办园多约 **5.0 分钟**，南国花园多约 **2.1 分钟**。这是选项范围变化后的路网差异。资格和录取仍取决于当年招生办法、家庭条件与学位。区教育局 2026 年小班计划列明，猎德幼儿园公开派位计划 135 个，其中业主子女类别 85 个，剩余随机派位 50 个。**教育可达性（educational accessibility）**还涉及家庭能否申请、负担及持续使用这个学位。[义务教育招生工作细则](https://www.thnet.gov.cn/gzjg/qzf/qjyj/zsks/content/post_10791180.html) · [幼儿园招生方案](https://www.thnet.gov.cn/gzjg/qzf/qjyj/zsks/content/post_10777181.html) · [幼儿园派位计划](https://www.thnet.gov.cn/gzjg/qzf/qjyj/zsks/content/post_10815546.html)

**Q4 · 哪些因素增加接送负担？** **交通负担（transportation burden）**包括步行与等车时间、过街、票价、换乘及接送时段的可预测性。07:20 早间模型下，中海到海明小学乘 138 路的步行部分为 253 米，总程 24 分钟，纯步行 1,722 米、约 23 分钟。中海到金穗花城园区则可乘地铁，模型总程 23 分钟，比纯步行约少 5.5 分钟，但仍需步行约 1 公里。对需要陪幼儿步行的家庭，少走路和省时间是不同收益。单次相差数分钟也可能累积，但每个家庭的往返次数、换人接送、返家或继续上班的路线均未测量。地铁 5 号线猎德—潭村按短程成人单程标准为 ¥2。公交表列平台显示的费用，家庭实际支出还受乘员、优惠与实乘线路影响。[广州地铁票务规则](https://www.gz.gov.cn/attachment/7/7792/7792262/10198954.pdf) · [广州市公交基础票价政策](https://fgw.gz.gov.cn/gkmlpt/content/9/9824/post_9824407.html)

**Q5 · 能否据此判断存在社会不平等？** 数据支持三个样本点到指定园校存在地理可达性差异，也支持三个样本都能较快走到至少一处公办园和各自地址对应小学。要判断这种差异是否系统性集中于资源较少或申请渠道受限的家庭，需要把实际接送负担与住房、家庭预算、招生资格及使用的学位联系起来。最小补证是同一上学时段重复走访不同楼栋和校门，并记录不同租住或自住、不同申请路径家庭的匿名接送和费用信息。[Geurs 与 van Wee 对可达性的空间、时段及个人约束框架](https://research.utwente.nl/en/publications/accessibility-evaluation-of-land-use-and-transport-strategies-rev/)

## 局限与现场补证

1. **取样范围。** 三个住宅各用一个起点，六处幼儿园是上一轮选定园区，十处教育点不是全量名录。阈值数量是样本计数，不能外推至整个猎德。可用不同楼栋和至少两个常用人行门检查结论是否随起点变动。
2. **门与过街。** 高德估计无法反映儿童步速、路口信号、楼栋到小区门时间及临时封闭。建议在平日 07:30–08:00 实走三条对口小学路线，以及中海至万锦、猎德花园至金穗花城园区的关键路线，记录出入口、过街点、信号等候与实际到达时间。
3. **公交模型。** 网页规划使用指定的出发时间，以展示的分钟数推算到达时间。没有实测候车、拥挤、运行波动或无障碍绕行。公交费用按显示值记录，现场可用站牌、票价牌或运营方公告核验。
4. **资格与费用。** 地址对应与派位计划是制度信息。园区小中班实际保教费、伙食费、申请资格、申请成功与否及家庭实际接送安排仍需当年收费公示、匿名家长访谈或小组现场记录。访谈应区分自住与租住、不同申请渠道，并避免收集可识别儿童的信息。

## Poster Summary

We assessed transport access from three residential developments in Liede and nearby Zhujiang New Town to four public primary schools and six kindergarten campuses. Amap pedestrian routes put the nearest sampled kindergarten at 3.6–6.5 minutes on foot and the nearest public kindergarten at 3.6–8.6 minutes. Estimated walks to the public primary schools listed for the sampled addresses in Tianhe’s 2026 catchment plan took 2.8–10.1 minutes. Each was also the closest of the four sampled primary schools to its corresponding origin. Relative proximity varied by destination across resettlement and market housing. Admissions and fee rules can change which nearby places a family can use, while escort time and travel costs can affect whether that option is sustainable. Gate observations, current fee notices and household travel records are needed to assess how these burdens are distributed.


## 地图来源

底图为 OpenStreetMap 道路、水系与绿地。高德地点标记经近似坐标转换后叠加在同一底图上。距离比例尺只用于读图。[OpenStreetMap © contributors · ODbL](https://www.openstreetmap.org/copyright) · [坐标转换方法参考](https://github.com/wandergis/coordTransform_py)
