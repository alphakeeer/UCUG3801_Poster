# 教育主题海报 v3：四款设计方案

《住得近，就能读得上吗？》的海报方案 A–D。四款方案共用一份文字与数据，只在版式、视觉语言和叙事顺序上不同。画布为 9:16、1080×1920，导出的预览图为 2160×3840。

打开 [方案对比.html](方案对比.html) 可以并排比较四款方案，对比页里写了每款的优点和取舍。

## 目录

| 路径 | 内容 |
| --- | --- |
| `shared/content.js` | 海报的全部文字与数据。改这里，四款方案同步更新 |
| `shared/charts.js` | 发现一、发现二的 SVG 图表，地图图例和地图标记 |
| `shared/base.css` | 字体、画布尺寸、地图组件 |
| `designs/a-academic/` | 方案 A：学术清晰 |
| `designs/b-editorial/` | 方案 B：报刊特稿 |
| `designs/c-pathways/` | 方案 C：一址四门 |
| `designs/d-mapstory/` | 方案 D：地图叙事 |
| `designs/e-fieldreport/` | 第二轮方案 E：田野报告（房产证、户口本、拆迁协议） |
| `designs/f-compare/` | 第二轮方案 F：两个社区对照（回迁户、业主与租户） |
| `designs/e-fieldreport-en/` | 方案 E 英文版（共用 `e-fieldreport/poster.css`、`poster.js`） |
| `shared/content-en.js` | 方案 E 英文文案 |
| `final/` | 路演定稿：中英两版 PNG 与 PDF（入库） |
| `shared/content2.js`、`shared/a3.js` | 第二轮文案；定稿的 A3 地图与对照表 |
| `assets/` | 去掉英文图例后的地图裁切图（取自 `交接资料/图表/02`）和现场照片 |
| `previews/` | 导出的 PNG / PDF（不入库，运行 `node export.cjs --pdf` 重新生成） |
| `shared/map.js`、`shared/mapdata.js` | 矢量地图：按经纬度重绘的 OSM 底图、22 个住宅、43 个园校点位 |
| `tools/build_map_data.py` | 由交接空间数据包生成 `shared/mapdata.js` |
| `map-lab/` | 三种地图版式 M1–M3 的对比页 |

## 导出

```bash
node export.cjs            # 导出全部方案的 PNG
node export.cjs c --pdf    # 只导出方案 C，同时导出 PDF
```

地图方案用 `node export-maps.cjs` 导出到 `previews/map-*.png`；改了源数据后先运行 `python3 tools/build_map_data.py`。

导出脚本复用 `../海报v2/node_modules` 里的 Playwright，以及 `../海报v2/fonts-src` 里的完整字体（字体目录不入库）。脚本会检查内容是否超出画布，并逐段打印各区块高度。

## 数据口径

所有数字都取自仓库交接数据，基准提交为 `0c0e50e`：

- 价格分组：`price_proximity_summary.csv`
- 同址四情境：`same-address-admission-scenarios.csv`
- 步行路线：`transport_routes.csv`
- 理论框架：`../研究分析/理论支撑/12_Poster整合说明_理论支撑定稿.md` 第三部分

地图上三个起点的位置，是按原图中标记的像素位置核对过的。

## 待定事项

- 组员：马知为、陈泽彬、方晓宇、赵秋语、饶越洋（英文版按名在前、姓在后书写）。
- 研究问题去掉了「收费」，因为两项发现都没有分析收费。如果要保留，需要补一段收费证据。
- 幼儿园招生名额、收费证据暂未上版。
- 定稿后要做字体子集，并按最终文字复查一次。
