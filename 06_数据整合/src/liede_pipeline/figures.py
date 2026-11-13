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
    from matplotlib.cm import ScalarMappable
    from matplotlib.colors import Normalize
    from matplotlib.colors import LinearSegmentedColormap
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
                      ("figure_B_comparisons",ctx.table("accessibility_comparisons")),
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
    fig.text(.045,.945,"住房与幼儿园、小学的空间分布",fontsize=21,weight=500,color="#19374B")
    fig.text(.045,.907,"猎德及周边候选设施｜2026仓库住房报价，指标与月份分别保留",fontsize=10)
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
    for r in unresolved:
        x,y = xy(r["longitude"],r["latitude"])
        ax.scatter(x,y,s=75,marker="x",color="#888888",linewidth=1.2,zorder=4)
    quoted = [r for r in mapped_home if r["sale_reference_cny_m2"] is not None]
    values = [r["sale_reference_cny_m2"]/10000 for r in quoted]
    low,high = (min(values),max(values)) if values else (0,1)
    norm = Normalize(low,high if high>low else low+1)
    blues = plt.get_cmap("Blues")
    cmap = LinearSegmentedColormap.from_list("ReferenceBlues",[blues(.3+.65*i/63) for i in range(64)])
    offsets = {"RES001":(-6,-17),"RES003":(5,7),"RES011":(-3,8),"RES015":(6,-15),"RES018":(5,-17)}
    for r in mapped_home:
        x,y = xy(r["longitude"],r["latitude"])
        value = r["sale_reference_cny_m2"]
        ax.scatter(x,y,s=108,marker="D" if r["sale_status"]=="not_comparable" else "o",
            facecolor=cmap(norm(value/10000)) if value is not None else "white",
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
        Line2D([],[],marker="x",linestyle="",color="#888888",label="未确认地图候选"),
        Line2D([],[],marker="^",markerfacecolor="white",linestyle="",color="#27736F",label="坐标转换后的园校POI")]
    panel.text(0,1.0,"地图证据覆盖",fontsize=13,weight=500,color="#19374B")
    panel.text(0,.93,f"住宅：{len(mapped_home)}/{len(homes)}　园校：{len(mapped_campus)}/{len(campuses)}",fontsize=10)
    panel.legend(handles=handles,loc="upper left",bbox_to_anchor=(-.02,.89),fontsize=9,frameon=False,labelspacing=.8)
    panel.text(0,.48,"住宅标记与参考价",fontsize=12,weight=500)
    rows = [r for key in ["RES003","RES011","RES015","RES001","RES018"] for r in mapped_home if r["residence_id"]==key]
    names = {"RES003":"花城湾","RES011":"利雅湾","RES015":"璟晖华庭","RES001":"猎德花园*","RES018":"南国花园"}
    for i,r in enumerate(rows):
        value = r["sale_reference_cny_m2"]
        metric = f"{value/10000:.2f}" if value is not None else "不可比" if r["sale_status"]=="not_comparable" else "缺失"
        panel.text(0,.415-i*.067,f"R{r['residence_id'][-2:]}  {names[r['residence_id']]}: {metric}",fontsize=9)
    panel.text(0,.002,"单位：万元/平方米；参考月份不同。\n* 五区参照点，与路线起点分开。\n白色住宅：参考价缺失或不可比。\n~ 表示坐标转换后的住宅POI。",fontsize=9,linespacing=1.5)
    cax = fig.add_axes([.16,.158,.38,.018])
    if values:
        cb = fig.colorbar(ScalarMappable(norm=norm,cmap=cmap),cax=cax,orientation="horizontal")
        cb.set_label("已定位、可比较的平台参考价（万元/平方米；非成交价）",fontsize=9)
        cb.ax.tick_params(labelsize=9)
    else:
        cax.axis("off")
        cax.text(0,0,"当前没有可展示的同口径、已定位参考价",fontsize=9)
    rent = [r for r in mapped_home if r["rent_cny_m2_month"] is not None]
    rent_text = "; ".join(f"R{r['residence_id'][-2:]} {r['rent_cny_m2_month']:.2f}" for r in rent)
    fig.text(.06,.075,"已定位租赁例证（元/平方米/月）："+rent_text+"。面积不同，不代表小区均价。",fontsize=9)
    fig.text(.06,.043,"来源：仓库住房摘录、官方园校名录、OpenStreetMap贡献者（ODbL）、高德POI转换。未定位对象保留在源数据。",fontsize=9)
    save(fig,"figure_A_housing_education")

    # Figure B: the original traffic model, connected to housing evidence and rules.
    fig = plt.figure(figsize=(11,6.8),facecolor="white")
    fig.text(.045,.945,"住房背景、招生渠道与步行可达性",fontsize=19,weight=500,color="#19374B")
    fig.text(.045,.90,"三个住宅起点｜2026小学一年级｜条件性申请渠道；实际录取未观察",fontsize=10)
    ax = fig.add_axes([.345,.29,.61,.45])
    comparisons = ctx.table("accessibility_comparisons")
    channels = [("address_linked_conditional","o","#27736F",.17,"地址对应小学\n须核完整资格"),
        ("migrant_points_listed_example","s","#8A6287",0,"来穗积分志愿例\n冼村小学"),
        ("hk_macao_listed_channel","D","#AA743B",-.17,"港澳单列渠道\n南国学校小学部")]
    for y,origin in zip([2,1,0],["D1","D2","D3"]):
        rows = [r for r in comparisons if r["origin_legacy_id"]==origin]
        ax.hlines(y,min(r["walk_minutes"] for r in rows),max(r["walk_minutes"] for r in rows),color="#D5DFE4",linewidth=2)
        for channel,marker,color,offset,label in channels:
            r = next(r for r in rows if r["channel"]==channel)
            value = r["walk_minutes"]
            ax.scatter(value,y+offset,marker=marker,color=color,s=65,zorder=3)
            ax.annotate(f"{value:.1f}",(value,y+offset),xytext=(7,0),textcoords="offset points",va="center",fontsize=10,color=color)
    ax.set_xlim(0,max(r["walk_minutes"] for r in comparisons)+5)
    ax.set_ylim(-.5,2.5)
    cost_by_id = {r["residence_id"]:r for r in homes}
    labels = []
    for origin,entity in [("D1","RES001"),("D2","RES015"),("D3","RES018")]:
        r = cost_by_id[entity]
        rents = [o for o in ctx.table("housing_observations") if o["id"] in r["rent_observation_ids"] and o["evidence_type"]=="listing_example"]
        if r["sale_reference_cny_m2"] is not None:
            detail = f"平台参考价 {r['sale_reference_cny_m2']:,.0f}元/平方米"
        elif rents:
            detail = f"{len(rents)}条整租挂牌："+"、".join(f"{v:g}" for v in sorted({o["value"] for o in rents}))+"元/月"
        elif r["rent_cny_month"] is not None:
            detail = f"租金报价 {r['rent_cny_month']:,.0f}元/月"
        else:
            detail = "住房成本缺失／需核对"
        name = {"D1":"猎德花园","D2":"中海璟晖华庭","D3":"南国花园"}[origin]
        labels.append(f"{origin}  {name}\n{detail}")
    ax.set_yticks([2,1,0],labels=labels)
    ax.tick_params(axis="y",length=0,labelsize=9,pad=12)
    ax.tick_params(axis="x",length=0,labelsize=10)
    ax.grid(axis="x",color="#E1E8EC",linewidth=.7)
    ax.set_xlabel("高德单程步行估算（分钟）",fontsize=10,labelpad=10)
    for spine in ax.spines.values():
        spine.set_visible(False)
    handles = [Line2D([],[],marker=m,color=c,linestyle="",label=label,markersize=7) for _,m,c,_,label in channels]
    fig.legend(handles=handles,loc="upper center",bbox_to_anchor=(.61,.86),ncol=3,frameon=False,fontsize=9,columnspacing=1.5)
    fig.text(.045,.155,"资格须核户籍、产权、具体门牌、备案或积分材料；安置户与合格租户按相应统筹条件审核。\n租户实际统筹去向及家庭录取未观察；冼村小学仅为一个名单内志愿例。",fontsize=9,linespacing=1.7)
    fig.text(.045,.058,"路线使用归档POI，实际校门和真实通学未观察。住房标签指标不同；南国两条租盘不合成均价。\n来源：2026-11-12高德路线；天河2026招生与渠道计划；原住房摘录及11月13日补证。",fontsize=9,linespacing=1.7)
    save(fig,"figure_B_admission_accessibility")
    write_json(destination/"figure_qa.json",dict(data_version=version,figures=qa,
        display_projection="EPSG:32649，本地原点113.332E/23.121N",
        analytical_coordinates="EPSG:4326",visual_review="视觉核对记录见../VERIFICATION.md；证据或绘图变化后重新检查"))
    legends = """# 中文图注与图件源数据

## 图 A｜住房与幼儿园、小学的空间分布

离线OSM参照图叠加已定位住宅及园校候选子集。住宅蓝色深浅表示归档平台参考价，单位万元/平方米，参考月份不同；不是登记成交，也不用于家庭收入分类。白色表示参考价缺失或不可比，猎德花园菱形为五区参照点，与海文路交通起点分开。租金例证另用元/平方米/月，不按不同面积、日期的挂牌计算小区均价。南国花园有两条新增整租例证，但小区参考价仍缺失。

园校形状区分小学与幼儿园，颜色区分办学类别。空心表示经过GCJ-02到WGS84转换的园校POI；灰叉为未确认候选，不计入已接受位置。K7旧地图别名已由2026官方地址与同一POI支持关联，实际园门和配套范围仍未核。华文为国企办园、海滨为普惠性民办，均为原有候选的补充定位。图未绘房价插值面，未推断学校质量、官方服务边界或因果关系。底图署名：© OpenStreetMap贡献者，ODbL。

源数据：`figure_source_data/figure_A_housing.csv`、`figure_A_campuses.csv`、`figure_A_unresolved.csv`，含规范ID与来源引用。原值及位置角色另见 `data/housing_observations.csv`、`data/positions.csv`、`data/work_evidence.csv`和 `data/source_registry.csv`。

## 图 B｜住房背景、招生渠道与步行可达性

九条住宅—申请渠道比较对应三个目的性案例起点。地址对应小学须核完整资格；拆迁安置及合格租户分别依其条件进入统筹，去向未观察。冼村小学只是一个积分名单内志愿例，不代表实际录取或已证明的最近可申请校。南国学校小学部另列港澳渠道。住房标签为不同类型的背景证据，不能解释为家庭收入。南国花园两条整租挂牌分别为2026-09-20与2026-11-10的个案，不合成均价。

时间为2026-11-12高德POI到POI单程模型估算，实际接送门及通学没有实测。11月13日新增三条幼儿园路线另存，未改变本图九条小学比较和原六园敏感性分母。南国花园至海滨园298米、238秒约4.0分钟，仅为扩展已测候选的最近值，不推断整个地区或实际可录取范围。没有总体统计检验、误差条或置信区间。

源数据：`figure_source_data/figure_B_comparisons.csv`和 `figure_B_housing_context.csv`，经路线、住房观察、住宅和规则ID连接到 `data/transport_routes.csv`、`data/housing_observations.csv`、`data/admission_rules.csv`、`data/admission_conditions.csv`和 `data/source_registry.csv`。
"""
    (destination/"FIGURE_LEGENDS.md").write_text(legends)
