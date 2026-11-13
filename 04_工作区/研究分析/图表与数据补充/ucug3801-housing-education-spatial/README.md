# UCUG3801 · Housing prices × educational facilities

独立研究包，来源提交 `5101aa7ca61e0d2ddeff85a8209d9cf126a33508`，核查基准 2026-11-13。

## 成果

- [Spatial Findings Report 与双语图注](spatial-findings-report.md)
- 完整版 [PNG](maps/housing-education-full.png) · [PDF](maps/housing-education-full.pdf) · [SVG](maps/housing-education-full.svg)
- 16:9 Poster 版 [PNG](maps/housing-education-poster.png) · [PDF](maps/housing-education-poster.pdf) · [SVG](maps/housing-education-poster.svg)
- 源表使用 UTF-8 BOM，方便 Excel 打开。空字段表示缺失或不适用。

## 数据导入

| 文件 | 主键或连接键 | 用法 |
| --- | --- | --- |
| [housing_projects.csv](data/housing_projects.csv) | `residence_id` | 原 `RES001–RES018` 保留，`RES019–RES022` 为新增建议 ID。项目 POI 独立保存为 `HES-AMAP-*`。以 `map_price_cny_m2` 作图，价格出处和月份同列。 |
| [housing_price_observations.csv](data/housing_price_observations.csv) | `id` → `residence_id` | 保留原参考价、挂牌、平台标示成交、租金及人才租金。新增观察带 `HES-PRICE-*`。珠江都荟原观测保留 ID，增加旧分类与勘误状态，便于在导入审查时修正指标。原仓库源表不受此包影响。 |
| [price_rechecks.csv](data/price_rechecks.csv) | `residence_id` | 每项目的原值、复核值、参考月份和出版方页面。原调查日期为 2026-11-11，新查为 11-13。 |
| [campuses.csv](data/campuses.csv) | `campus_id` | 保留全部原 `CAP-*` 与机构 ID。新位置可追加到 `positions`，用途是项目地图或园校参照。原交通起终点、疑点路线、实际门点和家户资格不能被自动替换。地图的 `Gxx` 编号独立于交通研究的旧 `Kx`。 |
| [prior_coordinate_crosswalk.csv](data/prior_coordinate_crosswalk.csv) | `entity_id` | 对照五个旧住宅参照点，以及凯旋新世界单期 POI。 |
| [map_layers.csv](data/map_layers.csv) / [map_scope.json](data/map_scope.json) | `map` × `entity_id` | 两幅图最终选点、分类、配色阈值、范围和分析投影。 |
| [campus_proximity.csv](data/campus_proximity.csv) / [proximity_pairs_within_800m.csv](data/proximity_pairs_within_800m.csv) / [price_proximity_summary.csv](data/price_proximity_summary.csv) | 住宅 × 半径或园校 | 设施直线距离、各类计数与分组敏感性。 |
| [amap_poi_checks.json](data/amap_poi_checks.json) | 住宅或园校 ID | 高德返回的名称、别名、地址、GCJ-02 坐标和 POI ID。与相应名录行、价格网页比对后才采用。 |
| [osm_basemap_2026-11-12.json.gz](data/osm_basemap_2026-11-12.json.gz) | OSM 要素 | GitHub 存档的道路、水体和公园底图。© OpenStreetMap contributors，ODbL。 |

## 可复算

用 Python 3.11+、`matplotlib`、`pyproj` 和可用的中文字体运行。把 GitHub 对应提交的检出目录作为第一个参数。准备程序沿用该分支已有 GCJ-02 迭代逆算。文件中 `raw_crs` 保留原坐标，`map_crs` 为 EPSG:4326，局部距离在 EPSG:32649 计算。转码精度不等于 POI 实地精度。

```text
python prepare_spatial_data.py <checkout-at-5101aa7> . --amap-input data/amap_poi_checks.json
python render_spatial_maps.py . --osm data/osm_basemap_2026-11-12.json.gz --font <Chinese-capable-font-path>
```

[原研究价格表](https://github.com/alphakeeer/UCUG3801_Poster/blob/5101aa7ca61e0d2ddeff85a8209d9cf126a33508/04_%E5%B7%A5%E4%BD%9C%E5%8C%BA/%E7%A0%94%E7%A9%B6%E5%88%86%E6%9E%90/%E6%88%BF%E4%BB%B7%E5%88%86%E5%B8%83/%E7%8C%8E%E5%BE%B7%E4%BD%8F%E6%88%BF%E4%BB%B7%E6%A0%BC%E6%95%B0%E6%8D%AE_2026-11-11.csv) · [原住宅点位](https://github.com/alphakeeer/UCUG3801_Poster/blob/5101aa7ca61e0d2ddeff85a8209d9cf126a33508/06_%E6%95%B0%E6%8D%AE%E6%95%B4%E5%90%88/outputs/data/positions.csv) · [原始底图](https://github.com/alphakeeer/UCUG3801_Poster/blob/5101aa7ca61e0d2ddeff85a8209d9cf126a33508/03_%E8%83%8C%E6%99%AF/%E6%95%99%E8%82%B2%E4%B8%93%E9%A2%98/%E5%9C%B0%E5%9B%BE/OSM_%E7%8C%8E%E5%BE%B7%E5%91%A8%E8%BE%B9_20261112.json) · [OpenStreetMap ODbL](https://www.openstreetmap.org/copyright)

