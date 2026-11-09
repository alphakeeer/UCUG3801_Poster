# 猎德研究海报 v2

《开门的时候，你在上班吗？》猎德街公共文化设施的时间可及性研究。9:16 竖版，1080×1920 画布，导出 3240×5760 PNG 与单页 PDF 到 `05_提交/poster_final/`。

## 目录

| 路径 | 内容 |
| --- | --- |
| `src/index.html` | 海报全部文字，按作业八部分组织 |
| `src/poster.css` | 版式与配色（纸色、墨黑、朱红强调） |
| `src/chart.js` | 图1 开放时段数据、假设空闲情景与三项统计，数字均由此计算 |
| `src/assets/` | 处理后的照片与字体子集 |
| `tools/prepare_photos.py` | 从 `02_现场/照片/` 裁切并调成暖黑白；雕塑图已裁去路人 |
| `tools/build_fonts.py` | 按页面用字生成字体子集 |
| `export.cjs` | Playwright 渲染导出，并检查内容是否超出画布 |

## 重新导出

```bash
npm install
npm run export
```

改了文字后先运行 `python3 tools/build_fonts.py`（需要 `fonttools`、`brotli`），否则新字会缺字形。完整字体放在 `fonts-src/`（不入库），来源见脚本注释。换照片后运行 `python3 tools/prepare_photos.py`（需要 Pillow）。

## 待替换的内容

- 组员姓名为占位，需换成真实姓名。
- 图2 的楼层由目录地址推断；入口、电梯、活动公告需现场审计后补入并更新图注。
- 空闲时段（工作日 19–22 时、周末 9–22 时）是假设情景，海报图注和局限中已说明。
