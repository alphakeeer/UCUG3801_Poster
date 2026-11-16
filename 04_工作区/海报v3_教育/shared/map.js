// 矢量地图：用 window.MAPDATA（tools/build_map_data.py 生成）绘制 SVG。
// 坐标单位为米（x 向东、y 向南），view 指定裁切范围，其余全部可按方案换肤。
(function () {
  const D = () => window.MAPDATA;

  // 房价分档（万元/㎡），与交接地图 map_scope.json 的分档一致
  const BANDS = [
    { max: 8, label: "<8" },
    { max: 10, label: "8–10" },
    { max: 12, label: "10–12" },
    { max: 14, label: "12–14" },
    { max: 99, label: "≥14" },
  ];
  const WARM = ["#f7dc93", "#f1b061", "#e2803f", "#c4502b", "#8c2a1c"];
  const band = (p) => BANDS.findIndex((b) => p < b.max);

  const THEMES = {
    light: {
      bg: "#f3f1ec", land: "#f3f1ec", water: "#bcd9e6", park: "#d8e8cf", minor: "#ffffff", tertiary: "#ffffff",
      secondary: "#ffffff", major: "#fbe7b8", casing: "#d9d4ca", label: "#7c7a74", water_label: "#4e88a3",
      bound: "#9a8f80", text: "#1e2730", halo: "#ffffff",
      pri: "#1d3557", kgPub: "#13897a", kgPri: "#13897a", price: WARM, noPrice: "#9aa0a6",
    },
    dark: {
      bg: "#13202e", land: "#17293a", water: "#0d1823", park: "#1d3a35", minor: "#22374b", tertiary: "#2a4259",
      secondary: "#33506b", major: "#46698a", casing: null, label: "#7f97ad", water_label: "#4f7391",
      bound: "#6f8aa3", text: "#eef3f7", halo: "#13202e",
      pri: "#ffffff", kgPub: "#5fd3bf", kgPri: "#5fd3bf", price: WARM, noPrice: "#6c7d8c",
    },
    mute: {
      bg: "#f5f4f0", land: "#f5f4f0", water: "#d3e4ec", park: "#e3ecdc", minor: "#ffffff", tertiary: "#ffffff",
      secondary: "#ffffff", major: "#ffffff", casing: "#e2ded6", label: "#a19d95", water_label: "#7aa3b6",
      bound: "#b9b1a5", text: "#1e2730", halo: "#ffffff",
      pri: "#1d3557", kgPub: "#13897a", kgPri: "#13897a", price: WARM, noPrice: "#a6abb0",
    },
  };

  const hex = (c) => { const m = c.match(/^#(..)(..)(..)(..)?$/); return [1, 2, 3].map((i) => parseInt(m[i], 16)).concat(m[4] ? parseInt(m[4], 16) : 255); };

  // 栅格化“半径 r 米内园校数”，按 breaks 分档上色，档位交界画细线。结果为 dataURL。
  function surfaceURL(o, sc, vx0, y0, M) {
    const S = o.surface, f = S.res || 2, W = Math.round(o.w * f), Hh = Math.round(o.h * f);
    const pts = M.schools.filter(S.filter || (() => true)), r2 = S.r * S.r;
    const xs = Float64Array.from(pts, (p) => p.x), ys = Float64Array.from(pts, (p) => p.y);
    const bandOf = new Uint8Array(W * Hh);
    for (let j = 0; j < Hh; j++) {
      const my = y0 + (j + 0.5) / f / sc;
      for (let i = 0; i < W; i++) {
        const mx = vx0 + (i + 0.5) / f / sc;
        let n = 0;
        for (let q = 0; q < xs.length; q++) { const dx = xs[q] - mx, dy = ys[q] - my; if (dx * dx + dy * dy <= r2) n++; }
        let b = 0; while (b < S.breaks.length && n >= S.breaks[b]) b++;
        bandOf[j * W + i] = b;
      }
    }
    const cols = S.colors.map(hex), edge = S.edge ? hex(S.edge) : null;
    const cv = document.createElement("canvas"); cv.width = W; cv.height = Hh;
    const ctx = cv.getContext("2d"), img = ctx.createImageData(W, Hh), d = img.data;
    const ew = S.edgeW || 2;
    for (let j = 0; j < Hh; j++) for (let i = 0; i < W; i++) {
      const k = j * W + i, b = bandOf[k];
      let c = cols[b];
      if (edge) {
        for (let e = 1; e <= ew; e++) {
          const rb = i + e < W ? bandOf[k + e] : b, bb = j + e < Hh ? bandOf[k + e * W] : b;
          if (rb > b || bb > b) { c = edge; break; }
        }
      }
      d.set(c, k * 4);
    }
    ctx.putImageData(img, 0, 0);
    return cv.toDataURL("image/png");
  }

  const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");

  /**
   * o.w,o.h      像素尺寸
   * o.view       [x0,y0,x1,y1] 米；按宽度等比，超出部分在高度方向补齐
   * o.theme      light | dark | mute 或对象
   * o.houses     "price" | "dot" | false
   * o.primary    true/false；o.kg true/false
   * o.labelPrice 在房价圆点内写数值
   * o.schoolLabels  [P01,...] 需要标名字的小学
   * o.roadLabels    [[名称, dx, dy], ...]
   * o.areaLabels    [[文字, x, y, 类型]]  类型 water|park|area
   * o.rings      [{house:"R14", r:500, color}]
   * o.routes     true：画 D1–D3 到地段学校与冼村小学的直线
   * o.callouts   {R14:[dx,dy,"文字"]} 指引线标注（像素偏移）
   * o.scale      比例尺长度（米）
   * o.k          图上符号整体缩放
   */
  window.liedeMap = function (o) {
    const M = D();
    const T = typeof o.theme === "object" ? o.theme : THEMES[o.theme || "light"];
    const [vx0, vy0, vx1, vy1] = o.view;
    const sc = o.w / (vx1 - vx0);
    const vh = o.h / sc;
    const cy = (vy0 + vy1) / 2;
    const y0 = cy - vh / 2;
    const k = o.k || 1;
    const px = (x) => (x - vx0) * sc, py = (y) => (y - y0) * sc;
    const sw = (p) => p / sc; // 像素 → 米（描边宽度用）
    const H = Object.fromEntries(M.houses.map((h) => [h.id, h]));
    const S = Object.fromEntries(M.schools.map((s) => [s.id, s]));
    const fs = (n) => n * k;

    let s = `<svg class="lmap" viewBox="0 0 ${o.w} ${o.h}" width="${o.w}" height="${o.h}" font-family="NSans">`;
    s += `<defs><clipPath id="lmclip${o.id || ""}"><rect width="${o.w}" height="${o.h}"/></clipPath></defs>`;
    s += `<rect width="${o.w}" height="${o.h}" fill="${T.bg}"/>`;
    // 底图：在米坐标系里画，再整体变换
    s += `<g clip-path="url(#lmclip${o.id || ""})"><g transform="scale(${sc}) translate(${-vx0},${-y0})" fill="none" stroke-linecap="round" stroke-linejoin="round">`;
    s += `<g fill="${T.park}" stroke="none">${M.parks.map((d) => `<path d="${d}"/>`).join("")}</g>`;
    if (o.surface) s += `<image href="${surfaceURL(o, sc, vx0, y0, M)}" x="${vx0}" y="${y0}" width="${o.w / sc}" height="${o.h / sc}" preserveAspectRatio="none" opacity="${o.surface.opacity ?? 1}"/>`;
    s += `<g fill="${T.water}" stroke="none" fill-rule="evenodd">${M.water.map((d) => `<path d="${d}"/>`).join("")}</g>`;
    s += `<g opacity="${o.roadOpacity ?? 1}">`;
    const road = (cls, w, col) => `<g stroke="${col}" stroke-width="${sw(w)}">${M.roads[cls].map((d) => `<path d="${d}"/>`).join("")}</g>`;
    const rw = o.roadW || { minor: 1.2, tertiary: 2.2, secondary: 3.2, major: 5 };
    if (T.casing) {
      s += road("secondary", rw.secondary + 1.4, T.casing) + road("major", rw.major + 1.6, T.casing);
    }
    s += (o.noMinor ? "" : road("minor", rw.minor, T.minor)) + road("tertiary", rw.tertiary, T.tertiary) + road("secondary", rw.secondary, T.secondary) + road("major", rw.major, T.major);
    s += `</g>`;
    if (o.bounds) s += `<g stroke="${T.bound}" stroke-width="${sw(1.4)}" stroke-dasharray="${sw(6)} ${sw(4)}">${M.bounds.map((b) => `<path d="${b.d}"/>`).join("")}</g>`;
    s += `</g>`;

    // 地名与路名
    const halo = (t, x, y, opt = {}) =>
      `<text x="${x}" y="${y}" ${opt.anchor ? `text-anchor="${opt.anchor}"` : 'text-anchor="middle"'} font-size="${opt.size || fs(12)}" font-weight="${opt.weight || 400}" ${opt.rot ? `transform="rotate(${opt.rot} ${x} ${y})"` : ""} ${opt.ls ? `letter-spacing="${opt.ls}"` : ""} fill="${opt.fill || T.text}" stroke="${opt.halo === false ? "none" : T.halo}" stroke-width="${opt.hw || 3}" paint-order="stroke" stroke-linejoin="round">${esc(t)}</text>`;
    (o.roadLabels || []).forEach(([nm, dx = 0, dy = 0, rot]) => {
      const L = M.labels[nm];
      if (!L) return;
      s += halo(L.text || nm, px(L.x) + dx, py(L.y) + dy + 4, { size: fs(11.5), fill: T.label, rot: rot ?? L.a, ls: o.roadLs || "0.12em", hw: 3 });
    });
    (o.areaLabels || []).forEach(([t, x, y, kind]) => {
      const col = kind === "water" ? T.water_label : kind === "park" ? "#5d8a55" : T.label;
      s += halo(t, px(x), py(y), { size: fs(kind === "water" ? 16 : 12.5), fill: col, ls: kind === "water" ? (o.waterLs || "0.5em") : (o.areaLs || "0.15em"), weight: kind === "area" ? 700 : 400, halo: kind !== "water" });
    });

    // 缓冲圈
    (o.rings || []).forEach((r) => {
      const h = H[r.house];
      s += `<circle cx="${px(h.x)}" cy="${py(h.y)}" r="${r.r * sc}" fill="${r.fill || "none"}" stroke="${r.color}" stroke-width="${r.sw || 2}" stroke-dasharray="${r.dash || "7 5"}"/>`;
    });

    // 路线（直线示意，非实际步行路径）
    if (o.routes) {
      const R = M.routes;
      const pc = S[R.points];
      R.origins.forEach((og, i) => {
        const h = H[og.house], loc = S[R.local[og.id]];
        s += `<line x1="${px(h.x)}" y1="${py(h.y)}" x2="${px(pc.x)}" y2="${py(pc.y)}" stroke="${o.routeB || "#8a5cc2"}" stroke-width="${2.6 * k}" stroke-dasharray="${8 * k} ${5 * k}" opacity=".95"/>`;
        s += `<line x1="${px(h.x)}" y1="${py(h.y)}" x2="${px(loc.x)}" y2="${py(loc.y)}" stroke="${o.routeA || "#13897a"}" stroke-width="${4 * k}" stroke-linecap="round"/>`;
      });
    }

    // 自定义标注层（画在学校与住宅之下）
    if (o.under) s += o.under({ px, py, H, S, sc, k });
    let sch = "";
    // 幼儿园
    if (o.kg !== false) {
      M.schools.filter((x) => x.kind === "kg").forEach((c) => {
        const r = (o.kgR || 5.2) * k, X = px(c.x), Y = py(c.y);
        if (X < -10 || X > o.w + 10 || Y < -10 || Y > o.h + 10) return;
        const pub = o.kgPub || T.kgPub, pri = o.kgPri || T.kgPri;
        sch += c.org === "public"
          ? `<circle cx="${X}" cy="${Y}" r="${r}" fill="${pub}" stroke="${T.halo}" stroke-width="1.6"/>`
          : `<circle cx="${X}" cy="${Y}" r="${r - 0.6}" fill="${T.halo}" stroke="${pri}" stroke-width="2.4"/>`;
      });
    }
    // 小学
    if (o.primary !== false) {
      M.schools.filter((x) => x.kind === "primary").forEach((c) => {
        const a = (o.priA || 15) * k, X = px(c.x), Y = py(c.y);
        if (X < -20 || X > o.w + 20 || Y < -20 || Y > o.h + 20) return;
        const pub = c.org === "public";
        sch += `<rect x="${X - a / 2}" y="${Y - a / 2}" width="${a}" height="${a}" rx="${2.5 * k}" fill="${pub ? T.pri : T.halo}" stroke="${pub ? T.halo : T.pri}" stroke-width="${pub ? 1.6 : 2.2}"/>`;
        sch += `<text x="${X}" y="${Y + a * 0.28}" text-anchor="middle" font-size="${a * 0.72}" font-weight="700" fill="${pub ? T.halo : T.pri}">${o.priGlyph || "小"}</text>`;
      });
    }
    if (!o.schoolsOnTop) s += sch;

    // 住宅
    if (o.houses) {
      const order = o.houses === "size" ? [...M.houses].sort((a, b) => (b.price ?? 0) - (a.price ?? 0))
        : o.houses === "spike" || o.houses === "lolli" ? [...M.houses].sort((a, b) => a.y - b.y)
        : [...M.houses].sort((a, b) => (a.price ?? 0) - (b.price ?? 0));
      order.forEach((h) => {
        const X = px(h.x), Y = py(h.y);
        if (X < -20 || X > o.w + 20 || Y < -20 || Y > o.h + 20) return;
        if (o.houses === "dot") {
          s += `<circle cx="${X}" cy="${Y}" r="${4.5 * k}" fill="${T.noPrice}" stroke="${T.halo}" stroke-width="1.2"/>`;
          return;
        }
        if (h.price == null) {
          const r = (o.naR || 8.5) * k;
          s += `<path d="M${X},${Y - r}L${X + r},${Y}L${X},${Y + r}L${X - r},${Y}Z" fill="${T.halo}" stroke="${T.noPrice}" stroke-width="2.2"/>`;
          return;
        }
        const b = band(h.price);
        if (o.houses === "lolli") {
          const ht = h.price * (o.lolliK || 5) * k, hr = (o.headR || 6.5) * k, hy = Y - ht;
          s += `<line x1="${X}" y1="${Y}" x2="${X}" y2="${hy}" stroke="${o.stem || "#2c3339"}" stroke-width="${1.6 * k}" opacity=".85"/>`;
          s += `<circle cx="${X}" cy="${Y}" r="${2.6 * k}" fill="${o.stem || "#2c3339"}"/>`;
          s += `<circle cx="${X}" cy="${hy}" r="${hr}" fill="${T.price[b]}" stroke="${T.halo}" stroke-width="1.6"/>`;
          if (o.labelPrice) s += halo(h.price.toFixed(1), X + hr + 3, hy + 4, { size: fs(11.5), weight: 700, fill: "#2c3339", anchor: "start", hw: 3 });
          return;
        }
        if (o.houses === "rank") {
          const r = (o.rankR || 10) * k, n = o.rankOf[h.id];
          const G = o.groupColors, hi = h.price >= 10;
          const fill = G ? G[hi ? 1 : 0] : T.price[b], ink = G ? (hi ? "#fff" : "#3a2a10") : b >= 2 ? "#fff" : "#3a2a10";
          s += `<circle cx="${X}" cy="${Y}" r="${r}" fill="${fill}" stroke="${T.halo}" stroke-width="2"/>`;
          s += `<text x="${X}" y="${Y + 4 * k}" text-anchor="middle" font-family="Mono" font-size="${fs(11.5)}" font-weight="500" fill="${ink}">${n}</text>`;
          return;
        }
        if (o.houses === "spike") {
          const bw = (o.spikeW || 13) * k, ht = h.price * (o.spikeK || 8) * k;
          s += `<ellipse cx="${X}" cy="${Y}" rx="${bw * 0.62}" ry="${bw * 0.26}" fill="rgba(0,0,0,.28)"/>`;
          s += `<path d="M${X - bw / 2},${Y}L${X},${Y - ht}L${X + bw / 2},${Y}Z" fill="${T.price[b]}" stroke="${T.halo}" stroke-width="1.1" stroke-linejoin="round"/>`;
          s += `<path d="M${X},${Y - ht}L${X + bw / 2},${Y}L${X},${Y}Z" fill="rgba(0,0,0,.16)"/>`;
          if (o.labelPrice) s += halo(h.price.toFixed(1), X, Y - ht - 5, { size: fs(11.5), weight: 700, fill: b >= 3 ? T.price[4] : "#7a4a14", hw: 3 });
          return;
        }
        const r = o.houses === "size" ? ((o.sizeMin || 11) + (h.price - 5) * (o.sizeK || 0.9)) * k : (o.labelPrice ? 15.5 : 9) * k;
        s += `<circle cx="${X}" cy="${Y}" r="${r}" fill="${T.price[b]}" stroke="${T.halo}" stroke-width="2" />`;
        if (o.labelPrice)
          s += `<text x="${X}" y="${Y + Math.min(4 * k, r * 0.34)}" text-anchor="middle" font-family="Mono" font-size="${Math.min(fs(11.5), r * 0.95)}" font-weight="500" fill="${b >= 2 ? "#fff" : "#3a2a10"}" letter-spacing="-0.04em">${h.price.toFixed(1)}</text>`;
      });
    }

    if (o.schoolsOnTop) s += sch;

    if (o.over) s += o.over({ px, py, H, S, sc, k });
    // 小学名称
    (o.schoolLabels || []).forEach(([id, dx = 12, dy = 4, anchor = "start"]) => {
      const c = S[id];
      s += halo(c.name, px(c.x) + dx * k, py(c.y) + dy * k, { size: fs(12), weight: 700, fill: T.pri === "#ffffff" ? T.text : T.pri, anchor });
    });

    // 指引线标注
    Object.entries(o.callouts || {}).forEach(([id, [dx, dy, text, color, anchor]]) => {
      const p = H[id] || S[id];
      const X = px(p.x), Y = py(p.y), tx = X + dx * k, ty = Y + dy * k;
      const an = anchor || (dx < 0 ? "end" : "start");
      s += `<line x1="${X}" y1="${Y}" x2="${tx}" y2="${ty}" stroke="${color || T.text}" stroke-width="1.4"/>`;
      String(text).split("\n").forEach((ln, i) => {
        s += halo(ln, tx + (an === "end" ? -4 : an === "middle" ? 0 : 4), ty + 5 + i * fs(15) - (dy < 0 ? (String(text).split("\n").length - 1) * fs(15) : 0), { size: fs(i ? 11.5 : 13), weight: i ? 400 : 700, fill: color || T.text, anchor: an, hw: 4 });
      });
    });

    // 编号徽标（D1–D3）
    (o.badges || []).forEach(([id, label, dx, dy, color]) => {
      const h = H[id];
      const X = px(h.x) + dx * k, Y = py(h.y) + dy * k, r = 12 * k;
      s += `<circle cx="${X}" cy="${Y}" r="${r}" fill="${color}" stroke="${T.halo}" stroke-width="2.2"/>`;
      s += `<text x="${X}" y="${Y + 4.6 * k}" text-anchor="middle" font-size="${fs(13)}" font-weight="700" fill="#fff">${label}</text>`;
    });

    // 比例尺 + 指北
    if (o.scale) {
      const L = o.scale * sc, x = o.scaleAt ? o.scaleAt[0] : 18, y = o.scaleAt ? o.scaleAt[1] : o.h - 20;
      s += `<g font-size="${fs(11)}" fill="${T.text}"><rect x="${x}" y="${y}" width="${L}" height="5" fill="${T.text}"/><rect x="${x + L / 2}" y="${y}" width="${L / 2}" height="5" fill="${T.halo}" stroke="${T.text}" stroke-width="1"/>`;
      s += halo("0", x, y - 5, { size: fs(11) }) + halo(`${o.scale} ${o.unit || "米"}`, x + L, y - 5, { size: fs(11) }) + `</g>`;
      const nx = o.northAt ? o.northAt[0] : x + L + 34, ny = o.northAt ? o.northAt[1] : y - 6;
      s += `<g transform="translate(${nx},${ny})"><path d="M0,-16L6,2L0,-2L-6,2Z" fill="${T.text}"/>${halo("N", 0, 16, { size: fs(11), weight: 700 })}</g>`;
    }
    if (o.attribution !== false)
      s += `<text x="${o.w - 8}" y="${o.h - 7}" text-anchor="end" font-size="9.5" fill="${T.label}" opacity=".9">© OpenStreetMap contributors</text>`;
    s += `</g></svg>`;
    return s;
  };

  window.liedeMap.BANDS = BANDS;
  window.liedeMap.THEMES = THEMES;
  window.liedeMap.band = band;
  // 有可比参考价的住宅，按价格从高到低
  window.liedeMap.ranked = () => D().houses.filter((h) => h.price != null).sort((a, b) => b.price - a.price);
  window.liedeMap.counts = () => {
    const sc = D().schools;
    return {
      primary: sc.filter((s) => s.kind === "primary").length,
      primaryPub: sc.filter((s) => s.kind === "primary" && s.org === "public").length,
      kg: sc.filter((s) => s.kind === "kg").length,
      kgPub: sc.filter((s) => s.kind === "kg" && s.org === "public").length,
    };
  };
})();
