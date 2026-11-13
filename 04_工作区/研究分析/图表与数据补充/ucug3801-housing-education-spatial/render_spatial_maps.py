import argparse
import csv
import gzip
import json
import math
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.path import Path as MPath
from matplotlib.transforms import Bbox
from pyproj import Transformer

parser = argparse.ArgumentParser()
parser.add_argument("package", type=Path)
parser.add_argument("--osm", type=Path, required=True)
parser.add_argument("--font", type=Path, required=True, help="Chinese-capable font such as msyh.ttc or Noto Sans CJK SC")
args = parser.parse_args()
root = args.package
font_manager.fontManager.addfont(str(args.font))
font = font_manager.FontProperties(fname=str(args.font)).get_name()
plt.rcParams.update({"font.family": [font, "DejaVu Sans"], "axes.unicode_minus": False,
    "pdf.fonttype": 42, "svg.fonttype": "path", "svg.hashsalt": "liedehousing2026"})

def read(name):
    with (root / "data" / (name + ".csv")).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

homes = read("housing_projects")
campuses = read("campuses")
spec = json.loads((root / "data/map_scope.json").read_text(encoding="utf-8"))
with (gzip.open(args.osm, "rt", encoding="utf-8-sig") if args.osm.suffix == ".gz" else args.osm.open(encoding="utf-8-sig")) as f:
    osm = json.load(f)["elements"]
xy = Transformer.from_crs(4326, 32649, always_xy=True).transform
ink = "#162d42"
muted = "#536978"
faint = "#dce6e8"
water = "#d6eaf1"
park = "#e4edda"
land = "#f7f8f5"
housing_colors = ["#dbeafa", "#a8d0ea", "#64a5d1", "#337cb5", "#164a7d"]
band_edges = spec["reference_price_bands_wan_cny_m2"]
band_names = ["<8", "8–<10", "10–<12", "12–<14", "≥14"]
school_colors = {"public":"#14766d","education_department":"#14766d",
    "private":"#b55722","other_department":"#8157a4"}
legend_pairs = [
    ("s", "public", "公办小学", "Public primary"),
    ("s", "private", "民办小学", "Private primary"),
    ("^", "education_department", "教育部门办园", "Education dept. KG"),
    ("^", "other_department", "其他部门办园", "Other dept. KG"),
    ("^", "private", "民办幼儿园", "Private KG"),
]
base_roads = {"motorway":(2.1,"#c8c6b9"),"trunk":(1.9,"#d4cdbb"),"primary":(1.65,"#d7cdb8"),
    "secondary":(1.25,"#d8d3c7"),"tertiary":(.77,"#dedfd8"),"residential":(.55,"#dedfd8"),
    "pedestrian":(.46,"#e2e6df"),"service":(.36,"#e8e9e4"),"footway":(.32,"#e9ebe6")}
road_label_settings = {
    "黄埔大道西":((113.324,23.1286),0),
    "金穗路":((113.3187,23.1245),0),
    "花城大道":((113.3185,23.1205),0),
    "临江大道":((113.3427,23.1151),0),
    "猎德大道":((113.331,23.1303),75),
    "马场路":((113.3347,23.1234),75),
    "平月路":((113.3389,23.1216),72),
}

def mapped(row, name):
    return row["in_" + name + "_map"] == "True"

def project(row):
    return xy(float(row["longitude_wgs84"]), float(row["latitude_wgs84"]))

def geo(el):
    return [(p["lon"],p["lat"]) for p in el.get("geometry", []) if p and "lon" in p]

def rings(parts):
    pieces = [list(p) for p in parts if len(p)>1]
    while pieces:
        chain = pieces.pop()
        while chain[0] != chain[-1]:
            for i,p in enumerate(pieces):
                if p[0]==chain[-1]:
                    chain.extend(p[1:])
                elif p[-1]==chain[-1]:
                    chain.extend(p[-2::-1])
                elif p[-1]==chain[0]:
                    chain=p[:-1]+chain
                elif p[0]==chain[0]:
                    chain=p[:0:-1]+chain
                else:
                    continue
                pieces.pop(i)
                break
            else:
                break
        if len(chain)>3 and chain[0]==chain[-1]:
            yield chain

def append_ring(vertices, codes, ring, inner):
    p = [xy(*v) for v in ring]
    signed = sum(x*v-u*y for (x,y),(u,v) in zip(p,p[1:]))
    if (signed < 0) != inner:
        p.reverse()
    vertices.extend(p)
    codes.extend([MPath.MOVETO]+[MPath.LINETO]*(len(p)-2)+[MPath.CLOSEPOLY])

def intersects(coords, extent, padding=.004):
    w,s,e,n=extent
    return coords and min(x for x,y in coords)<=e+padding and max(x for x,y in coords)>=w-padding and min(y for x,y in coords)<=n+padding and max(y for x,y in coords)>=s-padding

def draw_basemap(ax, extent, poster):
    for e in osm:
        t=e.get("tags", {})
        line=geo(e)
        if not intersects(line, extent):
            continue
        if t.get("leisure")=="park" and len(line)>3 and line[0]==line[-1]:
            ax.fill(*zip(*(xy(*p) for p in line)), facecolor=park, edgecolor="#d4e1cc", linewidth=.5, zorder=.6)
        if t.get("natural")=="water" and len(line)>3 and line[0]==line[-1]:
            ax.fill(*zip(*(xy(*p) for p in line)), facecolor=water, edgecolor="none", zorder=.65)
    for e in osm:
        if e["type"]!="relation" or e.get("tags",{}).get("natural")!="water":
            continue
        parts=e.get("members",[])
        v,c=[],[]
        for role in ("outer","inner"):
            for ring in rings(geo(part) for part in parts if part.get("role")==role):
                if intersects(ring,extent):
                    append_ring(v,c,ring,role=="inner")
        if v:
            ax.add_patch(PathPatch(MPath(v,c),facecolor=water,edgecolor="none",zorder=.7))
    roads={h:[] for h in base_roads}
    locations={n:[] for n in road_label_settings}
    for e in osm:
        t=e.get("tags",{})
        h=t.get("highway")
        name=t.get("name","")
        if h not in roads or t.get("tunnel") in {"yes","building_passage"} or t.get("location")=="underground":
            continue
        if poster and h in {"footway","service"}:
            continue
        line=geo(e)
        if len(line)<2 or not intersects(line,extent):
            continue
        roads[h].append([xy(*p) for p in line])
        if name in locations:
            locations[name].extend(line)
    for h in reversed(base_roads):
        width,color=base_roads[h]
        ax.add_collection(LineCollection(roads[h], linewidths=width, colors=color, zorder=1.5, capstyle="round"))
    return locations

def price_style(h):
    v=h["map_price_cny_m2"]
    if v:
        number=float(v)/10000
        band=sum(number>=edge for edge in band_edges[1:-1])
        return "o", housing_colors[band]
    return ({"product_not_comparable":"D","other_price_metric":"h","comparable_price_missing":"D"}.get(h["map_price_status"],"D"), "#ffffff")

def draw_scale(ax, poster):
    x0,x1=ax.get_xlim()
    y0,y1=ax.get_ylim()
    x=x0+.035*(x1-x0)
    y=y0+.063*(y1-y0)
    d=500
    thickness=.008*(y1-y0)
    for i in range(2):
        ax.add_patch(Rectangle((x+i*d/2,y),d/2,thickness,facecolor=ink if i==0 else "white",edgecolor=ink,linewidth=.7,zorder=8))
    size=8 if poster else 9
    for xx,label in [(x,"0"),(x+d,"500 m")]:
        ax.text(xx,y+thickness*2.1,label,ha="center",va="bottom",fontsize=size,color=ink,zorder=9)
    ax.annotate("N",xy=(.962,.954),xytext=(.962,.858),xycoords="axes fraction",textcoords="axes fraction",
        ha="center",va="center",fontsize=11,color=ink,arrowprops={"arrowstyle":"-|>","lw":1.4,"color":ink,"shrinkA":3,"shrinkB":2},zorder=9)

def label_marks(ax, home_points, school_points, poster):
    fig=ax.figure
    fig.canvas.draw()
    renderer=fig.canvas.get_renderer()
    point_pixels=fig.dpi/72
    points=[ax.transData.transform(p) for p in home_points+school_points]
    keep=[Bbox.from_bounds(x-5*point_pixels,y-5*point_pixels,10*point_pixels,10*point_pixels) for x,y in points]
    frame=ax.get_window_extent(renderer).padded(-8*point_pixels)
    for p,q in [((.02,.046),(.15,.12)),((.925,.83),(.988,.978))]:
        x,y=ax.transAxes.transform(p); u,v=ax.transAxes.transform(q)
        keep.append(Bbox.from_extents(x,y,u,v))
    labels=[]
    placements=[(r*math.cos(math.radians(a)),r*math.sin(math.radians(a)))
        for r in (13,17,23,30,38,49,64,79,99) for a in (42,138,-42,-138,0,180,90,-90,24,66,114,156,-24,-66,-114,-156)]
    def place(text, p, house):
        size=(8.2 if poster else 9.2) if house else (7.0 if poster else 7.4)
        opt={"fontsize":size,"fontweight":"bold" if house else "medium","color":ink if house else "#354d5b","zorder":12,
             "bbox":{"facecolor":"white","alpha":.90 if house else .86,"pad":1.15 if house else .75,"edgecolor":"none"}}
        ann=ax.annotate(text,p,xytext=(0,0),textcoords="offset points",ha="center",va="center",**opt)
        best=None
        for dx,dy in placements:
            ann.set_position((dx,dy))
            b=ann.get_window_extent(renderer).padded(2.7*point_pixels)
            if b.x0<frame.x0 or b.x1>frame.x1 or b.y0<frame.y0 or b.y1>frame.y1:
                continue
            overlap=sum((max(0,min(b.x1,q.x1)-max(b.x0,q.x0))*max(0,min(b.y1,q.y1)-max(b.y0,q.y0))) for q in keep)
            if best is None or overlap<best[0]:
                best=(overlap,dx,dy,b)
            if overlap==0:
                break
        if best is None:
            raise ValueError(f"No on-map label placement for {text}")
        area,dx,dy,b=best
        ann.set_position((dx,dy))
        if house or math.hypot(dx,dy)>23:
            ax.annotate("",p,xytext=(dx,dy),textcoords="offset points",
                arrowprops={"arrowstyle":"-","lw":.56,"color":"#6c8090","shrinkA":4,"shrinkB":4},zorder=8)
        keep.append(b)
        labels.append((text,round(area,1)))
    for r,p in zip(rendered_homes,home_points):
        price=r["map_price_wan_cny_m2"]
        featured = price and (not poster or float(price)<8 or float(price)>=14 or r["residence_id"]=="RES018")
        place(r["map_code"]+(("  "+price) if featured else ""),p,True)
    if not poster:
        for r,p in zip(rendered_schools,school_points):
            place(r["map_code"],p,False)
    return labels,keep

def text_road_labels(ax, locations, poster, keep):
    renderer=ax.figure.canvas.get_renderer()
    ppx=ax.figure.dpi/72
    frame=ax.get_window_extent(renderer).padded(-7*ppx)
    for road,(approx,angle) in road_label_settings.items():
        choices=sorted(locations[road],key=lambda p:(p[0]-approx[0])**2+(p[1]-approx[1])**2)
        for a,b in choices[::2]:
            lab=ax.annotate(road,xy(a,b),xytext=(0,3),textcoords="offset points",fontsize=8.5 if poster else 8.2,
                color="#7c776e",rotation=angle,va="bottom",ha="center",zorder=4)
            lab.set_path_effects([pe.withStroke(linewidth=2.6,foreground=land)])
            box=lab.get_window_extent(renderer).padded(2*ppx)
            if (box.x0>=frame.x0 and box.x1<=frame.x1 and box.y0>=frame.y0 and box.y1<=frame.y1
                    and not any(box.overlaps(o) for o in keep)):
                keep.append(box)
                break
            lab.remove()

def draw_panel(fig, poster, stage):
    box=[.683,.18,.282,.662] if poster else [.766,.348,.195,.528]
    ax=fig.add_axes(box)
    ax.axis("off")
    ax.add_patch(Rectangle((-.06,-.043),1.08,1.095,transform=ax.transAxes,facecolor="#f1f5f6",edgecolor="none",clip_on=False))
    ax.text(0,1.0,"Housing reference prices" if poster else "住宅项目参考价",fontsize=16 if poster else 17,weight="bold",color=ink,va="top",transform=ax.transAxes)
    ax.text(0,.925,"Fang.com  ·  CNY 10,000/m²  ·  Aug–Nov 2026" if poster else "房天下小区参考价｜万元/㎡｜2026年8–11月",
        color=muted,fontsize=9.0 if poster else 9.5,va="top",transform=ax.transAxes)
    for i,(c,t) in enumerate(zip(housing_colors,band_names)):
        xx=.015+i*.195
        ax.add_patch(Rectangle((xx,.842),.158,.032,transform=ax.transAxes,facecolor=c,edgecolor="#7d9aae",linewidth=.55))
        ax.text(xx+.078,.82,t,transform=ax.transAxes,ha="center",va="top",fontsize=8.5,color=ink)
    for yy,mark,zh,en in [(.746,"D","无可比参考价／产品不可比","Outside reference series or no comparable price"),
                              (.703,"h","其他价格指标（见附表）","Other sale-price metric")]:
        ax.plot([.022],[yy],marker=mark,ms=6.7,mfc="white",mec=ink,mew=.9,ls="none",transform=ax.transAxes)
        ax.text(.069,yy,en if poster else zh,transform=ax.transAxes,fontsize=8.5 if poster else 9.1,va="center",color=muted)
    ax.plot([0,1],[.656,.656],color="#d5e0e2",lw=.8,transform=ax.transAxes)
    ax.text(0,.624,"Education facilities" if poster else "园校类型",transform=ax.transAxes,fontsize=15 if poster else 15.5,va="top",weight="bold",color=ink)
    present = {(r["stage"],r["organizer_type"]) for r in rendered_schools}
    entries = [v for v in legend_pairs if ("primary" if v[0]=="s" else "kindergarten",v[1]) in present]
    for i,(marker,typ,zh,en) in enumerate(entries):
        yy=.535-i*.067
        ax.plot([.022],[yy],marker=marker,mfc=school_colors[typ],mec="white",mew=.7,ms=9,
            ls="none",transform=ax.transAxes)
        ax.text(.069,yy,en if poster else zh,transform=ax.transAxes,fontsize=10,va="center",color=ink)
    ax.plot([0,1],[.208,.208],color="#d5e0e2",lw=.8,transform=ax.transAxes)
    if poster:
        coverage=f"{len(rendered_homes)} housing projects  ·  16 with a reference price\n{stage['primary']}/13 primary  ·  {stage['kindergarten']}/30 kindergarten campuses"
        note="Candidate sites within the poster extent"
    else:
        coverage=f"{len(rendered_homes)} 个住宅项目｜16 个可比参考价\n{stage['primary']} 个小学校区｜{stage['kindergarten']} 个幼儿园园区"
        note="目的性样本｜园校按校区或园区计"
    ax.text(0,.159,coverage,transform=ax.transAxes,fontsize=10.1,linespacing=1.55,va="top",weight="bold",color=ink)
    ax.text(0,.018,note,transform=ax.transAxes,fontsize=8.2,va="bottom",color=muted)

def strip_name(h):
    return h["name"].replace("（整盘）","")

def poster_index(fig):
    ax=fig.add_axes([.678,.04,.292,.122])
    ax.axis("off")
    ax.text(0,1.17,"Housing index  ·  reference prices in CNY 10,000/m²",fontsize=9.0,weight="bold",color=ink,va="top",transform=ax.transAxes)
    # A compressed index of all 22 plotted projects, three columns.
    for i,h in enumerate(rendered_homes):
        col=i//8
        yy=.93-(i%8)*.124
        xx=.01+col*.335
        price=h["map_price_wan_cny_m2"] or "—"
        name=strip_name(h)
        ax.text(xx,yy,f"{h['map_code']} {name}",fontsize=6.8,transform=ax.transAxes,color=ink,va="top")
        ax.text(xx+.309,yy,price,fontsize=6.8,weight="bold",transform=ax.transAxes,color=ink,va="top",ha="right")

def full_index(fig):
    ax=fig.add_axes([.046,.062,.91,.265])
    ax.axis("off")
    ax.plot([0,1],[1.045,1.045],transform=ax.transAxes,clip_on=False,color="#d9e4e6",lw=1)
    ax.text(0,1.0,"住宅项目索引",fontsize=13,weight="bold",transform=ax.transAxes,va="top",color=ink)
    ax.text(.43,1.0,"园校索引",fontsize=13,weight="bold",transform=ax.transAxes,va="top",color=ink)
    ax.text(.136,1.0,"万元/㎡  ·  参考月",fontsize=8.4,transform=ax.transAxes,va="top",color=muted)
    for i,h in enumerate(rendered_homes):
        x=.198*(i//11); y=.85-.069*(i%11)
        code=h["map_code"]
        p=h["map_price_wan_cny_m2"]
        val=p+" · "+h["price_period"][-2:]+"月" if p else "—"
        if not p and h["map_price_status"]=="other_price_metric":
            val="其他口径"
        ax.text(x,y,f"{code}  {strip_name(h)}",transform=ax.transAxes,fontsize=9.5,va="top",color=ink)
        ax.text(x+.181,y,val,transform=ax.transAxes,fontsize=8.6,weight="bold",ha="right",va="top",color=muted)
    for i,r in enumerate(rendered_schools):
        col=i//15
        x=.43+.194*col
        y=.85-.053*(i%15)
        ax.text(x,y,r["map_code"],transform=ax.transAxes,fontsize=8.1,weight="bold",va="top",color=school_colors[r["organizer_type"]])
        ax.text(x+.025,y,r["short_name"],transform=ax.transAxes,fontsize=8.25,va="top",color=ink)

def render(name):
    global rendered_homes,rendered_schools
    poster=name=="poster"
    extent=spec["bounds_wgs84"][name]
    rendered_homes=[h for h in homes if mapped(h,name)]
    rendered_schools=sorted([r for r in campuses if mapped(r,name)],key=lambda r:(r["stage"]!="primary",r["map_code"]))
    stage=Counter(r["stage"] for r in rendered_schools)
    fig=plt.figure(figsize=(16,9) if poster else (19.2,12.2),facecolor="white")
    title="Housing prices and educational facilities in Liede" if poster else "猎德及周边住宅参考价与教育设施分布"
    sub=("Zhujiang New Town, Guangzhou  /  2026 purposive sample" if poster else
        "广州珠江新城及相邻片区｜2026 年房天下参考价与天河区小学、幼儿园候选样本")
    fig.text(.043,.944,title,color=ink,fontsize=27 if poster else 30,weight="bold",va="top")
    fig.text(.045,.88 if poster else .897,sub,color=muted,fontsize=11.8 if poster else 12.5,va="top")
    ax=fig.add_axes([.043,.069,.607,.779] if poster else [.044,.352,.690,.507])
    ax.set_facecolor(land)
    w,s,e,n=extent
    left,bottom=xy(w,s); right,top=xy(e,n)
    ax.set_xlim(left,right)
    ax.set_ylim(bottom,top)
    ax.set_aspect("equal",adjustable="box")
    for sp in ax.spines.values():
        sp.set_color("#cedcdd")
        sp.set_linewidth(.9)
    ax.set_xticks([])
    ax.set_yticks([])
    road_loc=draw_basemap(ax,extent,poster)
    context=[(113.3348,23.1214,"珠江公园",0),(113.3196,23.1124,"珠 江",0)]
    for lon,lat,txt,rot in context:
        ax.text(*xy(lon,lat),txt,fontsize=11,color="#688679" if rot==0 and txt!="珠 江" else "#7395a5",
            va="center",ha="center",zorder=3,rotation=rot)
    hp,sp=[project(h) for h in rendered_homes],[project(r) for r in rendered_schools]
    for r,p in zip(rendered_schools,sp):
        ax.scatter(*p,s=50 if poster else 60,marker="s" if r["stage"]=="primary" else "^",color=school_colors[r["organizer_type"]],
            edgecolor="white",linewidth=.85,zorder=5)
    for h,p in zip(rendered_homes,hp):
        shape,color=price_style(h)
        ax.scatter(*p,s=84 if poster else 93,marker=shape,facecolor=color,edgecolor="#163754",linewidth=1.06,zorder=6)
    draw_scale(ax,poster)
    marks,keep=label_marks(ax,hp,sp,poster)
    text_road_labels(ax,road_loc,poster,keep)
    draw_panel(fig,poster,stage)
    if poster:
        poster_index(fig)
        fig.text(.046,.037,"Sources  Fang.com · Tianhe Education Bureau · Amap / OpenStreetMap  © OpenStreetMap contributors, ODbL",
                 fontsize=7.3,color=muted)
        fig.text(.046,.018,"Symbols show mapped locations. Nearby facilities do not indicate admission eligibility.",fontsize=7.3,color=muted)
    else:
        full_index(fig)
        fig.text(.046,.036,"数据：房天下、天河区教育局、高德及 OSM 项目/园校点位。底图 © OpenStreetMap contributors (ODbL)，2026-11-12 存档。",
                 fontsize=9.0,color=muted)
        fig.text(.046,.018,"编号对应项目/校区或园区。点位与房价均按样本显示；接送门、招生资格及家庭收入未由地图判定。",
                 fontsize=9.0,color=muted)
    fig.canvas.draw()
    renderer=fig.canvas.get_renderer()
    for item in fig.findobj(matplotlib.text.Text):
        if not item.get_visible() or not item.get_text().strip():
            continue
        box=item.get_window_extent(renderer)
        if box.x0<0 or box.y0<0 or box.x1>fig.bbox.x1 or box.y1>fig.bbox.y1:
            raise ValueError(f"Outside figure: {item.get_text()} {box}")
    dest=root/"maps"/("housing-education-poster" if poster else "housing-education-full")
    dest.parent.mkdir(exist_ok=True)
    for ext in ("png","pdf","svg"):
        fig.savefig(dest.with_suffix("."+ext),dpi=300)
    plt.close(fig)
    print(name,len(rendered_homes),dict(stage),"label overlaps",[(t,a) for t,a in marks if a>0])

for mode in ("full","poster"):
    render(mode)

