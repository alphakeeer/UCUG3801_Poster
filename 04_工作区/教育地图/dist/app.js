import { AtlasMap, project } from "./map.js";

const $ = (selector) => document.querySelector(selector);
const escapeHTML = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (character) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        character
      ],
  );
const number = (value) => Number(value).toLocaleString("zh-CN");
const stageNames = { kg: "幼儿园", primary: "小学", junior: "初中" };
const stageMarks = { kg: "幼", primary: "小", junior: "初" };
const modeNames = {
  distribution: "学校分布",
  admission: "入学路径",
  fees: "费用与支持",
  relations: "小学与初中",
  compare: "并排比较",
};
const mobile = () => innerWidth <= 900;
const sceneNames = [
  "观察学校分布",
  "住房与名额分配",
  "来穗家庭的申请路径",
  "追踪小学升初中",
  "猎德与利民的公共供给",
];
const sourceButton = (id, label = "查看依据") =>
  `<button class="source-link" data-source="${escapeHTML(id)}">${label} ↗</button>`;

let data;
let schools;
let byId;
let map;
let markerElements = [];
let toastTimer;

const params = new URLSearchParams(location.hash.slice(1));
const state = {
  mode: Object.hasOwn(modeNames, params.get("mode"))
    ? params.get("mode")
    : "distribution",
  stage: ["all", "kg", "primary", "junior"].includes(params.get("stage"))
    ? params.get("stage")
    : "all",
  owner: "all",
  query: "",
  selected: params.get("school") || (mobile() ? null : "E004-052"),
  detailTab: "overview",
  compare: [],
  compareType: "schools",
  expanded: false,
  scene: null,
  collapsed: mobile(),
  hukou: "tianhe",
  housing: "owned",
  integral: false,
  feeItem: "tuition",
  seniorKindergarten: false,
};

function notify(message) {
  clearTimeout(toastTimer);
  $("#toast").textContent = message;
  $("#toast").hidden = false;
  toastTimer = setTimeout(() => {
    $("#toast").hidden = true;
  }, 3600);
}

function filteredSchools() {
  const query = state.query.trim().toLowerCase();
  return schools.filter(
    (school) =>
      (state.stage === "all" || school.stage === state.stage) &&
      (state.owner === "all" ||
        school.owner === state.owner ||
        (state.owner === "inclusive" && school.inclusive)) &&
      (!query ||
        `${school.name} ${school.short} ${school.address} ${school.campus}`
          .toLowerCase()
          .includes(query)),
  );
}

function updateURL() {
  const current = new URLSearchParams();
  if (state.mode !== "distribution") current.set("mode", state.mode);
  if (state.stage !== "all") current.set("stage", state.stage);
  if (state.selected) current.set("school", state.selected);
  const hash = current.toString();
  history.replaceState(
    null,
    "",
    `${location.pathname}${location.search}${hash ? "#" + hash : ""}`,
  );
}

function admissionPath(school) {
  if (school.stage === "kg") {
    if (school.owner === "public") {
      if (state.hukou !== "tianhe")
        return {
          title: "政策照顾 / 自主招生条件待核",
          body: "教育部门园社会派位面向天河户籍及符合政策性照顾的非穗籍幼儿。政策类别与园所自主招生材料需逐项核验。",
          source: "E003",
        };
      return state.housing === "owned"
        ? {
            title: "配套优先或社会派位",
            body: "符合本区户籍配套小区业主等条件，可进入优先登记。配套范围、产权、人户条件及住宅学位使用仍需园方核对，其余按社会派位规则申请。",
            source: "E003",
          }
        : {
            title: "社会电脑随机派位",
            body: "天河户籍适龄幼儿可按文件参加社会派位，2026年选择1所教育部门办园。年龄、材料及当年报名时间仍需满足。",
            source: "E003",
          };
    }
    if (school.owner === "other")
      return {
        title: "本系统与社会招生",
        body: "其他部门办园除招收本系统工作人员子女，剩余学位面向社会。具体比例、条件、流程由举办部门与园所公布。",
        source: "E003",
      };
    return {
      title: "民办园社会招生",
      body: "面向社会招生。小区配套、普惠优抚、招生材料及收费按该园当年简章核验。",
      source: "E003",
    };
  }
  if (school.owner === "private")
    return {
      title:
        state.hukou === "migrant" && state.integral
          ? "民办报名与积分渠道"
          : "民办学校报名",
      body: "按天河户籍、学籍或有效居住证等适用条件报名，超计划时电脑派位。积分补贴需经系统录取、注册报到且实际就读，逐校计划另核。",
      source: "E002",
    };
  if (state.hukou === "migrant") {
    const integral = school.plans.find(
      (plan) => plan.category === "来穗积分渠道",
    );
    if (state.integral && integral)
      return {
        title: `公布积分计划 ${integral.amount}人`,
        body: "市积分核定后，还需满足连续居住证、天河居住或就业等申请条件，按积分优先、遵循志愿录取。计划人数对应2026该渠道。",
        source: "E030",
      };
    return {
      title: state.integral
        ? "专项计划与政策类别待核"
        : "积分 / 政策照顾条件待核",
      body: "非穗籍家庭需匹配来穗积分、政策性照顾或其他明确渠道。当前公开计划及家庭证明材料需要一起核验。",
      source: "E030",
    };
  }
  if (school.stage === "junior")
    return {
      title: school.id === "J05" ? "自主报名电脑派位" : "小学对口 / 地段或统筹",
      body:
        school.id === "J05"
          ? "珠江新城校区面向天河区穗籍小学毕业生，含符合条件的政策性照顾学生、返区生，按附件10报名及派位。"
          : "毕业小学、户籍、实际居住、人户一致及返区或跨地段类别共同影响初中申请。学校对口关系和具体校区分流需分别核验。",
      source: "E002",
    };
  if (state.hukou === "tianhe" && state.housing === "owned")
    return {
      title: "地段生条件待核",
      body: "文件要求人户一致、完全房产等条件及学位未被占用。具体门牌、入住和办理时间需与学校招生地段一并核查。",
      source: "E002",
    };
  return {
    title: "统筹条件待核",
    body: "广州户籍租住或其他居住类别需核无其他房产、唯一居住地、租赁备案及规定时间等材料，由教育局按适用类别统筹。",
    source: "E002",
  };
}

function feeFor(school) {
  if (state.feeItem === "subsidy") {
    if (school.owner === "private" && school.stage !== "kg")
      return {
        value: school.stage === "primary" ? 2500 : 3000,
        unit: "元 / 人·学期",
        label: "积分民办学位补贴",
        source: "E030",
        note: "需经积分系统录取、注册报到且实际在天河民办学校就读。补贴由学校发放或抵减，实际收费核算待学校公示。",
      };
    return {
      value: null,
      label: "查看适用补贴渠道",
      unit: "",
      source: "E030",
      note: "当前所选项目适用于符合条件的民办小学与初中积分就读者。",
    };
  }
  if (state.feeItem === "aftercare") {
    if (school.stage !== "kg")
      return {
        value: 2,
        unit: "元 / 人·40分钟课时",
        label: "学校提供的课后服务",
        source: "E051",
        note: "按实际参加计费。认定家庭经济困难学生参加学校提供服务免收。第三方素质拓展适用另行规定，学校具体项目待核。",
      };
    return {
      value: null,
      unit: "",
      label: "逐园托管项目待核",
      source: "E039",
      note: "幼儿园托管按相应政策及园所公示核验，当前未取得逐园2026实际收费。",
    };
  }
  if (school.stage === "kg") {
    if (state.seniorKindergarten && school.owner !== "private")
      return {
        value: 0,
        unit: "元 / 人·月",
        label: "适龄大班保教费减免",
        source: "E009",
        note: "自2025秋季起按政策免公办园学前一年保教费，适龄及班型条件需核。伙食、住宿和批准的服务代收费分别处理。",
      };
    return {
      value: null,
      unit: "元 / 人·月",
      label: state.seniorKindergarten
        ? "民办大班差额待核"
        : "逐园保教费公示待取得",
      source: state.seniorKindergarten ? "E009" : "E039",
      note: state.seniorKindergarten
        ? "按本区同类型公办水平相应减免，园所原价、减免额和剩余差额待核。"
        : "广州2024公办全日制类别基准为规范园823、示范园995元/月。逐园2026类别、实际公示及新老生条件仍需核对。",
    };
  }
  return {
    value: school.tuition,
    unit: "元 / 人·学期",
    label: school.owner === "private" ? "正式批复学费标准" : "公办义务教育学费",
    source: school.tuitionSource || "E055",
    note:
      school.owner === "private"
        ? "批复自2024秋季起四学年。实际可下浮，需核新老生条件及公用经费补助、积分补贴扣除。餐费等另核。"
        : "依法免收学费、杂费。餐费、交通、课后服务和住宿等依法列明项目另行核验。",
  };
}

function pathMetric(school) {
  const title = admissionPath(school).title;
  if (title.includes("配套")) return "配套条件待核";
  if (title.includes("随机")) return "社会随机派位";
  if (title.includes("本系统")) return "园方规则待核";
  if (title.includes("积分计划")) return title;
  if (title.includes("统筹")) return "统筹条件待核";
  if (title.includes("地段生")) return "地段条件待核";
  if (title.includes("对口")) return "对口条件待核";
  if (title.includes("民办")) return "民办报名";
  return "申请条件待核";
}

function feeMetric(school) {
  const fee = feeFor(school);
  if (fee.value === null) return "待核";
  if (fee.value === 0) return school.stage === "kg" ? "免保教费" : "免学费";
  return `${state.feeItem === "subsidy" ? "补贴 " : "¥"}${number(fee.value)}`;
}

function feeUnit() {
  if (state.feeItem === "aftercare") return "元/人/40分钟课时";
  return state.feeItem === "tuition" && state.stage === "kg"
    ? "元/人/月"
    : "元/人/学期";
}

function sourceIds(school) {
  const ids = [school.source, "E002", school.stage === "kg" ? "E003" : "E030"];
  if (school.stage === "kg")
    ids.push(
      school.owner === "private"
        ? "E006"
        : school.owner === "other"
          ? "E005"
          : "E004",
    );
  if (school.tuitionSource) ids.push(school.tuitionSource);
  if (school.id === "E005-032") ids.push("E024");
  if (school.inspection) ids.push("E058-A001");
  return [...new Set(ids)];
}

function relationGroups() {
  const grouped = [];
  const tianheOrigins = ["P09", "P06", "P03", "P07", "P08", "P05", "P04"];
  for (const origin of tianheOrigins)
    grouped.push({
      from: origin,
      targets: ["J03", "J04"],
      kind: "direct",
      note: "天河中学学校层级对口，具体校区分流待核",
      source: "E002",
    });
  for (const [from, to] of [
    ["P01", "J01"],
    ["P02", "J02"],
    ["P10", "J06"],
  ]) {
    grouped.push({
      from,
      targets: [to],
      kind: "direct",
      note: "按当年毕业资格、户籍及招生规则核验对口路径",
      source: "E002",
    });
  }
  return grouped;
}

function activeRelations() {
  if (state.mode !== "relations" || !state.selected) return [];
  return relationGroups().filter(
    (edge) =>
      edge.from === state.selected || edge.targets.includes(state.selected),
  );
}

function createMarkers() {
  const edges = activeRelations();
  const relatedIds = new Set(
    edges.flatMap((edge) => [edge.from, ...edge.targets]),
  );
  const records = [
    ...new Map(
      [
        ...filteredSchools(),
        ...schools.filter((school) => relatedIds.has(school.id)),
      ].map((school) => [school.id, school]),
    ).values(),
  ].filter((school) => school.position);
  const groups = new Map();
  for (const school of records) {
    const key = `${school.position.lon.toFixed(5)},${school.position.lat.toFixed(5)}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(school);
  }
  const fragment = document.createDocumentFragment();
  markerElements = [];
  for (const group of groups.values()) {
    const school = group.find((item) => item.id === state.selected) || group[0];
    const button = document.createElement("button");
    const selected = group.some((item) => item.id === state.selected);
    const compared = group.some((item) => state.compare.includes(item.id));
    const related = group.some((item) => relatedIds.has(item.id));
    button.className = `map-marker ${school.owner} ${school.stage}${selected ? " is-selected" : ""}${compared ? " is-compared" : ""}${related ? " is-related" : ""}${state.mode === "fees" || (state.mode === "admission" && selected) ? " has-metric" : ""}`;
    button.dataset.school = school.id;
    button.setAttribute(
      "aria-label",
      `${school.short}，${stageNames[school.stage]}${group.length > 1 ? "，同址多个学段" : ""}`,
    );
    button.setAttribute("aria-pressed", String(selected));
    button.innerHTML = `<span class="marker-dot"><b>${stageMarks[school.stage]}</b>${group.length > 1 ? `<span class="stage-count">${group.length}</span>` : ""}</span>
      <span class="marker-caption">${escapeHTML(school.short)}</span>
      ${state.mode === "admission" && selected ? `<span class="marker-metric">${escapeHTML(pathMetric(school))}</span>` : ""}
      ${state.mode === "fees" ? `<span class="marker-metric">${escapeHTML(feeMetric(school))}</span>` : ""}`;
    fragment.append(button);
    markerElements.push({ button, school });
  }
  $("#map-markers").replaceChildren(fragment);
  positionMarkers();
}

function positionMarkers() {
  if (!map) return;
  const label = $("#study-area-label");
  const [labelX, labelY] = map.screen(project(113.328, 23.1158));
  label.style.left = `${labelX}px`;
  label.style.top = `${labelY}px`;
  label.hidden =
    !map.showBoundary ||
    labelX < 0 ||
    labelX > map.width ||
    labelY < 100 ||
    labelY > map.height - 50;
  $("#study-area").classList.toggle("boundary-off", !map.showBoundary);
  $("#study-area-description").textContent = map.showBoundary
    ? "绿色覆盖为研究主体，周边学校一并展示。"
    : "覆盖层已隐藏，点击“查看范围”可重新显示。";
  for (const { button, school } of markerElements) {
    const [x, y] = map.screen(school.position.xy);
    button.style.left = `${x}px`;
    button.style.top = `${y}px`;
    button.hidden =
      x < -60 || y < 75 || x > map.width + 60 || y > map.height + 60;
  }
  drawConnections();
}

function drawConnections() {
  const svg = $("#connections");
  const focusedRelation = document.activeElement?.dataset.relation;
  svg.setAttribute("viewBox", `0 0 ${map.width} ${map.height}`);
  const elements = [];
  for (const edge of activeRelations()) {
    const origin = byId.get(edge.from);
    const targets = edge.targets
      .map((id) => byId.get(id))
      .filter((school) => school?.position);
    if (!origin?.position || !targets.length) continue;
    const [x1, y1] = map.screen(origin.position.xy);
    const targetPoints = targets.map((target) =>
      map.screen(target.position.xy),
    );
    const x2 =
      targetPoints.reduce((sum, point) => sum + point[0], 0) /
      targetPoints.length;
    const y2 =
      targetPoints.reduce((sum, point) => sum + point[1], 0) /
      targetPoints.length;
    let path;
    if (Math.hypot(x2 - x1, y2 - y1) < 8) {
      path = `M${x1},${y1} C${x1 + 85},${y1 - 90} ${x1 + 110},${y1 + 55} ${x1 + 8},${y1 + 4}`;
    } else {
      path = `M${x1},${y1} Q${(x1 + x2) / 2},${Math.min(y1, y2) - 38} ${x2},${y2}`;
    }
    elements.push(
      `<path class="relation-line" d="${path}" data-relation="${escapeHTML(edge.from)}" marker-end="url(#relation-arrow)" tabindex="0" role="button" aria-label="${escapeHTML(origin.short + "的对口关系，" + edge.note)}"><title>${escapeHTML(edge.note)}</title></path>`,
    );
    if (targets.length > 1) {
      for (const [x, y] of targetPoints)
        elements.push(
          `<path d="M${x2},${y2} L${x},${y}" fill="none" stroke="#879b76" stroke-width="1.2" stroke-dasharray="3 4"/>`,
        );
      elements.push(
        `<text x="${x2 + 8}" y="${y2 - 9}" fill="#617a55" font-size="10" paint-order="stroke" stroke="#faf9f4" stroke-width="3">天河中学 · 学校层级</text>`,
      );
    }
  }
  svg.innerHTML = `<defs><marker id="relation-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 Z" fill="#376d59"/></marker></defs>${elements.join("")}`;
  if (focusedRelation)
    svg
      .querySelector(`[data-relation="${focusedRelation}"]`)
      ?.focus({ preventScroll: true });
}

function renderList() {
  const records = filteredSchools();
  const mapped = records.filter((school) => school.position).length;
  $("#result-count").textContent =
    `${records.length} 条资料 · ${mapped} 条已定位`;
  $("#school-list").innerHTML = records.length
    ? records
        .map(
          (school) => `
    <button class="school-item${school.id === state.selected ? " is-selected" : ""}" data-school="${escapeHTML(school.id)}" aria-pressed="${school.id === state.selected}">
      <span class="school-name"><i class="legend-dot ${school.owner}" aria-hidden="true"></i><span>${escapeHTML(school.short)}</span></span>
      <span class="school-address">${escapeHTML(school.address.replace(/^广州市天河区|^广州市|^天河区/, ""))}</span>
      <span class="school-meta"><span>${stageNames[school.stage]} · ${school.inclusive ? "普惠性民办" : escapeHTML(school.organizer)}</span>
      <span class="${school.position ? "" : "unmapped-label"}">${state.mode === "fees" ? escapeHTML(feeMetric(school)) : state.mode === "admission" ? escapeHTML(pathMetric(school)) : school.position ? "↗ 地图" : "位置待核"}</span></span>
    </button>`,
        )
        .join("")
    : '<p class="empty-state">当前条件下没有匹配资料。可调整学段、主体或检索词。</p>';
}

function lotteryChart(school) {
  const lottery = school.lottery;
  if (!lottery) return "";
  const ownerWidth = (lottery.owners / lottery.total) * 100;
  return `<h3>社会电脑派位名额</h3>
    <div class="stacked-bar" role="img" aria-label="业主子女${lottery.owners}人，剩余随机${lottery.random}人，总数${lottery.total}人">
      <span class="bar-owner" style="width:${ownerWidth}%"></span><span class="bar-random" style="width:${100 - ownerWidth}%"></span>
    </div><div class="bar-legend"><span><i></i>业主子女 ${lottery.owners}</span><span><i></i>剩余随机 ${lottery.random}</span></div>
    <p>2026年公布计划。报名人数与最终录取汇总待取得。</p>${sourceButton("E004")}`;
}

function overview(school) {
  const relatedStages = schools.filter(
    (item) =>
      item.id !== school.id &&
      item.institution === school.institution &&
      item.address === school.address &&
      item.stage !== school.stage,
  );
  const plan = school.plans.find(
    (item) =>
      item.category.includes("公布") ||
      item.category.includes("普通") ||
      item.category === "学校合计" ||
      item.category === "电脑派位",
  );
  const stats = school.lottery
    ? [
        [school.lottery.total, "人", "社会派位总数"],
        [school.classes, "班", "小班计划"],
        [school.lottery.random, "人", "剩余随机名额"],
      ]
    : school.classes
      ? [[school.classes, "班", "2026小班计划"]]
      : plan
        ? [[plan.amount, plan.unit, plan.category]]
        : [];
  return `${stats.length ? `<div class="stat-grid">${stats.map(([amount, unit, label]) => `<div><strong>${number(amount)}<span class="unit">${unit}</span></strong><small>${escapeHTML(label)}</small></div>`).join("")}</div>` : ""}
    ${school.lottery ? lotteryChart(school) : `<h3>位置与办学</h3><ul class="fact-list"><li><span>街道</span><strong>${escapeHTML(school.street || "当前归属待核")}</strong></li><li><span>举办主体</span><strong>${escapeHTML(school.organizer)}</strong></li>${school.inclusive ? "<li><span>普惠属性</span><strong>2026名录列普惠性民办园</strong></li>" : ""}${school.inspection ? `<li><span>年检</span><strong>2025年度 ${escapeHTML(school.inspection)}</strong></li>` : ""}</ul>`}
    ${relatedStages.length ? `<p class="section-label" style="margin-top:20px">同址其他学段</p><div class="stage-choices">${relatedStages.map((item) => `<button data-school="${item.id}">${stageNames[item.stage]} ↗</button>`).join("")}</div>` : ""}
    ${school.id === "E005-032" ? '<p>2025年开园，2026名录列为国企办规范园，小班计划3班。</p><button class="source-link" data-timeline>查看公共供给时间线 ↗</button>' : ""}
    <div class="source-inline"><span>${escapeHTML(school.locator)}</span>${sourceButton(school.source, "原始资料")}</div>`;
}

function admissionDetail(school) {
  const path = admissionPath(school);
  const plans = school.plans.filter(
    (plan) =>
      plan.category.includes("积分") ||
      plan.category.includes("港澳") ||
      plan.category.includes("派位"),
  );
  return `<p class="section-label">当前构造条件下的文件路径</p><div class="condition-box"><h3>${escapeHTML(path.title)}</h3><p>${escapeHTML(path.body)}</p>${sourceButton(path.source)}</div>
    ${school.lottery ? lotteryChart(school) : ""}
    ${plans.map((plan) => `<div class="condition-box"><h3>${escapeHTML(plan.category)} · ${plan.amount}${plan.unit}</h3><p>${escapeHTML(plan.note || "按对应申请资格和时间要求核验。")}</p>${sourceButton(plan.source)}</div>`).join("")}
    <p class="method-note">家庭条件用于解释规则。具体资格还需完整材料、规定时间、地段或配套范围及学校审核。</p>
    <button class="source-link" data-activate-admission>调整家庭条件 ↗</button>`;
}

function feesDetail(school) {
  const fee = feeFor(school);
  return `<p class="cost-label">${escapeHTML(fee.label)}</p><div class="cost-number">${fee.value === null ? "待核" : number(fee.value)}<small>${escapeHTML(fee.unit)}</small></div>
    <p>${escapeHTML(fee.note)}</p>${sourceButton(fee.source)}
    <ul class="fact-list"><li><span>依据状态</span><strong>${state.feeItem === "tuition" && school.tuition !== null && school.owner === "private" && school.stage !== "kg" ? "正式批复已取得，实际公示待核" : fee.value === null ? "具体项目与适用条件待核验" : "政策标准，适用条件见原文"}</strong></li><li><span>餐饮交通</span><strong>当前实收费待取得</strong></li><li><span>其他项目</span><strong>托管、校服、住宿等按项目核验</strong></li></ul>
    <p class="method-note">批复标准、补贴、减免与家庭实付各有适用条件。跨周期费用需按来源核对。</p>`;
}

function renderDetail() {
  const panel = $("#detail-panel");
  const school = byId.get(state.selected);
  panel.hidden = !school;
  $("#atlas").classList.toggle("detail-closed", !school);
  if (!school) return;
  const tabs = [
    ["overview", "概况"],
    ["admission", "入学"],
    ["fees", "费用"],
    ["sources", "证据"],
  ];
  let body;
  if (state.detailTab === "admission") body = admissionDetail(school);
  else if (state.detailTab === "fees") body = feesDetail(school);
  else if (state.detailTab === "sources")
    body = `<h3>可追溯的资料依据</h3>${sourceIds(school)
      .map(
        (id) =>
          `<div class="source-item"><strong>${escapeHTML(data.sources[id]?.title || id)}</strong><small>${escapeHTML(data.sources[id]?.date || "")}</small>${sourceButton(id, "查看文件与定位")}</div>`,
      )
      .join("")}
    <div class="method-note">${school.position ? `${escapeHTML(school.position.method)} · ${escapeHTML(school.position.name)}。${escapeHTML(school.position.note)}。<br><a href="${escapeHTML(school.position.url)}" target="_blank" rel="noopener noreferrer">查看位置来源 ↗</a>` : "当前有官方地址，可靠地图坐标待补。"}</div>`;
  else body = overview(school);
  panel.innerHTML = `<div class="detail-top"><p class="eyebrow"><i class="legend-dot ${school.owner}"></i> 学校档案 · ${stageNames[school.stage]}</p><button class="icon-button" data-close-detail aria-label="关闭学校详情">×</button>
      <h2>${escapeHTML(school.short)}</h2><p class="address">${escapeHTML(school.address)}</p>
      <div class="detail-tags"><span>${escapeHTML(school.organizer)}</span>${school.inclusive ? "<span>普惠性</span>" : ""}<span>${school.position ? "校园参照点" : "位置待核"}</span><span>${school.areaLabel}</span><span class="year">2026资料</span></div></div>
    <div class="detail-tabs" role="tablist" aria-label="学校资料栏目">${tabs.map(([id, title]) => `<button role="tab" id="tab-${id}" data-detail-tab="${id}" aria-controls="detail-tab-content" aria-selected="${state.detailTab === id}" tabindex="${state.detailTab === id ? 0 : -1}">${title}</button>`).join("")}</div>
    <div id="detail-tab-content" class="detail-body" role="tabpanel" aria-labelledby="tab-${state.detailTab}">${body}</div>
    <div class="detail-bottom"><button class="primary-button" data-compare="${school.id}">${state.compare.includes(school.id) ? "已加入比较 · 移除" : "加入学校比较"}</button><button class="secondary-button" data-show-relations="${school.id}">${school.stage === "kg" ? "招生计划" : "升学关系"} ↗</button></div>`;
}

function miniBars(records, value, unit, maximum) {
  const max = maximum || Math.max(...records.map(value), 1);
  return `<div class="mini-bars">${records.map((school) => `<div class="mini-bar-row"><button data-school="${school.id}">${escapeHTML(school.short)}</button><div class="track"><div class="fill" style="width:${(value(school) / max) * 100}%"></div></div><span class="value">${number(value(school))}${unit}</span></div>`).join("")}</div>`;
}

function timeline() {
  return `<span class="concept">空间不平等 · 公共供给回应</span><p>利民社区华文幼儿园的建设与开办，为观察街道内部配套时差提供一个案例。</p>
    <div class="timeline">${[
      ["2022", "居民诉求<br>项目批复"],
      ["2023", "开始动工"],
      ["2024", "主体封顶"],
      ["2025", "9月正式开园"],
      ["2026", "名录列国企办<br>小班计划3班"],
    ]
      .map(
        ([year, text]) =>
          `<button data-source="${year === "2026" ? "E005" : "E024"}"><strong>${year}</strong><small>${text}</small></button>`,
      )
      .join("")}</div>
    <p>报道总容量7班210个学位，2026小班计划3班。家庭实际受益与社会招生细目继续核验。</p>${sourceButton("E024", "开办与建设记录")}`;
}

function schoolComparison() {
  const selected = state.compare.map((id) => byId.get(id)).filter(Boolean);
  if (selected.length < 2)
    return `<div class="compare-prompt"><p>从地图或资料列表选择两所同学段学校，点击详情中的“加入学校比较”。</p></div>
    ${selected.map((school) => `<button class="compare-chip" data-school="${school.id}">${escapeHTML(school.short)}</button>`).join("")}
    <p class="fine-print">${selected.length ? "已选1所，可继续选择另一所学校。" : "比较项包括申请路径、名额、费用依据及待核信息。"}</p>`;
  return `<div class="compare-grid">${selected
    .map((school) => {
      const fee = feeFor(school);
      return `<div class="compare-column"><h3><button data-school="${school.id}">${escapeHTML(school.short)} ↗</button></h3><dl>
      <dt>办学与学段</dt><dd>${escapeHTML(school.organizer)} · ${stageNames[school.stage]}</dd>
      <dt>公布计划</dt><dd>${school.lottery ? `${school.lottery.total}人社会派位，${school.lottery.random}人剩余随机` : school.classes ? `小班${school.classes}班` : school.plans[0] ? `${escapeHTML(school.plans[0].category)} ${school.plans[0].amount}${school.plans[0].unit}` : "计划口径待核"}</dd>
      <dt>文件路径</dt><dd>${escapeHTML(admissionPath(school).title)}</dd>
      <dt>${escapeHTML(fee.label)}</dt><dd>${fee.value === null ? "待核" : `${number(fee.value)} ${escapeHTML(fee.unit)}`}</dd>
      <dt>继续核验</dt><dd>实际收费、申请材料与校门路线</dd></dl><button class="remove-compare" data-compare="${school.id}">移除此校</button></div>`;
    })
    .join(
      "",
    )}</div><p class="comparison-key">相同学段 · 计划单位按各文件标注 · 实缴及供需分母仍待取得</p>`;
}

function communityComparison() {
  return `<span class="concept">空间不平等 · 制度性分层</span><div class="compare-grid"><div class="compare-column"><h3><button data-school="E004-052">猎德社区侧 ↗</button></h3><dl><dt>研究对象</dt><dd>猎德幼儿园、猎德实验学校及附近供给</dd><dt>已知入口</dt><dd>教育部门园业主优先及社会随机派位</dd><dt>计划实例</dt><dd>猎德园135人，业主85、剩余随机50</dd></dl></div>
    <div class="compare-column"><h3><button data-focus-limin>利民社区侧 ↗</button></h3><dl><dt>研究对象</dt><dd>华文幼儿园、启赋幼儿园及附近小学地段</dd><dt>已知入口</dt><dd>国企办园系统与社会招生，民办普惠园</dd><dt>供给变化</dt><dd>华文2025开园，2026小班计划3班</dd></dl></div></div>
    <p class="fine-print">两社区暂定为研究比较对象。边界、同口径学校数量、路线及实际费用需补证。地图通过已定位学校提供地理参照。</p><button class="source-link" data-timeline>展开公共供给时间线 ↗</button>`;
}

function relationsContent() {
  const selected = byId.get(state.selected);
  const edges = activeRelations();
  if (!selected)
    return '<span class="concept">社会再生产 · 阶段之间的制度联系</span><p>选择小学或初中，查看当年文件支持的对口关系。</p><button class="source-link" data-school="P06">从兴国小学开始 ↗</button>';
  if (!edges.length)
    return `<span class="concept">制度性分层 · 申请资格</span><p>${selected.id === "J05" ? "天河外国语珠江新城校区面向天河区穗籍小学毕业生，含符合条件的政策性照顾学生、返区生。6班216人，采用自主报名电脑派位。" : "当前选择尚无已整理的具体对口连线，可查看完整当年招生附件及申请条件。"}</p>${sourceButton("E002", "查看2026升学文件")}`;
  return `<span class="concept">社会再生产 · 小学经历与后续路径</span>${edges.map((edge) => `<button class="related-button" data-school="${edge.from === state.selected ? edge.targets[0] : edge.from}">${escapeHTML(byId.get(edge.from).short)} → ${edge.targets.length > 1 ? "天河中学" : escapeHTML(byId.get(edge.targets[0]).short)}<span>↗</span><small>${escapeHTML(edge.note)}</small></button>`).join("")}
    <p class="fine-print">2026文件的对口关系需与毕业资格、户籍及相应材料共同核验。</p>${sourceButton("E002")}`;
}

function renderAnalysis() {
  const panel = $("#analysis-panel");
  const selected = byId.get(state.selected);
  let kicker = "研究视角";
  let title = "学校位置如何转化为教育机会？";
  let content =
    '<span class="concept">空间不平等 · 制度性分层 · 社会再生产</span><p>居住位置、申请资格与家庭资源共同影响教育机会。点击学校，沿名额、入学条件、费用和升学关系探索。</p><p>目前有50条校区学段或园区资料，已定位点附位置来源。实际校门、路线与家庭使用经验继续补证。</p>';
  if (state.mode === "admission") {
    kicker = "制度性分层";
    title = selected?.lottery
      ? "住房条件如何进入学位分配？"
      : "不同家庭有哪些文件支持的申请路径？";
    content = selected
      ? `<span class="concept">当前构造条件</span><p>${escapeHTML(admissionPath(selected).title)}。${escapeHTML(admissionPath(selected).body)}</p>${selected.lottery ? lotteryChart(selected) : sourceButton(admissionPath(selected).source)}`
      : "<p>调整左侧家庭条件，再点击学校查看文件路径与待核材料。</p>";
  } else if (state.mode === "fees") {
    kicker = "教育支出与公共支持";
    title =
      state.feeItem === "subsidy"
        ? "补贴怎样影响教育负担？"
        : "同学段的收费依据与适用条件";
    const candidates = filteredSchools().filter(
      (school) => feeFor(school).value !== null,
    );
    const comparable =
      state.stage === "all"
        ? candidates.filter((school) => school.stage === "primary")
        : candidates;
    const positive = comparable
      .filter((school) => feeFor(school).value > 0)
      .slice(0, 5);
    content = `<span class="concept">家庭资源 · 公共支持</span>${positive.length ? miniBars(positive, (school) => feeFor(school).value, "元") : "<p>当前筛选下尚无可直接绘制的同口径金额。可点击学校查看类别标准及待核项目。</p>"}<p class="fine-print">${feeUnit()}。具体适用条件见学校详情，批复、补贴与实际缴费需结合原文核算。</p>`;
  } else if (state.mode === "relations") {
    kicker = "升学关系";
    title = "小学经历如何关联后续申请路径？";
    content = relationsContent();
  } else if (state.mode === "compare") {
    kicker = "同口径比较";
    title =
      state.compareType === "communities"
        ? "猎德与利民的教育供给与入口"
        : `学校比较${state.compare.length ? ` · 已选${state.compare.length}所` : ""}`;
    content = `<div class="compare-type" role="group" aria-label="比较对象类型"><button data-compare-type="schools" aria-pressed="${state.compareType === "schools"}">学校</button><button data-compare-type="communities" aria-pressed="${state.compareType === "communities"}">社区</button><button data-compare-type="timeline" aria-pressed="${state.compareType === "timeline"}">供给时间线</button></div>${state.compareType === "communities" ? communityComparison() : state.compareType === "timeline" ? timeline() : schoolComparison()}`;
  } else if (selected?.id === "E005-032") {
    kicker = "空间不平等";
    title = "一所新园怎样进入利民社区？";
    content = timeline();
  } else if (selected?.lottery) {
    kicker = "制度性分层";
    title = "附近学位通过哪些渠道分配？";
    const records = schools.filter(
      (school) =>
        school.lottery &&
        ["E004-052", "E004-036", "E004-054"].includes(school.id),
    );
    content = `<span class="concept">2026社会派位中的剩余随机计划</span>${miniBars(records, (school) => school.lottery.random, "人")}<p class="fine-print">各园业主优先条件和实际报名人数需一并核验。</p>${sourceButton("E004")}`;
  }
  $("#analysis-kicker").textContent = kicker;
  $("#analysis-title").textContent = title;
  $("#analysis-content").innerHTML = content;
  $("#analysis-content").hidden = !state.expanded;
  $("#analysis-toggle").setAttribute("aria-expanded", String(state.expanded));
  panel.classList.toggle("expanded", state.expanded);
}

function render() {
  document
    .querySelectorAll("[data-mode]")
    .forEach((button) =>
      button.setAttribute(
        "aria-pressed",
        String(button.dataset.mode === state.mode),
      ),
    );
  document
    .querySelectorAll("[data-stage]")
    .forEach((button) =>
      button.setAttribute(
        "aria-pressed",
        String(button.dataset.stage === state.stage),
      ),
    );
  document.querySelectorAll("[data-scene]").forEach((button) => {
    button.classList.toggle(
      "is-active",
      Number(button.dataset.scene) === state.scene,
    );
  });
  $("#family-controls").hidden = state.mode !== "admission";
  $("#fee-controls").hidden = state.mode !== "fees";
  $("#compare-count").hidden = !state.compare.length;
  $("#compare-count").textContent = state.compare.length;
  $("#context-text").textContent =
    `${modeNames[state.mode]} · ${state.stage === "all" ? "三学段" : stageNames[state.stage]}${state.mode === "fees" ? " · " + feeUnit() : state.mode === "relations" ? " · 含关联学段" : ""}`;
  $("#sidebar").classList.toggle("collapsed", state.collapsed);
  $("#atlas").classList.toggle("filters-collapsed", state.collapsed);
  $("#sidebar-toggle").textContent = state.collapsed ? "+" : "−";
  $("#sidebar-toggle").setAttribute("aria-expanded", String(!state.collapsed));
  $("#sidebar-toggle").setAttribute(
    "aria-label",
    state.collapsed ? "展开筛选" : "收起筛选",
  );
  $("#school-search").value = state.query;
  $("#owner-filter").value = state.owner;
  $("#family-hukou").value = state.hukou;
  $("#family-housing").value = state.housing;
  $("#family-integral").checked = state.integral;
  $("#fee-item").value = state.feeItem;
  $("#senior-kindergarten").checked = state.seniorKindergarten;
  renderList();
  renderDetail();
  renderAnalysis();
  createMarkers();
  updateURL();
}

function selectSchool(id, shouldFocus = true) {
  const school = byId.get(id);
  if (!school) return;
  if (!filteredSchools().some((item) => item.id === id)) {
    state.stage = school.stage;
    state.owner = "all";
    state.query = "";
  }
  state.selected = id;
  if (mobile()) state.collapsed = true;
  render();
  if (shouldFocus && school.position) map.focus(school.position.xy);
  if (!school.position)
    notify("官方地址已保存，地图坐标待核。详情中可查看原始资料。");
}

function setMode(mode) {
  state.mode = mode;
  state.scene = null;
  if (mode === "admission") state.detailTab = "admission";
  else if (mode === "fees") {
    state.detailTab = "fees";
    if (state.stage === "all")
      state.stage = byId.get(state.selected)?.stage || "primary";
  } else state.detailTab = "overview";
  if (mode === "relations" && byId.get(state.selected)?.stage === "kg") {
    state.selected = "P06";
    state.stage = "all";
  }
  if (mode === "compare") {
    state.expanded = true;
    state.selected = null;
    state.query = "";
    state.owner = "all";
    if (state.compare.length) state.stage = byId.get(state.compare[0]).stage;
  }
  render();
  const position = byId.get(state.selected)?.position;
  if (position)
    map.focus(
      position.xy,
      mode === "relations" ? 0.24 : Math.max(map.scale, 0.3),
    );
}

function toggleCompare(id) {
  const school = byId.get(id);
  if (state.compare.includes(id))
    state.compare = state.compare.filter((item) => item !== id);
  else {
    if (state.compare.length >= 2)
      return notify("已选两所学校，可先移除一所再添加。");
    const first = byId.get(state.compare[0]);
    if (first && first.stage !== school.stage)
      return notify("请选择同一学段的学校进行比较。");
    state.compare.push(id);
    notify(
      `已加入比较${state.compare.length === 1 ? "，可继续选择另一所同学段学校。" : "，打开“比较”查看。"}`,
    );
  }
  render();
}

function openSources(ids, heading = "资料依据") {
  const sources = [...new Set(ids.split(/[ /,]+/).filter(Boolean))]
    .map((id) => data.sources[id])
    .filter(Boolean);
  $("#source-dialog-content").innerHTML =
    `<div class="dialog-inner"><div class="dialog-header"><h2>${escapeHTML(heading)}</h2><button class="icon-button" data-close-dialog aria-label="关闭资料窗口">×</button></div>
    ${sources.map((source) => `<article class="source-item"><strong>${escapeHTML(source.title)}</strong><small>${escapeHTML(source.id)} · ${escapeHTML(source.date)}</small><p>${escapeHTML(source.note)}</p><a href="${escapeHTML(source.url)}" target="_blank" rel="noopener noreferrer">打开官方原文或原始载体 ↗</a></article>`).join("")}
    <p class="fine-print">研究资料截至2026-11-10。扫描表格、年份与适用对象已在仓库保留原件和核验记录。</p></div>`;
  $("#source-dialog").showModal();
}

function openMethodology() {
  const mapped = schools.filter((school) => school.position).length;
  $("#source-dialog-content").innerHTML =
    `<div class="dialog-inner"><div class="dialog-header"><h2>资料与研究方法</h2><button class="icon-button" data-close-dialog aria-label="关闭资料窗口">×</button></div>
    <div class="dialog-stats"><div><strong>50</strong><small>园区 / 校区学段资料</small></div><div><strong>${mapped}</strong><small>记录有地图参照点</small></div><div><strong>77</strong><small>已归档来源载体</small></div></div>
    <h3>研究范围</h3><p>以猎德街道为主体，保留冼村、天河南、员村等周边候选。地图采用OpenStreetMap的街道参考边界，细尺度社区界线及1/2公里筛选继续核验。</p>
    <h3>空间位置</h3><p>底图和校园参照点来源于OpenStreetMap与Nominatim，获取于2026-11-12。学校面采用几何中心，实际校门和路线待审计。海明学校的地图旧名为“体育东路小学东校区”，别名关联继续核验。</p>
    <h3>制度、费用与解释</h3><p>学校及计划以2026官方名录和招生文件为主，收费采用有效期覆盖当年的政策与批复，具体公示及实缴继续补证。家庭条件是构造情景，申请路径需结合完整材料。计划、报名和实际录取分别按原件核对。</p>
    <h3>社会学解释</h3><p>空间不平等关注设施位置、人口需求和通学负担的差异。制度性分层关注户籍、产权、积分及对口规则如何划分申请路径。社会再生产关注家庭经济和住房资源如何经这些路径影响后续教育机会，实际代际结果需要追踪资料。</p>
    <h3>研究局限</h3><p>同年适龄人口、报名分母、真实家庭预算及现场路线尚缺。当前分析聚焦教育机会条件，学业及职业流动结果需追踪资料。猎德与利民暂定为两社区比较对象。</p>
    <p><a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">© OpenStreetMap contributors · 地理数据按ODbL许可 ↗</a></p>
    <p class="fine-print">本地矢量底图，缩放拖动按需绘制。运行时资料在浏览器内读取，地图无需持续请求远端瓦片。</p>
    ${sourceButton("E002/E003/E004/E030/E039/E052/E054", "查看主要官方依据")}</div>`;
  $("#source-dialog").showModal();
}

function runScene(index) {
  state.scene = index;
  state.query = "";
  state.owner = "all";
  state.compare = [];
  state.stage = "all";
  state.hukou = "tianhe";
  state.housing = "owned";
  state.integral = false;
  state.expanded = index > 0;
  if (index === 0) {
    state.mode = "distribution";
    state.selected = null;
    state.detailTab = "overview";
  } else if (index === 1) {
    state.mode = "admission";
    state.stage = "kg";
    state.selected = "E004-052";
    state.detailTab = "admission";
  } else if (index === 2) {
    state.mode = "admission";
    state.stage = "junior";
    state.selected = "J01";
    state.detailTab = "admission";
    state.hukou = "migrant";
    state.housing = "rented";
    state.integral = true;
  } else if (index === 3) {
    state.mode = "relations";
    state.selected = "P06";
    state.detailTab = "overview";
  } else {
    state.mode = "compare";
    state.selected = null;
    state.compareType = "communities";
  }
  if (mobile()) state.collapsed = true;
  $("#presentation-panel").hidden = true;
  $("#presentation-toggle").setAttribute("aria-expanded", "false");
  render();
  if (state.selected && byId.get(state.selected).position)
    map.focus(byId.get(state.selected).position.xy, index === 3 ? 0.23 : 0.3);
  else map.reset();
}

function bindEvents() {
  document.addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button) return;
    if (button.dataset.school) return selectSchool(button.dataset.school);
    if (button.dataset.mode) return setMode(button.dataset.mode);
    if (button.dataset.stage) {
      state.stage = button.dataset.stage;
      const selected = byId.get(state.selected);
      if (selected && state.stage !== "all" && selected.stage !== state.stage)
        state.selected = null;
      return render();
    }
    if (button.dataset.detailTab) {
      state.detailTab = button.dataset.detailTab;
      return renderDetail();
    }
    if (button.dataset.source) {
      const dialogWasOpen = $("#source-dialog").open;
      if (dialogWasOpen) $("#source-dialog").close();
      return openSources(button.dataset.source);
    }
    if (button.dataset.compare) return toggleCompare(button.dataset.compare);
    if (button.dataset.compareType) {
      state.compareType = button.dataset.compareType;
      return renderAnalysis();
    }
    if (button.hasAttribute("data-close-detail")) {
      state.selected = null;
      return render();
    }
    if (button.hasAttribute("data-close-dialog"))
      return $("#source-dialog").close();
    if (button.hasAttribute("data-activate-admission")) {
      state.collapsed = false;
      return setMode("admission");
    }
    if (button.hasAttribute("data-timeline")) {
      state.compareType = "timeline";
      state.expanded = true;
      state.mode = "compare";
      if (mobile()) state.selected = null;
      return render();
    }
    if (button.hasAttribute("data-focus-limin")) {
      state.selected = "E006-105";
      state.detailTab = "overview";
      render();
      return map.focus(byId.get("E006-105").position.xy);
    }
    if (button.dataset.showRelations) {
      const school = byId.get(button.dataset.showRelations);
      if (school.stage === "kg") {
        state.detailTab = "admission";
        state.mode = "admission";
        state.expanded = true;
        return render();
      }
      state.expanded = true;
      return setMode("relations");
    }
    if (button.dataset.scene !== undefined)
      return runScene(Number(button.dataset.scene));
  });
  $("#connections").addEventListener("click", (event) => {
    if (event.target.dataset.relation)
      openSources("E002", "对口关系与适用条件");
  });
  $("#connections").addEventListener("keydown", (event) => {
    if (["Enter", " "].includes(event.key) && event.target.dataset.relation) {
      event.preventDefault();
      openSources("E002", "对口关系与适用条件");
    }
  });
  $("#school-search").addEventListener("input", (event) => {
    state.query = event.target.value;
    renderList();
    createMarkers();
  });
  $("#owner-filter").addEventListener("change", (event) => {
    state.owner = event.target.value;
    if (
      state.selected &&
      !filteredSchools().some((school) => school.id === state.selected)
    )
      state.selected = null;
    render();
  });
  $("#reset-filters").addEventListener("click", () => {
    state.query = "";
    state.owner = "all";
    state.stage = "all";
    render();
    map.reset();
  });
  $("#boundary-toggle").addEventListener("change", (event) => {
    map.showBoundary = event.target.checked;
    map.requestDraw();
  });
  $("#scope-details-toggle").addEventListener("click", () => {
    const details = $("#scope-details");
    details.hidden = !details.hidden;
    $("#scope-details-toggle").setAttribute(
      "aria-expanded",
      String(!details.hidden),
    );
  });
  $("#fit-boundary").addEventListener("click", () => {
    state.selected = null;
    state.expanded = false;
    state.scene = null;
    if (mobile()) state.collapsed = true;
    map.showBoundary = true;
    $("#boundary-toggle").checked = true;
    $("#scope-details").hidden = true;
    $("#scope-details-toggle").setAttribute("aria-expanded", "false");
    render();
    map.fitStudyArea();
  });
  $("#sidebar-toggle").addEventListener("click", () => {
    state.collapsed = !state.collapsed;
    render();
  });
  $("#analysis-toggle").addEventListener("click", () => {
    state.expanded = !state.expanded;
    renderAnalysis();
    const position = byId.get(state.selected)?.position;
    if (state.expanded && position) map.focus(position.xy);
  });
  for (const [selector, key, checkbox] of [
    ["#family-hukou", "hukou", false],
    ["#family-housing", "housing", false],
    ["#family-integral", "integral", true],
    ["#fee-item", "feeItem", false],
    ["#senior-kindergarten", "seniorKindergarten", true],
  ]) {
    $(selector).addEventListener("change", (event) => {
      state[key] = checkbox ? event.target.checked : event.target.value;
      render();
    });
  }
  $("#zoom-in").addEventListener("click", () =>
    map.zoom(1.35, undefined, undefined, true),
  );
  $("#zoom-out").addEventListener("click", () =>
    map.zoom(1 / 1.35, undefined, undefined, true),
  );
  $("#fit-map").addEventListener("click", () => map.reset());
  $("#brand-home").addEventListener("click", (event) => {
    event.preventDefault();
    runScene(0);
  });
  $("#methodology-open").addEventListener("click", openMethodology);
  $("#presentation-toggle").addEventListener("click", () => {
    const panel = $("#presentation-panel");
    panel.hidden = !panel.hidden;
    $("#presentation-toggle").setAttribute(
      "aria-expanded",
      String(!panel.hidden),
    );
  });
  $("#presentation-close").addEventListener("click", () => {
    $("#presentation-panel").hidden = true;
    $("#presentation-toggle").setAttribute("aria-expanded", "false");
  });
  $("#source-dialog").addEventListener("click", (event) => {
    if (event.target === $("#source-dialog")) $("#source-dialog").close();
  });
  document.addEventListener("keydown", (event) => {
    const tab = event.target.closest('[role="tab"]');
    if (tab && ["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) {
      event.preventDefault();
      const tabs = [...document.querySelectorAll("[data-detail-tab]")];
      const offset = event.key === "ArrowLeft" ? -1 : 1;
      const index =
        event.key === "Home"
          ? 0
          : event.key === "End"
            ? tabs.length - 1
            : (tabs.indexOf(tab) + offset + tabs.length) % tabs.length;
      state.detailTab = tabs[index].dataset.detailTab;
      renderDetail();
      document.querySelector(`[data-detail-tab="${state.detailTab}"]`).focus();
    }
    if (
      event.key === "/" &&
      !/INPUT|SELECT|TEXTAREA/.test(event.target.tagName) &&
      !$("#source-dialog").open
    ) {
      event.preventDefault();
      state.collapsed = false;
      render();
      $("#school-search").focus();
    }
    if (event.key === "Escape" && !$("#source-dialog").open) {
      state.selected = null;
      $("#presentation-panel").hidden = true;
      $("#scope-details").hidden = true;
      $("#scope-details-toggle").setAttribute("aria-expanded", "false");
      $("#presentation-toggle").setAttribute("aria-expanded", "false");
      render();
    }
  });
}

async function start() {
  try {
    const responses = await Promise.all([
      fetch("./assets/schools.json"),
      fetch("./assets/basemap.json"),
    ]);
    for (const response of responses)
      if (!response.ok) throw new Error(`资料读取失败 ${response.status}`);
    const [dataset, geography] = await Promise.all(
      responses.map((response) => response.json()),
    );
    data = dataset;
    schools = dataset.schools;
    byId = new Map(schools.map((school) => [school.id, school]));
    if (state.selected && !byId.has(state.selected)) state.selected = null;
    $("#presentation-scenes").innerHTML = sceneNames
      .map(
        (title, index) =>
          `<button data-scene="${index}"><span class="scene-number">0${index + 1}</span><span>${title}</span></button>`,
      )
      .join("");
    map = new AtlasMap(
      $("#map-surface"),
      $("#basemap"),
      geography,
      positionMarkers,
    );
    for (const school of schools)
      school.areaLabel = school.position
        ? map.containsStudyArea(school.position.xy)
          ? "猎德街道参照界内"
          : "周边参照点"
        : "范围待核";
    const mapped = schools.filter((school) => school.position);
    const inside = mapped.filter((school) =>
      map.containsStudyArea(school.position.xy),
    ).length;
    $("#study-area-count").textContent =
      `按校园参照点与该边界判断，${mapped.length}条已定位资料中${inside}条在界内，${mapped.length - inside}条在周边。其余${schools.length - mapped.length}条的范围待核。`;
    if (map.studyArea) $("#boundary-source").href = map.studyArea.url;
    bindEvents();
    render();
    map.reset(false);
    const initialPosition = byId.get(state.selected)?.position;
    if (params.has("school") && initialPosition) map.focus(initialPosition.xy);
    $("#map-loading").hidden = true;
  } catch (error) {
    $("#map-loading").innerHTML =
      `<div class="empty-state"><strong>地图资料暂未读取</strong><p>${escapeHTML(error.message)}</p><button class="secondary-button" onclick="location.reload()">重新加载</button></div>`;
    console.error(error);
  }
}

start();
