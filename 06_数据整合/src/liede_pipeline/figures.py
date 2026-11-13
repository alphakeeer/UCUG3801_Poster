"""Python-only figures built from the integrated tables, never old poster assets."""

import json
import os
from pathlib import Path

from .common import EDUCATION, write_csv, write_json


def render_figures(ctx,destination,version):
    os.environ.setdefault("MPLCONFIGDIR",str(ctx.module/".state/matplotlib"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.collections import LineCollection
    from pyproj import Transformer

    from matplotlib import font_manager
    from .common import digest
    spec = json.loads((ctx.module/"config/figure_font.json").read_text())
    font_dir = Path(os.environ.get("LIEDE_FONTS_DIR","/usr/share/fonts/truetype/wqy"))
    for filename,expected in spec["files"].items():
        path = font_dir/filename
        if not path.is_file() or digest(path)!=expected:
            raise RuntimeError("中文字体缺失或版本不同，请按config/figure_font.json安装并校验："+filename)
        font_manager.fontManager.addfont(str(path))
    plt.rcParams.update({"font.family":spec["family"],"font.size":10,"font.weight":500,
        "axes.titleweight":500,"axes.labelweight":500,"axes.unicode_minus":False,
        "axes.spines.top":False,"axes.spines.right":False,
        "svg.fonttype":"none","pdf.fonttype":42,"svg.hashsalt":version})
    output = destination/"figures"
    data_output = destination/"figure_source_data"
    output.mkdir(exist_ok=True)
    data_output.mkdir(exist_ok=True)
    transformer = Transformer.from_crs("EPSG:4326","EPSG:32649",always_xy=True)
    ox,oy = transformer.transform(113.332,23.121)
    def xy(lon,lat):
        x,y = transformer.transform(lon,lat)
        return x-ox,y-oy
    positions = {r["id"]:r for r in ctx.table("positions")}
    homes = []
    for row in ctx.table("residence_cost_summary"):
        p = positions.get(row["preferred_position_id"],{})
        homes.append(dict(row,longitude=p.get("longitude"),latitude=p.get("latitude"),
            position_role=p.get("position_role","missing"),
            coordinate_status=p.get("verification_status","missing"),
            position_source_id=p.get("source_id","")))
    campuses = []
    for row in ctx.table("education_campuses"):
        p = positions.get(row["preferred_position_id"],{})
        campuses.append(dict(row,longitude=p.get("longitude"),latitude=p.get("latitude"),
            coordinate_status=p.get("verification_status","missing"),position_source_id=p.get("source_id","")))
    unresolved = [p for p in positions.values() if p["candidate_entity_id"] and not p["entity_id"]]
    for name,rows in [("figure_A_housing",homes),("figure_A_campuses",campuses),("figure_A_unresolved",unresolved),
                      ("figure_B_comparisons",[r for r in ctx.table("accessibility_comparisons") if r["channel"]!="hk_macao_listed_channel"]),
                      ("figure_B_secondary_channels",[r for r in ctx.table("accessibility_comparisons") if r["channel"]=="hk_macao_listed_channel"]),
                      ("figure_B_housing_context",[r for r in homes if r["id"] in {"RES001","RES015","RES018"}])]:
        write_csv(data_output/(name+".csv"),rows,list(dict.fromkeys(k for r in rows for k in r)))
    qa = []
    def save(fig,name):
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        outside = []
        cmap_chars = matplotlib.ft2font.FT2Font(str(font_dir/"wqy-zenhei.ttc")).get_charmap()
        missing_glyphs = sorted({c for artist in fig.findobj(matplotlib.text.Text) for c in artist.get_text()
            if not c.isspace() and ord(c)>127 and ord(c) not in cmap_chars})
        if missing_glyphs:
            raise ValueError("图件中文字体缺字："+"".join(missing_glyphs))
        unused_ticks = set()
        for axis in fig.axes:
            for coordinate,limits in [(axis.xaxis,axis.get_xlim()),(axis.yaxis,axis.get_ylim())]:
                low,high = sorted(limits)
                for tick in coordinate.get_major_ticks():
                    if not low <= tick.get_loc() <= high:
                        unused_ticks.update([tick.label1,tick.label2])
        for artist in fig.findobj(matplotlib.text.Text):
            if artist in unused_ticks or not artist.get_visible() or not artist.get_text().strip():
                continue
            # Axis ticks outside view limits are not drawn by matplotlib.
            if artist.axes and artist not in artist.axes.texts and artist not in [artist.axes.title,artist.axes.xaxis.label,artist.axes.yaxis.label]:
                continue
            b = artist.get_window_extent(renderer)
            if b.x0 < -1 or b.y0 < -1 or b.x1 > fig.bbox.width+1 or b.y1 > fig.bbox.height+1:
                outside.append(artist.get_text())
        if outside:
            raise ValueError(f"图件{name}的文字超出画布：{outside}")
        fig.savefig(output/(name+".png"),dpi=300,metadata={"Software":"UCUG3801 integration pipeline"})
        fig.savefig(output/(name+".svg"),metadata={"Date":None,"Creator":"UCUG3801 integration pipeline"})
        fig.savefig(output/(name+".pdf"),metadata={"CreationDate":None,"ModDate":None,"Creator":"UCUG3801 integration pipeline"})
        qa.append(dict(figure=name,backend="matplotlib",text_outside_canvas=outside,
            missing_glyphs=missing_glyphs,font_family=spec["family"],font_sha256=spec["files"],
            source_data="figure_source_data/",formats=["png","svg","pdf"],
            causal_or_population_inference=False,statistical_tests="不适用；目的性案例样本"))
        plt.close(fig)

    # Figure A: one map, with separate metric/missingness summaries.
    fig = plt.figure(figsize=(12,8.3),facecolor="white")
    fig.text(.045,.945,"住宅与园校样本定位",fontsize=21,weight=500,color="#19374B")
    fig.text(.045,.907,"猎德及周边｜仅绘已定位候选，不表达房价梯度或设施密度",fontsize=10)
    ax = fig.add_axes([.065,.245,.585,.60])
    panel = fig.add_axes([.70,.25,.28,.60])
    panel.axis("off")
    mapped_home = [r for r in homes if r["longitude"] is not None]
    mapped_campus = [r for r in campuses if r["longitude"] is not None]
    points = [xy(r["longitude"],r["latitude"]) for r in mapped_home+mapped_campus+unresolved]
    xs,ys = zip(*points)
    ax.set_xlim(min(xs)-280,max(xs)+280)
    ax.set_ylim(min(ys)-260,max(ys)+260)
    ax.set_aspect("equal",adjustable="box")
    osm = json.loads((ctx.root/EDUCATION/"地图/OSM_猎德周边_20261112.json").read_text())
    roads = []
    for element in osm["elements"]:
        tags,geometry = element.get("tags",{}),element.get("geometry",[])
        if not geometry:
            continue
        line = [xy(p["lon"],p["lat"]) for p in geometry if "lon" in p and "lat" in p]
        if tags.get("natural")=="water" and len(line)>2:
            x,y = zip(*line)
            ax.fill(x,y,color="#EEF4F7",zorder=0)
        if tags.get("highway"):
            roads.append(line)
    ax.add_collection(LineCollection(roads,colors="#DDE4E8",linewidths=.45,zorder=1))
    colors = {"public":"#27736F","education_department":"#27736F","private":"#AA743B","other_department":"#836C99"}
    for r in mapped_campus:
        x,y = xy(r["longitude"],r["latitude"])
        converted = r["coordinate_status"]=="transformed_poi_estimate"
        ax.scatter(x,y,s=34,marker="s" if r["stage"]=="primary" else "^",
                   facecolor="white" if converted else colors[r["ownership"]],
                   edgecolor=colors[r["ownership"]] if converted else "white",linewidth=1 if converted else .45,zorder=3)
    offsets = {"RES001":(-6,-17),"RES003":(5,7),"RES011":(-3,8),"RES015":(6,-15),"RES018":(5,-17)}
    for r in mapped_home:
        x,y = xy(r["longitude"],r["latitude"])
        ax.scatter(x,y,s=108,marker="D" if r["residence_id"]=="RES001" else "o",
            facecolor="#F1F4F6",
            edgecolor="#16384A",linewidth=1.3,zorder=6)
        label = "R"+r["residence_id"][-2:]+("~" if r["coordinate_status"]=="transformed_poi_estimate" else "")
        ax.annotate(label,(x,y),xytext=offsets.get(r["residence_id"],(6,7)),textcoords="offset points",
            fontsize=9,weight=500,zorder=7,bbox=dict(facecolor="white",edgecolor="none",pad=.6,alpha=.8))
    ax.set_xlabel("相对本地原点的向东距离（米）",fontsize=9)
    ax.set_ylabel("相对本地原点的向北距离（米）",fontsize=9)
    ax.tick_params(labelsize=9)
    ax.grid(color="#EAEFF2",linewidth=.5,zorder=0)
    handles = [Line2D([],[],marker="s",linestyle="",color="#4A5964",label="小学校区"),
        Line2D([],[],marker="^",linestyle="",color="#4A5964",label="幼儿园园区"),
        Line2D([],[],marker="o",linestyle="",color="#27736F",label="公办小学／教育部门办园"),
        Line2D([],[],marker="o",linestyle="",color="#AA743B",label="民办"),
        Line2D([],[],marker="o",linestyle="",color="#836C99",label="其他部门办园（含国企）"),
        Line2D([],[],marker="^",markerfacecolor="white",linestyle="",color="#27736F",label="坐标转换后的园校POI")]
    panel.text(0,1.0,"地图证据覆盖",fontsize=13,weight=500,color="#19374B")
    kg = sum(r["stage"]=="kindergarten" for r in mapped_campus)
    primary = sum(r["stage"]=="primary" for r in mapped_campus)
    kg_total = sum(r["stage"]=="kindergarten" for r in campuses)
    primary_total = sum(r["stage"]=="primary" for r in campuses)
    panel.text(0,.93,f"住宅：{len(mapped_home)}/{len(homes)}\n幼儿园：{kg}/{kg_total}　小学：{primary}/{primary_total}",fontsize=10)
    panel.legend(handles=handles,loc="upper left",bbox_to_anchor=(-.02,.83),fontsize=9,frameon=False,labelspacing=.8)
    panel.text(0,.48,"住宅项目参照",fontsize=12,weight=500)
    rows = [r for key in ["RES003","RES011","RES015","RES001","RES018"] for r in mapped_home if r["residence_id"]==key]
    names = {"RES003":"花城湾","RES011":"利雅湾","RES015":"璟晖华庭","RES001":"猎德花园*","RES018":"南国花园"}
    for i,r in enumerate(rows):
        panel.text(0,.415-i*.067,f"R{r['residence_id'][-2:]}  {names[r['residence_id']]}",fontsize=9)
    panel.text(0,.002,"住宅颜色不编码价格。\n* 仅五区参照，与交通起点分开。\n~ 表示转换POI；实际入口未核。\n待核旧地图点仅保留在源数据。",fontsize=9,linespacing=1.5)
    fig.text(.06,.13,"定位覆盖按学段不均，未定位对象不补点；不据此比较片区供给密度或空间聚集。",fontsize=10)
    fig.text(.06,.075,"来源：官方园校名录、仓库住宅参照、OpenStreetMap贡献者（ODbL）、高德POI转换。",fontsize=9)
    save(fig,"figure_A_housing_education")

    # 沿用既有双系列图的研究对照与配色，只向本模块导出。
    fig = plt.figure(figsize=(11,6.8),facecolor="white")
    fig.text(.045,.945,"School walking times by admission channel",fontsize=19,color="#19374B")
    fig.text(.045,.895,"Grade 1 in Tianhe, 2026 | Three origins, two specified destination choices",fontsize=10)
    ax = fig.add_axes([.275,.285,.68,.46])
    comparisons = [r for r in ctx.table("accessibility_comparisons") if r["channel"]!="hk_macao_listed_channel"]
    channels = [("address_linked_conditional","o","#27736F",.12,"Address-linked school (conditional)"),
        ("migrant_points_listed_example","s","#8A6287",-.12,"Points example: Xian Cun Primary")]
    for y,origin in zip([2,1,0],["D1","D2","D3"]):
        rows = [r for r in comparisons if r["origin_legacy_id"]==origin]
        ax.hlines(y,min(r["walk_minutes"] for r in rows),max(r["walk_minutes"] for r in rows),color="#D5DFE4",linewidth=2)
        for channel,marker,color,offset,label in channels:
            r=next(r for r in rows if r["channel"]==channel)
            value=r["walk_minutes"]
            ax.scatter(value,y+offset,marker=marker,color=color,s=70,zorder=3)
            ax.annotate(f"{value:.1f}",(value,y+offset),xytext=(7,0),textcoords="offset points",va="center",fontsize=11,color=color)
    ax.set_xlim(0,32.5)
    ax.set_ylim(-.5,2.5)
    ax.set_yticks([2,1,0],labels=["D1  Liede Garden","D2  Jinghui Huating","D3  Nanguo Garden"])
    ax.tick_params(axis="y",length=0,labelsize=10,pad=12)
    ax.tick_params(axis="x",length=0,labelsize=10)
    ax.grid(axis="x",color="#E1E8EC",linewidth=.7)
    ax.set_xlabel("One-way Amap walking estimate (minutes)",fontsize=10,labelpad=10)
    for spine in ax.spines.values():
        spine.set_visible(False)
    handles=[Line2D([],[],marker=m,color=c,linestyle="",label=label,markersize=7) for _,m,c,_,label in channels]
    fig.legend(handles=handles,loc="upper center",bbox_to_anchor=(.61,.84),ncol=2,frameon=False,fontsize=9)
    fig.text(.045,.17,"Address-linked eligibility requires household and address documents. Xian Cun is one listed preference example.\nBoth series use archived point-to-point Amap estimates; gates, actual allocations and commutes were unobserved.",fontsize=9,linespacing=1.6)
    fig.text(.045,.065,"Sources: Amap, 12 Nov 2026; Tianhe 2026 primary catchment rules and migrant-points intake list.\nPurposeful case comparison; no housing-cost ranking or nearest-eligible-school claim.",fontsize=9,linespacing=1.6)
    save(fig,"figure_B_admission_accessibility")
    write_json(destination/"figure_qa.json",dict(data_version=version,figures=qa,
        display_projection="EPSG:32649，本地原点113.332E/23.121N",
        analytical_coordinates="EPSG:4326",visual_review="视觉核对记录见../VERIFICATION.md；证据或绘图变化后重新检查"))
    legends = """# 最终图件图注与使用说明

## 图 A｜住宅与园校样本定位（辅助空间背景）

仅绘已定位住宅与园校：住宅5/18，幼儿园14/30，小学12/13。住宅统一中性色，不编码房价、租金或收入。定位覆盖按学段不均，不据此推断设施密度、聚集或房价梯度。住宅R01菱形为猎德花园五区参照，与交通起点分开。园校形状区分学段，颜色区分办学类别，空心为GCJ-02转换POI，均未确认实际接送门。P03旧地图候选保留在 `figure_A_unresolved.csv` 供核查，避免与正式参照在主图重复画点。底图署名：© OpenStreetMap贡献者，ODbL。

源数据：`figure_source_data/figure_A_housing.csv`、`figure_A_campuses.csv`、`figure_A_unresolved.csv`。住房价格仍在数据中保存，但本图不使用价格字段。已定位候选不代表全量名录。

## 图 B｜不同招生渠道的指定小学路线（主图，英文）

沿用原双系列路线图的比较与配色，按最终数据重绘到整合模块，不运行旧图件覆盖脚本。六个点对应六条独立路线、三个住宅起点：条件性地段对应小学与来穗积分名单内的冼村小学志愿例。地段对应须核户籍、产权、实际居住、门牌和学位占用等；冼村小学不代表实际分配或已证明的最近可申请校。两组均为2026-11-12高德POI到POI模型估算，不是实走、录取或家庭通学观察。不展示混合住房报价。

南国花园两条指定路线为166秒与1706秒，差1540秒约25.7分钟；单项先按秒换算，差值也先按秒求差再四舍五入。港澳一年级安排按公示后积分排名依次至南国学校小学部，计划45人；该起点与地段对应目的地重合，作为补充表保留，不加入主图第三系列。

源数据：`figure_source_data/figure_B_comparisons.csv`（6行主图）、`figure_B_secondary_channels.csv`（3行港澳补充）；完整9行见 `data/accessibility_comparisons.csv`。旧住房背景源表保留用于追溯，不用于主图标签。统计单元是模型路线，非家庭样本，不作总体检验或置信区间。

## 幼儿园最近值与路线质量

原六园下，南国花园最近任一园388秒（约6.5分钟）；扩展已测候选后海滨园238秒（约4.0分钟），属普惠性民办。K7物理园区关联已有依据，但D3至K7原18米短于约51.6米端点直距，仍排除；不能推定其有效距离。两条其他起点至K7旧名POI路线仅可带标签作补充分析。全部42条按39条普通POI、2条旧名地址匹配及1条异常排除分别解释。
"""
    (destination/"FIGURE_LEGENDS.md").write_text(legends)
