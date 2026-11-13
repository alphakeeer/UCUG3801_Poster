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

    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,
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
            raise ValueError(f"Figure text outside canvas in {name}: {outside}")
        fig.savefig(output/(name+".png"),dpi=300,metadata={"Software":"UCUG3801 integration pipeline"})
        fig.savefig(output/(name+".svg"),metadata={"Date":None,"Creator":"UCUG3801 integration pipeline"})
        fig.savefig(output/(name+".pdf"),metadata={"CreationDate":None,"ModDate":None,"Creator":"UCUG3801 integration pipeline"})
        qa.append(dict(figure=name,backend="matplotlib",text_outside_canvas=outside,
            source_data="figure_source_data/",formats=["png","svg","pdf"],
            causal_or_population_inference=False,statistical_tests="none; purposeful case sample"))
        plt.close(fig)

    # Figure A: one map, with separate metric/missingness summaries.
    fig = plt.figure(figsize=(12,8.3),facecolor="white")
    fig.text(.045,.945,"Housing and educational facilities",fontsize=21,weight="bold",color="#19374B")
    fig.text(.045,.907,"Liede and surrounding candidates | archived 2026 housing references, not transaction estimates",fontsize=10)
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
            fontsize=9,weight="bold",zorder=7,bbox=dict(facecolor="white",edgecolor="none",pad=.6,alpha=.8))
    ax.set_xlabel("Easting relative to local origin (m)",fontsize=9)
    ax.set_ylabel("Northing relative to local origin (m)",fontsize=9)
    ax.tick_params(labelsize=9)
    ax.grid(color="#EAEFF2",linewidth=.5,zorder=0)
    handles = [Line2D([],[],marker="s",linestyle="",color="#4A5964",label="Primary campus"),
        Line2D([],[],marker="^",linestyle="",color="#4A5964",label="Kindergarten campus"),
        Line2D([],[],marker="o",linestyle="",color="#27736F",label="Public / education dept."),
        Line2D([],[],marker="o",linestyle="",color="#AA743B",label="Private"),
        Line2D([],[],marker="o",linestyle="",color="#836C99",label="Other department"),
        Line2D([],[],marker="x",linestyle="",color="#888888",label="Unresolved map candidate"),
        Line2D([],[],marker="^",markerfacecolor="white",linestyle="",color="#27736F",label="Converted campus POI")]
    panel.text(0,1.0,"Mapped evidence",fontsize=13,weight="bold",color="#19374B")
    panel.text(0,.93,f"Residences: {len(mapped_home)}/{len(homes)}   Campuses: {len(mapped_campus)}/{len(campuses)}",fontsize=10)
    panel.legend(handles=handles,loc="upper left",bbox_to_anchor=(-.02,.89),fontsize=9,frameon=False,labelspacing=.8)
    panel.text(0,.48,"Selected housing markers",fontsize=12,weight="bold")
    rows = [r for key in ["RES003","RES011","RES015","RES001","RES018"] for r in mapped_home if r["residence_id"]==key]
    names = {"RES003":"Huacheng Bay","RES011":"Liyawan","RES015":"Jinghui Huating","RES001":"Liede Garden*","RES018":"Nanguo Garden"}
    for i,r in enumerate(rows):
        value = r["sale_reference_cny_m2"]
        metric = f"{value/10000:.2f}" if value is not None else "not comparable" if r["sale_status"]=="not_comparable" else "missing"
        panel.text(0,.415-i*.067,f"R{r['residence_id'][-2:]}  {names[r['residence_id']]}: {metric}",fontsize=9)
    panel.text(0,.002,"Values: 10,000 CNY/m²; mixed months.\n* Phase-5 map reference, not route origin.\nWhite homes: missing / non-comparable.\n~ indicates a converted residential POI.",fontsize=9,linespacing=1.5)
    cax = fig.add_axes([.16,.158,.38,.018])
    if values:
        cb = fig.colorbar(ScalarMappable(norm=norm,cmap=cmap),cax=cax,orientation="horizontal")
        cb.set_label("Mapped comparable platform sale reference (10,000 CNY/m²)",fontsize=9)
        cb.ax.tick_params(labelsize=9)
    else:
        cax.axis("off")
        cax.text(0,0,"No comparable mapped sale reference remains after review flags",fontsize=9)
    rent = [r for r in mapped_home if r["rent_cny_m2_month"] is not None]
    rent_text = "; ".join(f"R{r['residence_id'][-2:]} {r['rent_cny_m2_month']:.2f}" for r in rent)
    fig.text(.06,.075,"Separate mapped rental examples (CNY/m²/month): "+rent_text+". Unmatched dwelling sizes; not development means.",fontsize=9)
    fig.text(.06,.043,"Sources: archived housing extracts; education listings; OpenStreetMap contributors (ODbL); transformed Amap POIs. Missing locations remain in source data.",fontsize=9)
    save(fig,"figure_A_housing_education")

    # Figure B: the original traffic model, connected to housing evidence and rules.
    fig = plt.figure(figsize=(11,6.8),facecolor="white")
    fig.text(.045,.945,"Housing, admission channels and modeled walks",fontsize=19,weight="bold",color="#19374B")
    fig.text(.045,.90,"Three residential origins | primary grade 1, 2026 | conditional pathways, no observed allocations",fontsize=10)
    ax = fig.add_axes([.345,.29,.61,.45])
    comparisons = ctx.table("accessibility_comparisons")
    channels = [("address_linked_conditional","o","#27736F",.17,"Address-linked\nconditions apply"),
        ("migrant_points_listed_example","s","#8A6287",0,"Migrant-points example\nXian Cun Primary"),
        ("hk_macao_listed_channel","D","#AA743B",-.17,"HK/Macao listed channel\nNanguo Primary")]
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
        if r["sale_reference_cny_m2"] is not None:
            detail = f"Platform reference {r['sale_reference_cny_m2']:,.0f} CNY/m²"
        elif r["rent_cny_month"] is not None:
            detail = f"Rent quote {r['rent_cny_month']:,.0f} CNY/month"
        else:
            detail = "Housing costs missing / require review"
        name = {"D1":"Liede Garden","D2":"Zhonghai Jinghui Huating","D3":"Nanguo Garden"}[origin]
        labels.append(f"{origin}  {name}\n{detail}")
    ax.set_yticks([2,1,0],labels=labels)
    ax.tick_params(axis="y",length=0,labelsize=9,pad=12)
    ax.tick_params(axis="x",length=0,labelsize=10)
    ax.grid(axis="x",color="#E1E8EC",linewidth=.7)
    ax.set_xlabel("One-way Amap walking estimate (minutes)",fontsize=10,labelpad=10)
    for spine in ax.spines.values():
        spine.set_visible(False)
    handles = [Line2D([],[],marker=m,color=c,linestyle="",label=label,markersize=7) for _,m,c,_,label in channels]
    fig.legend(handles=handles,loc="upper center",bbox_to_anchor=(.61,.86),ncol=3,frameon=False,fontsize=9,columnspacing=1.5)
    fig.text(.045,.155,"Eligibility: full ownership, hukou, exact address, lease or points documentation still require review.\nRenters' coordinated destinations and actual admissions remain unknown; Xian Cun is one listed option.",fontsize=9,linespacing=1.7)
    fig.text(.045,.058,"All times use archived POI routes; gates and actual trips were unobserved. Housing indicators describe different evidence types.\nSources: Amap snapshot, 12 Nov 2026; Tianhe 2026 admissions and channel plans; archived housing quotations.",fontsize=9,linespacing=1.7)
    save(fig,"figure_B_admission_accessibility")
    write_json(destination/"figure_qa.json",dict(data_version=version,figures=qa,
        display_projection="EPSG:32649, local origin 113.332E/23.121N",
        analytical_coordinates="EPSG:4326",visual_review="V1 visual inspection is recorded in ../VERIFICATION.md; repeat visual review after evidence changes"))
    legends = """# Figure legends and source data

## Figure A | Housing and educational facilities

An offline OSM reference map juxtaposes the mapped subset of residences and primary/kindergarten campuses. Residence shading encodes archived comparable platform sale references, in 10,000 CNY/m². Reference months differ. White residence markers indicate missing or non-comparable sale evidence; the Liede Garden diamond represents a phase-5 reference, distinct from the transport-origin POI. Rental examples retain separate units and unmatched dwelling sizes. Campus shapes encode stage and colors encode ownership category. Grey crosses are unresolved map candidates and are excluded from accepted campus counts. Approximate GCJ-02 conversion is flagged in source data. No price surface, income classification, school quality inference or geographic census is claimed. OSM attribution: © OpenStreetMap contributors, ODbL.

Source data: `figure_source_data/figure_A_housing.csv`, `figure_A_campuses.csv`, `figure_A_unresolved.csv`. These contain canonical IDs and source references; full observations are in `data/housing_observations.csv`, `data/positions.csv`, `data/source_registry.csv`.

## Figure B | Housing, admission channels and modeled walks

Nine route/channel comparisons describe three purposeful residential cases. Address-linked schools are conditional on full eligibility verification. Xian Cun is one migrant-points listed choice; it is neither an allocation nor an established nearest eligible destination. Nanguo Primary is also listed for the separate HK/Macao channel. No actual household admission, commute or fee burden was observed. Housing labels describe distinct contextual evidence, not household income. Times are archived 2026 Amap POI-to-POI estimates, without confirmed gates. There are no statistical tests or population confidence intervals.

Source data: `figure_source_data/figure_B_comparisons.csv` and `figure_B_housing_context.csv`, linked through route, housing observation, residence and rule IDs to `data/transport_routes.csv`, `data/housing_observations.csv`, `data/admission_rules.csv` and `data/source_registry.csv`.
"""
    (destination/"FIGURE_LEGENDS.md").write_text(legends)
