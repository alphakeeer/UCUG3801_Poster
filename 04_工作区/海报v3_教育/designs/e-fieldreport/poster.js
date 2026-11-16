// 方案 E 渲染脚本：读取 window.K（中文 content2.js 或英文 content-en.js），生成整张海报。
(function () {
  const K = window.K, U = K.ui, lang = K.lang || "zh";
  const cite = (s) => String(s).replace(/\[([\d–,\s]+)\]/g, '<sup class="cite">[$1]</sup>');
  const sh = (no, nm) => `<div class="sh">${no ? `<span class="no">${no}</span>` : ""}<span class="nm">${nm}</span></div>`;
  const A = "../../assets/";
  let q = K.question;
  (U.hiQuestion || []).forEach(([a, b]) => (q = q.replace(a, b)));

  const hero = `
  <header class="hero pad">
    <img src="${A}hero.jpg" alt="" />
    <div class="topbar"><span class="brand"><span><b>UCUG3801</b>　${K.courseName}</span></span><span>${K.week}　·　${K.fieldShort}</span></div>
    <div class="ttl">
      <h1>${K.title.join("<br>").replace(K.titleHi, `<em>${K.titleHi}</em>`)}</h1>
      <div class="sub">${K.subtitle}</div>
      <div class="members">${K.members}</div>
    </div>
    <div class="photo">${K.coverCaption}</div>
    <div class="q"><span>${U.rq}</span><p>${q}</p></div>
  </header>`;

  const ctx = `
  <section class="ctx pad">
    <div>${sh("01", U.s["01"])}<p class="t">${cite(K.background)}</p>
      <div class="tl">${K.timeline.map(([y, t]) => `<div><b>${y}</b>${cite(t)}</div>`).join("")}</div></div>
    <div>${sh("02", U.s["02"])}<div class="cc">${K.concepts
      .map((c) => `<div><div class="h"><b>${c.key}</b><small>${c.who.replace(/\s*\[\d+\]/, "")} · ${c.week}</small></div><p>${c.def}</p><p><em>${U.inLiede}</em>${c.use}</p></div>`)
      .join("")}</div></div>
    <div>${sh("03", U.s["03"])}<div class="mm">${K.methods.map((m) => `<div><i>${m.k}</i><span><b>${m.t}</b>${m.d}</span></div>`).join("")}</div></div>
  </section>`;

  const kpi = (k) => `<div class="kpi"><div class="n">${k.n}</div><div class="t">${k.t}</div><div class="s">${k.s}</div></div>`;

  const f1 = `
  <section class="f1 pad">
    <div class="fhead"><div>${sh("04", U.s["04"])}<h2>${K.f1.title}</h2><p class="lead">${cite(K.f1.leadE || K.f1.lead)}</p></div>${kpi(K.kpi1)}</div>
    <div class="f1body">
      <div class="mapbox" id="map"></div>
      <div><div id="tbl"></div><p class="cap">${cite(K.f1.caption)}</p></div>
    </div>
  </section>`;

  const C = K.compare;
  const cell = (v) => `<span class="big">${v.big}</span>${v.u ? `<span class="u">${v.u}</span>` : ""}${v.s ? `<span class="s">${cite(v.s)}</span>` : ""}`;
  const f2 = `
  <section class="f2 pad">
    <div class="fhead"><div>${sh("05", U.s["05"])}<h2>${K.f2.title}</h2><p class="lead">${cite(K.f2.leadE)}</p></div>${kpi(K.kpi2)}</div>
    <div class="f2body">
      <div>
        <div class="ch">
          <div class="r h"><span>${U.chHead[0]}</span><span>${U.chHead[1]}</span><span>${U.chHead[2]}</span></div>
          ${K.f2.rows.map((r, i) => `<div class="r ${i === 1 ? "hl" : ""}"><b>${r.who}</b><span>${r.doc}</span><span class="c">${r.ch}</span></div>`).join("")}
          <p class="note">${K.f2.note}</p>
        </div>
        <figure class="kgph"><img src="${A}web/p03-liede-kg.png" alt="" /><figcaption><b>${K.kgPhoto.t}</b>${cite(K.kgPhoto.c)}</figcaption></figure>
      </div>
      <div class="cmp">
        <div class="bf">
          <div class="bf-h">
            <figure class="a"><img src="${A}f04.jpg" alt="" /><figcaption><b>${C.a.name}</b><span>${C.a.type}</span></figcaption></figure>
            <figure class="b"><img src="${A}web/p01-nanguo.jpg" alt="" /><figcaption><b>${C.b.name}</b><span>${C.b.type}</span></figcaption></figure>
          </div>
          ${K.cmpRows.map((r) => `<div class="bf-r"><div class="va">${cell(r.a)}</div><div class="k">${r.k}</div><div class="vb">${cell(r.b)}</div></div>`).join("")}
        </div>
        <p class="cap">${K.cmpNote}</p>
      </div>
    </div>
  </section>`;

  const an = `
  <section class="an pad">
    ${sh("06", U.s["06"])}
    ${K.analysis.map((a, i) => `<div class="col"><h4><i>${"ABC"[i]}</i>${a.h}</h4><p>${a.t}</p></div>`).join("")}
    <div class="concl"><div class="lb">${U.concl}</div><h4>${K.conclusion.lead}</h4><p>${K.conclusion.body}</p><p class="nx">${K.conclusion.next}</p></div>
  </section>`;

  const ft = `
  <footer class="ft pad">
    <div>${sh("07", U.s["07"])}<div class="lim">${K.limits.map(([k, v]) => `<div><b>${k}</b>${v}</div>`).join("")}</div><p class="refl"><b>${U.refl}</b>${K.reflexivity}</p></div>
    <div>${sh("08", U.s["08"])}<ol class="refs">${K.refs.map((r) => `<li>${r}</li>`).join("")}</ol><p class="credit">${K.credit}</p></div>
  </footer>`;

  document.getElementById("poster").innerHTML = hero + ctx + f1 + f2 + an + ft;
  const MV = K.mapOpts || {};
  document.getElementById("map").innerHTML =
    a3.map({ id: "e", lang, w: 570, h: MV.h || 340, annoK: MV.annoK || 1.12, hideLabels: ["P07"], view: [-900, -560, 1250, 790], k: 0.82, noScale: true, northAt: [550, 36] }) + a3.legend({ lang, pxPerM: 570 / 2150 });
  document.getElementById("tbl").innerHTML = a3.table({ lang });
  document.fonts.ready.then(() => (document.body.dataset.ready = 1));
})();
