"use strict";

/*
 * 数据：《天河区公共文化设施目录》2026-05-22 版（S23），
 * 与 03_背景/数据/03_猎德街8项设施_开放时段与面积.csv 一致。
 * 图1 的开放时段、空闲情景与三项统计都由下面同一组数据计算。
 */
const SCHEDULE = {
  // 周一至周五 9–18，周六 9–12，周日无常规时段
  community: [[[9, 18]], [[9, 18]], [[9, 18]], [[9, 18]], [[9, 18]], [[9, 12]], []],
  // 每天 9–12、14–18
  station: Array.from({ length: 7 }, () => [[9, 12], [14, 18]]),
};

// 假设情景：朝九晚六上班族（含通勤）的空闲时段，工作日 19–22，周末 9–22
const FREE = [[[19, 22]], [[19, 22]], [[19, 22]], [[19, 22]], [[19, 22]], [[9, 22]], [[9, 22]]];

const DAYS = ["一", "二", "三", "四", "五", "六", "日"];
const H0 = 7;
const H1 = 23;

const overlap = (a, b) =>
  a.reduce(
    (sum, [s1, e1]) =>
      sum + b.reduce((t, [s2, e2]) => t + Math.max(0, Math.min(e1, e2) - Math.max(s1, s2)), 0),
    0,
  );

function stats() {
  const after18 = Object.values(SCHEDULE).reduce(
    (sum, week) => sum + week.slice(0, 5).reduce((t, day) => t + overlap(day, [[18, 24]]), 0),
    0,
  );
  const weeklyOverlap = (week) => week.reduce((t, day, i) => t + overlap(day, FREE[i]), 0);
  return {
    after18,
    overlapCommunity: weeklyOverlap(SCHEDULE.community),
    overlapStation: weeklyOverlap(SCHEDULE.station),
  };
}

const NS = "http://www.w3.org/2000/svg";
function el(name, attrs, parent) {
  const node = document.createElementNS(NS, name);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  if (parent) parent.appendChild(node);
  return node;
}

function drawWeek(svg, week) {
  const W = 452;
  const left = 26;
  const top = 4;
  const rowH = 16;
  const gap = 4;
  const plotW = W - left - 4;
  const x = (h) => left + ((h - H0) / (H1 - H0)) * plotW;
  const H = top + DAYS.length * (rowH + gap) + 22;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);

  const defs = el("defs", {}, svg);
  const pat = el("pattern", { id: `hatch-${svg.id}`, width: 6, height: 6, patternUnits: "userSpaceOnUse", patternTransform: "rotate(45)" }, defs);
  el("rect", { width: 6, height: 6, fill: "var(--red-wash)" }, pat);
  el("line", { x1: 0, y1: 0, x2: 0, y2: 6, stroke: "var(--red)", "stroke-width": 1.4, opacity: 0.55 }, pat);

  // 18:00 参考线
  el("line", { x1: x(18), x2: x(18), y1: 0, y2: H - 18, class: "ref-line" }, svg);

  DAYS.forEach((d, i) => {
    const y = top + i * (rowH + gap);
    el("text", { x: 0, y: y + rowH / 2 + 5, class: "day" }, svg).textContent = d;
    el("rect", { x: x(H0), y, width: plotW, height: rowH, class: "track" }, svg);
    for (const [s, e] of FREE[i]) {
      el("rect", { x: x(s), y, width: x(e) - x(s), height: rowH, fill: `url(#hatch-${svg.id})` }, svg);
    }
    for (const [s, e] of week[i]) {
      el("rect", { x: x(s) + 0.5, y, width: x(e) - x(s) - 1, height: rowH, class: "open" }, svg);
      for (const [fs, fe] of FREE[i]) {
        const a = Math.max(s, fs);
        const b = Math.min(e, fe);
        if (b > a) el("rect", { x: x(a) + 0.5, y, width: x(b) - x(a) - 1, height: rowH, class: "hit" }, svg);
      }
    }
  });

  const axisY = H - 4;
  for (let h = 9; h <= 21; h += 3) {
    el("text", { x: x(h), y: axisY, class: "tick", "text-anchor": "middle" }, svg).textContent = `${h}:00`;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".week").forEach((fig, i) => {
    const svg = fig.querySelector("svg");
    svg.id = `week-${i}`;
    drawWeek(svg, SCHEDULE[fig.dataset.kind]);
  });
  const s = stats();
  document.querySelectorAll("[data-stat]").forEach((node) => {
    node.textContent = s[node.dataset.stat];
  });
  document.body.dataset.ready = "1";
});
