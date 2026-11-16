// A3 地图（定稿）：500 米园校数底色 + 两组房价编号圆 + 两处证据标注；以及“房价 × 园校数”对照表。
// 依赖 mapdata.js、map.js。支持中英文：opts.lang = "zh" | "en"。
(function () {
  const SURF3 = { r: 500, breaks: [4, 7], colors: ["#00000000", "#dcefe9", "#a8d6c9"], edge: "#ffffffcc", edgeW: 2 };
  const GC = ["#e9b04a", "#b23f26"];
  const WEST = ["R02", "R04", "R06", "R10", "R09", "R15", "R03", "R07", "R11"];
  const ROADPOS = { huangpu: [-560, -815, 3.5], liede: [-84, -330, 90], linjiang: [1080, 845, 7], huacheng: [760, 214, 5.5] };

  const T = {
    zh: {
      school: { P01: "猎德实验小学部", P02: "南国学校小学部", P03: "海明学校", P06: "兴国学校", P07: "冼村小学", P08: "第一实验小学", P09: "体育东路小学" },
      road: { huangpu: "黄埔大道", liede: "猎德大道", linjiang: "临江大道", huacheng: "花城大道" },
      river: "珠　江", park: "珠江公园", unit: "米", glyph: "小",
      west: ["西侧住宅群", "房价 7.6–14.0 万，500 米内园校 5–9 个"],
      pair: ["同一地段，房价差三倍", "① 颐德公馆 17.4 万 · ⑯ 誉城苑 5.5 万", "同属猎德实验小学部地段（部分门牌）", "500 米内园校 6 个 vs 7 个"],
      th: ["楼盘", "房价（万元/㎡）", "500 米内园校数"],
      med: ["10 万元/㎡ 分组线", "园校数中位数：上组 <b>6</b> · 下组 <b>7</b>"],
      off: "图外",
      lg: { surf: "底色", surfT: "500 米内园校数", est: "楼盘", hi: "≥10 万/㎡", lo: "低于 10 万", na: "无可比价", priL: "小学", kgL: "幼儿园", pub: "公办", prv: "民办", scaleM: 500 },
    },
    en: {
      school: { P01: "Liede Exp. Primary", P02: "Nanguo Sch. Primary", P03: "Haiming School", P06: "Xingguo School", P07: "Xiancun Primary", P08: "No.1 Exp. Primary", P09: "Tiyu Donglu Primary" },
      road: { huangpu: "HUANGPU AVE", liede: "LIEDE AVE", linjiang: "LINJIANG AVE", huacheng: "HUACHENG AVE" },
      river: "PEARL RIVER", park: "Zhujiang Park", unit: "m", glyph: "P",
      west: ["Western cluster", "CNY 76k–140k/m²; 5–9 schools within 500 m"],
      pair: ["Same catchment, 3× price gap", "① Yide 17.4 vs ⑯ Yucheng 5.5 (10k/m²)", "Schools within 500 m: 6 vs 7"],
      th: ["Estate", "CNY 10k/m²", "Schools ≤500 m"],
      med: ["CNY 100k/m² split", "Median schools: upper <b>6</b> · lower <b>7</b>"],
      off: "off map",
      lg: { surf: "Shading", surfT: "schools ≤500 m", est: "Estates", hi: "≥100k/m²", lo: "<100k/m²", na: "no price", priL: "Primary", kgL: "Kindergarten", pub: "public", prv: "private", scaleM: 250 },
    },
  };

  const ranked = () => window.MAPDATA.houses.filter((h) => h.price != null).sort((a, b) => b.price - a.price);

  window.a3 = {
    GC, SURF3, ranked, T,
    map(o) {
      const lang = o.lang || "zh", t = T[lang];
      const M = window.MAPDATA, L = window.liedeMap, k = o.k || 1, gc = o.gc || GC;
      M.schools.forEach((c) => {
        c._zh = c._zh || c.name;
        c.name = T[lang].school[c.id] || c._zh;
      });
      Object.entries(ROADPOS).forEach(([n, [x, y, a]]) => (M.labels["@" + n] = { x, y, a, text: t.road[n] }));
      const fs = (n) => n * k * (o.annoK || 1);
      const halo = (s, x, y, q = {}) => `<text x="${x}" y="${y}" font-size="${q.size || fs(12.5)}" font-weight="${q.w || 400}" fill="${q.fill || "#1e2730"}" text-anchor="${q.a || "start"}" stroke="#fff" stroke-width="4" paint-order="stroke" stroke-linejoin="round">${s}</text>`;
      const under = ({ px, py, H }) => {
        let g = "";
        const xs = WEST.map((id) => px(H[id].x)), ys = WEST.map((id) => py(H[id].y)), pad = 18 * k;
        const x0 = Math.min(...xs) - pad, x1 = Math.max(...xs) + pad, y0 = Math.min(...ys) - pad, y1 = Math.max(...ys) + pad;
        g += `<rect x="${x0}" y="${y0}" width="${x1 - x0}" height="${y1 - y0}" rx="${20 * k}" fill="rgba(255,255,255,.2)" stroke="#1e2730" stroke-width="1.3" stroke-dasharray="5 4" opacity=".7"/>`;
        g += halo(t.west[0], x0 + 2, y0 - fs(22), { w: 700, size: fs(13.5) }) + halo(t.west[1], x0 + 2, y0 - fs(7), { size: fs(12) });
        const a = H.R14, b = H.R16;
        g += `<line x1="${px(a.x)}" y1="${py(a.y)}" x2="${px(b.x)}" y2="${py(b.y)}" stroke="#1e2730" stroke-width="1.6" stroke-dasharray="4 3"/>`;
        const tx = px(a.x) + fs(40), ty = py(a.y) - fs(66);
        g += `<polyline points="${px(a.x) + 8},${py(a.y) - 8} ${tx - 4},${ty + fs(34)} ${tx - 4},${ty - fs(12)}" fill="none" stroke="#1e2730" stroke-width="1.2"/>`;
        g += halo(t.pair[0], tx, ty, { w: 700, size: fs(13.5), fill: "#8c2a1c" }) + t.pair.slice(1).map((s, i) => halo(s, tx, ty + fs(16 * (i + 1)), { size: fs(12) })).join("");
        return g;
      };
      const rankOf = Object.fromEntries(ranked().map((h, i) => [h.id, i + 1]));
      const en = lang === "en";
      return L({
        id: o.id || "a3", w: o.w, h: o.h, view: o.view || [-1060, -1330, 1310, 1210], k, theme: "mute",
        surface: SURF3, noMinor: true, schoolsOnTop: true, roadOpacity: 0.65, naR: 6, scale: o.noScale ? 0 : 500, unit: t.unit, priGlyph: t.glyph,
        kgPub: "#0f5f56", kgPri: "#0f5f56", kgR: 5.4, priA: 18, roadLs: en ? "0.08em" : "0.12em", waterLs: en ? "0.3em" : "0.5em", areaLs: en ? "0.04em" : "0.15em",
        roadLabels: (o.roads || ["huangpu", "liede", "linjiang"]).map((n) => ["@" + n]),
        areaLabels: [[t.river, 300, 1080, "water"], [t.park, 600, -260, "park"]],
        schoolLabels: [["P07", 0, -15, "middle"], ["P01", -14, 20, "end"], ["P02", -14, 5, "end"], ["P06", -14, 5, "end"], ["P08", 14, 5], ["P03", 14, 5], ["P09", 14, 5]].filter(([id]) => !(o.hideLabels || []).includes(id)),
        houses: "rank", rankOf, rankR: 10, groupColors: gc, under, scaleAt: o.scaleAt, northAt: o.northAt,
      });
    },
    // 对照表：每个楼盘一行，左侧房价条，右侧 500 米内园校刻度
    table(o = {}) {
      const lang = o.lang || "zh", t = T[lang], gc = o.gc || GC, rk = ranked();
      const pips = (n) => `<span class="a3-pips">${Array.from({ length: 9 }, (_, i) => `<u class="${i < n ? "f" : ""}"></u>`).join("")}<span>${n}</span></span>`;
      let rows = `<div class="a3-r a3-h"><span></span><span>${t.th[0]}</span><span style="grid-column:span 2">${t.th[1]}</span><span>${t.th[2]}</span></div>`;
      rk.forEach((h, i) => {
        if (i > 0 && rk[i - 1].price >= 10 && h.price < 10) rows += `<div class="a3-med"><span>${t.med[0]}</span><span>${t.med[1]}</span></div>`;
        const hi = h.price >= 10, nm = lang === "en" ? h.nameEn : h.name;
        rows += `<div class="a3-r"><b style="background:${gc[hi ? 1 : 0]};color:${hi ? "#fff" : "#3a2a10"}">${i + 1}</b><span class="nm">${nm}${h.id === "R22" ? `<small> ${t.off}</small>` : ""}</span><i style="width:${(h.price / 17.4) * 100}%;background:${gc[hi ? 1 : 0]}"></i><em>${h.price.toFixed(1)}</em>${pips(h.n500)}</div>`;
      });
      return `<div class="a3-tbl">${rows}</div>`;
    },
    legend(o = {}) {
      const lang = o.lang || "zh", t = T[lang].lg, gc = o.gc || GC, g = T[lang].glyph;
      const kg = (pub) => `<svg width="12" height="12"><circle cx="6" cy="6" r="${pub ? 5 : 4.2}" fill="${pub ? "#0f5f56" : "#fff"}" stroke="#0f5f56" stroke-width="${pub ? 0 : 2}"/></svg>`;
      const pri = (pub) => `<svg width="15" height="15"><rect x="1" y="1" width="13" height="13" rx="2.5" fill="${pub ? "#1d3557" : "#fff"}" stroke="#1d3557" stroke-width="${pub ? 0 : 2}"/><text x="7.5" y="11.3" text-anchor="middle" font-size="9.5" font-weight="700" fill="${pub ? "#fff" : "#1d3557"}" font-family="NSans">${g}</text></svg>`;
      const sw = SURF3.colors.map((c, i) => `<span class="a3-sw"><i style="background:${i ? c : "#f4f2ed"};${i ? "" : "box-shadow:inset 0 0 0 1px #ddd8ce"}"></i>${["0–3", "4–6", "≥7"][i]}</span>`).join("");
      return `<div class="a3-lg">
        <div><b>${t.surf}</b> ${t.surfT} ${sw}</div>
        <div><b>${t.est}</b> <span class="a3-dot" style="background:${gc[1]}"></span>${t.hi} <span class="a3-dot" style="background:${gc[0]}"></span>${t.lo} <svg width="13" height="13"><path d="M6.5,1L12,6.5L6.5,12L1,6.5Z" fill="#fff" stroke="#a6abb0" stroke-width="1.8"/></svg>${t.na}</div>
        <div><b>${t.priL}</b> ${pri(true)}${t.pub} ${pri(false)}${t.prv}<b style="margin-left:12px">${t.kgL}</b> ${kg(true)}${t.pub} ${kg(false)}${t.prv}</div>
        ${o.pxPerM ? `<div class="a3-sc"><span>0</span><i style="width:${o.pxPerM * t.scaleM}px"></i><span>${t.scaleM} ${T[lang].unit}</span></div>` : ""}
      </div>`;
    },
  };

  const css = `
  .a3-tbl { display: flex; flex-direction: column; font-size: var(--a3-fs, 13px); font-variant-numeric: tabular-nums; }
  .a3-r { display: grid; grid-template-columns: 18px var(--a3-name, 84px) var(--a3-bar, 70px) 32px 1fr; align-items: center; gap: 6px; height: var(--a3-row, 23px); }
  .a3-r .nm { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .a3-h { font-size: 11px; color: var(--muted, #6b7178); height: 20px; border-bottom: 1px solid var(--ink, #1d1915); margin-bottom: 4px; letter-spacing: .02em; }
  .a3-r b { width: 18px; height: 18px; border-radius: 50%; display: grid; place-items: center; font: 500 10px "Mono"; }
  .a3-r small { color: #8a8f95; font-size: 10px; }
  .a3-r i { height: 8px; display: block; border-radius: 0 4px 4px 0; }
  .a3-r em { font: 500 12.5px "Mono"; font-style: normal; text-align: right; }
  .a3-pips { display: flex; gap: 2px; align-items: center; }
  .a3-pips u { width: 6px; height: 11px; border-radius: 1px; background: #e4ded3; display: block; }
  .a3-pips u.f { background: #2f7f72; }
  .a3-pips span { font: 500 12px "Mono"; margin-left: 6px; color: #2f7f72; }
  .a3-med { display: grid; grid-template-columns: 1fr auto; align-items: center; font-size: 11px; color: #8b2a1c; height: 22px; border-top: 1px solid #b23f26; border-bottom: 1px solid #b23f26; margin: 4px 0; padding: 0 2px; background: rgba(178,63,38,.05); }
  .a3-med b { color: #2f7f72; font-family: "Mono"; }
  .a3-lg { display: flex; flex-wrap: wrap; gap: 3px 16px; font-size: 11px; align-items: center; }
  .a3-lg > div { display: flex; align-items: center; gap: 5px; white-space: nowrap; }
  .a3-lg b { font-weight: 700; margin-right: 2px; }
  .a3-lg svg { display: block; }
  .a3-sw { display: inline-flex; align-items: center; gap: 3px; font: 400 10.5px "Mono"; }
  .a3-sw i { width: 20px; height: 10px; display: block; }
  .a3-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
  .a3-sc { margin-left: auto; font: 400 10px "Mono"; color: #3a332c; display: flex !important; align-items: center; gap: 4px; }
  .a3-sc i { height: 5px; display: block; background: linear-gradient(90deg, #1e2730 50%, #fff 50%); box-shadow: 0 0 0 1px #1e2730; }`;
  const st = document.createElement("style");
  st.textContent = css;
  document.head.appendChild(st);
})();
