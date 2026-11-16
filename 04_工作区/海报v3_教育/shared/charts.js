// 共享图表：生成内联 SVG，颜色全部取自各方案的 CSS 变量，因此同一图表可换肤。
// --ch-low / --ch-high：发现一两组；--ch-a / --ch-b：地段学校 / 积分志愿例；
// --ch-ink 文字，--ch-muted 次要文字，--ch-grid 网格线。
(function () {
  const esc = (s) => String(s);

  // 发现一：三个半径 × 两组价格的中位数横条，空心刻度为 9 月子样本。
  window.priceChart = function (o) {
    const C = window.C.f1;
    const W = o.width, rowH = o.rowH || 58, top = o.top || 34, left = o.left || 70, right = o.right || 44;
    const fs = o.fs || 15;
    const H = top + rowH * C.rows.length + 30;
    const max = 12, x = (v) => left + ((W - left - right) * v) / max;
    let s = `<svg class="chart price-chart" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" font-size="${fs}">`;
    // legend：按估算文字宽度依次排开
    const tw = (t) => [...t].reduce((w, ch) => w + (ch.charCodeAt(0) > 255 ? 1 : 0.56) * (fs - 1), 0);
    const t1 = `低于 10 万元/㎡（n=${C.nLow}）`, t2 = `≥10 万元/㎡（n=${C.nHigh}）`;
    const x2 = left + 20 + tw(t1) + 16, x3 = x2 + 20 + tw(t2) + 16;
    s += `<g class="lg" font-size="${fs - 1}">
      <rect x="${left}" y="4" width="14" height="14" rx="2" style="fill:var(--ch-low)"/>
      <text x="${left + 20}" y="16" style="fill:var(--ch-ink)">${t1}</text>
      <rect x="${x2}" y="4" width="14" height="14" rx="2" style="fill:var(--ch-high)"/>
      <text x="${x2 + 20}" y="16" style="fill:var(--ch-ink)">${t2}</text>
      <line x1="${x3}" x2="${x3}" y1="3" y2="19" style="stroke:var(--ch-ink)" stroke-width="2.5"/>
      <text x="${x3 + 7}" y="16" style="fill:var(--ch-muted)">仅 9 月</text>
    </g>`;
    // grid
    for (let v = 0; v <= max; v += 3) {
      s += `<line x1="${x(v)}" x2="${x(v)}" y1="${top - 6}" y2="${top + rowH * C.rows.length}" style="stroke:var(--ch-grid)" stroke-width="1"/>`;
      s += `<text x="${x(v)}" y="${top + rowH * C.rows.length + 20}" text-anchor="middle" style="fill:var(--ch-muted)" font-size="${fs - 2}">${v}</text>`;
    }
    C.rows.forEach((r, i) => {
      const y0 = top + i * rowH + 6, bh = (rowH - 18) / 2;
      s += `<text x="${left - 12}" y="${y0 + bh + 6}" text-anchor="end" style="fill:var(--ch-ink)" font-weight="700">${r.r} 米</text>`;
      [["low", r.low, r.low9, 0], ["high", r.high, r.high9, 1]].forEach(([k, v, v9, j]) => {
        const y = y0 + j * (bh + 4);
        s += `<rect x="${left}" y="${y}" width="${x(v) - left}" height="${bh}" rx="2" style="fill:var(--ch-${k})"/>`;
        s += `<text x="${x(v) + 6}" y="${y + bh - 4}" style="fill:var(--ch-ink)" font-weight="700" font-size="${fs}">${v}</text>`;
        s += `<line x1="${x(v9)}" x2="${x(v9)}" y1="${y - 3}" y2="${y + bh + 3}" style="stroke:var(--ch-ink)" stroke-width="2.5"/>`;
      });
    });
    s += `<text x="${left - 12}" y="${top + rowH * C.rows.length + 20}" text-anchor="end" style="fill:var(--ch-muted)" font-size="${fs - 2}">园校数</text>`;
    return s + "</svg>";
  };

  // 发现二：三个住宅到地段学校（圆）与积分志愿例（方）的步行分钟哑铃图。
  window.routeChart = function (o) {
    const R = window.C.f2.routes;
    const W = o.width, rowH = o.rowH || 54, top = o.top || 30, left = o.left || 130, right = o.right || 40;
    const fs = o.fs || 15, max = 30;
    const H = top + rowH * R.length + 28;
    const x = (m) => left + ((W - left - right) * m) / max;
    let s = `<svg class="chart route-chart" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" font-size="${fs}">`;
    s += `<g font-size="${fs - 1}">
      <circle cx="${left + 7}" cy="11" r="7" style="fill:var(--ch-a)"/>
      <text x="${left + 20}" y="16" style="fill:var(--ch-ink)">条件性地段学校</text>
      <rect x="${left + W * 0.32}" y="4" width="14" height="14" style="fill:var(--ch-b)"/>
      <text x="${left + W * 0.32 + 20}" y="16" style="fill:var(--ch-ink)">积分志愿例：冼村小学</text>
    </g>`;
    for (let v = 0; v <= max; v += 5) {
      s += `<line x1="${x(v)}" x2="${x(v)}" y1="${top}" y2="${top + rowH * R.length}" style="stroke:var(--ch-grid)"/>`;
      s += `<text x="${x(v)}" y="${top + rowH * R.length + 20}" text-anchor="middle" style="fill:var(--ch-muted)" font-size="${fs - 2}">${v}</text>`;
    }
    s += `<text x="${left - 14}" y="${top + rowH * R.length + 20}" text-anchor="end" style="fill:var(--ch-muted)" font-size="${fs - 2}">步行分钟</text>`;
    R.forEach((r, i) => {
      const cy = top + i * rowH + rowH / 2, a = r.a / 60, b = r.b / 60;
      s += `<text x="${left - 14}" y="${cy + 5}" text-anchor="end" style="fill:var(--ch-ink)" font-weight="700">${esc(r.name)}</text>`;
      s += `<line x1="${x(a)}" x2="${x(b)}" y1="${cy}" y2="${cy}" style="stroke:var(--ch-muted)" stroke-width="3" opacity=".45"/>`;
      s += `<circle cx="${x(a)}" cy="${cy}" r="8" style="fill:var(--ch-a)"/>`;
      s += `<rect x="${x(b) - 7.5}" y="${cy - 7.5}" width="15" height="15" style="fill:var(--ch-b)"/>`;
      const near = Math.abs(x(b) - x(a)) < 70;
      s += `<text x="${x(a)}" y="${cy - 14}" text-anchor="middle" style="fill:var(--ch-a)" font-weight="700">${minutes(r.a)}</text>`;
      s += `<text x="${near ? x(b) + 14 : x(b)}" y="${near ? cy + 5 : cy - 14}" text-anchor="${near ? "start" : "middle"}" style="fill:var(--ch-b)" font-weight="700">${minutes(r.b)}</text>`;
    });
    return s + "</svg>";
  };

  // 地图图例（中文），供各方案复用。
  window.mapLegend = function () {
    const L = window.C.mapLegend;
    const shape = (k, c) =>
      k === "sq"
        ? `<svg width="14" height="14"><rect x="1.5" y="1.5" width="11" height="11" fill="${c}"/></svg>`
        : k === "tri"
        ? `<svg width="14" height="14"><path d="M7 1.5 13 12.5H1Z" fill="${c}"/></svg>`
        : `<svg width="14" height="14"><path d="M7 1 13 7 7 13 1 7Z" fill="#fff" stroke="#17324d" stroke-width="1.4"/></svg>`;
    let h = `<div class="map-legend"><div class="ml-price"><span class="ml-t">住宅参考价 万元/㎡</span><span class="ml-ramp">`;
    L.price.forEach((p, i) => (h += `<span><i style="background:${L.priceColors[i]}"></i>${p}</span>`));
    h += `</span></div><div class="ml-sites">`;
    L.sites.forEach(([k, c, t]) => (h += `<span>${shape(k, c)}${t}</span>`));
    return h + `</div></div>`;
  };

  // 地图上的三个路线起点标记
  window.mapPins = function () {
    return window.C.pins
      .map((p) => `<span class="pin${p.left ? " l" : ""}" style="left:${p.x}%;top:${p.y}%">${p.left ? `<em>${p.name}</em>` : ""}<b>${p.id.slice(1)}</b>${p.left ? "" : `<em>${p.name}</em>`}</span>`)
      .join("");
  };

  // 引用序号 [n] 统一加样式
  window.cite = (html) => html.replace(/\[(\d[\d–,\s]*)\]/g, '<sup class="cite">[$1]</sup>');

  window.ready = () => document.fonts.ready.then(() => (document.body.dataset.ready = "1"));
})();
