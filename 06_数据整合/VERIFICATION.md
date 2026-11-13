# v1 复现与图件核验记录

核验日期：2026-11-13。此记录仅对应下面的数据版本；后续补证、映射或绘图代码变化后，应重新执行检查并视觉核对。

数据版本：`a821cbd2717d338db09a87718909dccc1a4845a5e166fbdcff9418899b212fd9`。

## 自动及干净检出复现

- 33项标准库unittest回归测试通过，包括完整补证重建、未知实体、重复事实冲突、坐标冲突、来源ID冲突、非法单位/数值、初中排除、共享计划去重、缺失/零值和原件保护。
- 构建时367项输入、来源及关系检查通过；完整validate连同生成物哈希和版本检查共411项通过，失败数0。
- 使用仅含已提交模块代码的独立干净detached worktree，先建立该工作区保护基线，再运行同一all和validate入口。
- 与当前证据包比较，44个输出文件的SHA-256全部一致，包括25张CSV、JSON质量/版本/字段信息、Markdown交接文件、图件源数据及6份PNG/SVG/PDF。
- 四张既有交通派生CSV在临时目录复算后与旧版本逐字节一致；原交通脚本、旧图件、地图和Poster均未被执行写入。
- 同一锁定Python环境离线复现；未重新开展外部事实检索。

## 图件视觉与导出检查

- 两张PNG均从matplotlib原始画布导出并实际打开检查，未见标签重叠或截断，程序检查文本越出画布数量均为0。
- Figure A低值蓝色与缺失白色分开；不可比住宅为菱形，转换住宅POI用~标记，转换园校POI为空心，未确认地图候选为灰色叉号。
- Figure A写明5/18住宅、23/43园校的当前地图覆盖。没有把未定位记录补到相近对象，也未绘制房价插值面或认定官方招生边界。
- Figure B保留9条住宅/申请渠道比较；图中注明条件性申请、示例志愿、未观察实际分配和未核校门。住房标签随规范成本表生成，缺失及冲突不填值。
- SVG保留可编辑文本：A为47个text元素，B为35个text元素；PDF文本可提取，A约1155字符、B约980字符。
- 所有绘制与视觉预览均使用Python后端。输出PDF/SVG移除时间戳，SVG采用固定版本hash salt；未修改旧Poster或网页资产。

## 当前图件文件哈希

| 文件 | SHA-256 |
|---|---|
| `figure_A_housing_education.pdf` | `1ebbd469af18625acbd0455a91f492d6e2f877e58d16b2c19d9ca9b68dfbaa8c` |
| `figure_A_housing_education.png` | `d9f98bd4830bc92a15b1eaa570502f5c0c8c81c15efdbfb69963ef1f3e1a2fec` |
| `figure_A_housing_education.svg` | `505d9b1fb95a9d3a1abce5ef029fca6722d5542ae224b74c8442ae0cfd836ed2` |
| `figure_B_admission_accessibility.pdf` | `357ec2fc457a400e8a29cd538cc0409e6f7d19311671a34a6e1393b41711dd2d` |
| `figure_B_admission_accessibility.png` | `e08f3bf4e8c2cfb431c2eda291379fff531935b546f39d8d497246b7a4634f13` |
| `figure_B_admission_accessibility.svg` | `880e1d469ae79b2448984f4f46646196e442e7229ace8f4a9a831449fb9de69c` |

## 已知限制

这份检查不证明数据完整、校门准确、费用已实缴或因果效应成立。K7身份仍未确认，43条园校为候选集合，住房价格有不同指标和月份，家庭录取、预算及真实接送结果未观察。具体限制见[研究交接](outputs/HANDOFF.md)、[数据字典](DATA_DICTIONARY.md)及[缺口表](outputs/data/research_gaps.csv)。
