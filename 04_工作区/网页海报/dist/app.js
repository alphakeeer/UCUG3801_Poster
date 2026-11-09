"use strict";

const communityHours = [
  [[9, 18]],
  [[9, 18]],
  [[9, 18]],
  [[9, 18]],
  [[9, 18]],
  [[9, 12]],
  [],
];
const stationHours = Array.from({ length: 7 }, () => [
  [9, 12],
  [14, 18],
]);
const facilities = [
  {
    id: "liede",
    name: "猎德社区中心",
    level: "社区级",
    address: "海文路16号103铺之一",
    hours: communityHours,
    description: "周一至周五9–18时，周六9–12时",
  },
  {
    id: "limin",
    name: "利民社区中心",
    level: "社区级",
    address: "兴民路214号二楼",
    hours: communityHours,
    description: "周一至周五9–18时，周六9–12时",
  },
  {
    id: "station",
    name: "猎德街文化站",
    level: "街道级",
    address: "海文路33号1楼",
    hours: stationHours,
    description: "每日9–12时、14–18时",
  },
];
const dayNames = ["一", "二", "三", "四", "五", "六", "日"];

function sumHours(days) {
  return days.reduce(
    (total, periods) =>
      total + periods.reduce((sum, [start, end]) => sum + end - start, 0),
    0,
  );
}

function svgElement(name, attributes, text) {
  const element = document.createElementNS("http://www.w3.org/2000/svg", name);
  for (const [key, value] of Object.entries(attributes))
    element.setAttribute(key, value);
  if (text !== undefined) element.textContent = text;
  return element;
}

function renderSchedule(facility) {
  const card = document.createElement("div");
  card.className = "schedule-facility";
  const heading = document.createElement("h3");
  heading.className = "facility-name";
  heading.textContent = facility.name;
  const level = document.createElement("small");
  level.textContent = facility.level;
  heading.append(level);
  card.append(heading);

  const chart = svgElement("svg", {
    viewBox: "0 0 275 182",
    class: "weekly-chart",
    role: "img",
    "aria-label": `${facility.name}，${facility.description}，每周${sumHours(facility.hours)}小时，周末${sumHours(facility.hours.slice(5))}小时`,
  });
  const cellWidth = 18;
  const cellGap = 2;
  const chartStart = 30;
  facility.hours.forEach((periods, day) => {
    const y = day * 23;
    chart.append(
      svgElement(
        "text",
        { x: 4, y: y + 12, class: "chart-day" },
        dayNames[day],
      ),
    );
    for (let hour = 9; hour < 21; hour += 1) {
      const available = periods.some(
        ([start, end]) => hour >= start && hour < end,
      );
      const cell = svgElement("rect", {
        x: chartStart + (hour - 9) * (cellWidth + cellGap),
        y,
        width: cellWidth,
        height: 16,
        rx: 1,
        class: available
          ? `chart-available ${facility.id === "station" ? "station" : ""}`
          : "chart-background",
      });
      cell.append(
        svgElement(
          "title",
          {},
          `星期${dayNames[day]} ${hour}–${hour + 1}时，${available ? "公布开放时段" : "目录未列常规开放"}`,
        ),
      );
      chart.append(cell);
    }
  });
  for (const hour of [9, 12, 15, 18, 21]) {
    chart.append(
      svgElement(
        "text",
        {
          x: chartStart + (hour - 9) * (cellWidth + cellGap),
          y: 179,
          class: "chart-tick",
          "text-anchor": hour === 21 ? "end" : "start",
        },
        String(hour).padStart(2, "0"),
      ),
    );
  }
  card.append(chart);
  const totals = document.createElement("div");
  totals.className = "schedule-totals";
  const total = document.createElement("strong");
  total.textContent = sumHours(facility.hours);
  const unit = document.createElement("span");
  unit.textContent = "小时 / 周";
  const weekend = document.createElement("span");
  weekend.className = "weekend-label";
  weekend.append("周末 ");
  const weekendNumber = document.createElement("b");
  weekendNumber.textContent = sumHours(facility.hours.slice(5));
  weekend.append(weekendNumber, " h");
  totals.append(total, unit, weekend);
  card.append(totals);
  return card;
}

document
  .getElementById("schedule-grid")
  .append(...facilities.map(renderSchedule));

for (const facility of facilities) {
  document
    .querySelectorAll(`[data-weekly="${facility.id}"]`)
    .forEach((element) => {
      element.textContent = sumHours(facility.hours);
    });
  document
    .querySelectorAll(`[data-weekend="${facility.id}"]`)
    .forEach((element) => {
      element.textContent = sumHours(facility.hours.slice(5));
    });
  const row = document.createElement("tr");
  for (const value of [
    facility.name,
    facility.description,
    `${sumHours(facility.hours)}小时`,
    `${sumHours(facility.hours.slice(5))}小时`,
  ]) {
    const cell = document.createElement("td");
    cell.textContent = value;
    row.append(cell);
  }
  document.getElementById("data-table-body").append(row);
}

function selectScenario(scenario) {
  const [availableStart, availableEnd] =
    scenario === "day" ? [10, 12] : [19, 21];
  const dailyOverlap = communityHours
    .slice(0, 5)
    .map((periods) =>
      periods.reduce(
        (total, [start, end]) =>
          total +
          Math.max(
            0,
            Math.min(end, availableEnd) - Math.max(start, availableStart),
          ),
        0,
      ),
    );
  document.getElementById("overlap-hours").textContent = dailyOverlap.reduce(
    (sum, hours) => sum + hours,
    0,
  );
  const bars = document.getElementById("scenario-bars");
  bars.replaceChildren();
  dailyOverlap.forEach((hours, day) => {
    const row = document.createElement("div");
    row.className = "scenario-bar-row";
    const label = document.createElement("span");
    label.textContent = `周${dayNames[day]}`;
    const track = document.createElement("div");
    track.className = "scenario-bar-track";
    const fill = document.createElement("div");
    fill.className = "scenario-bar-fill";
    fill.style.width = `${(hours / 2) * 100}%`;
    track.append(fill);
    const number = document.createElement("b");
    number.textContent = `${hours} h`;
    row.append(label, track, number);
    bars.append(row);
  });
  document.querySelectorAll("[data-scenario]").forEach((button) => {
    const selected = button.dataset.scenario === scenario;
    button.classList.toggle("selected", selected);
    button.setAttribute("aria-pressed", String(selected));
  });
}

document
  .querySelectorAll("[data-scenario]")
  .forEach((button) =>
    button.addEventListener("click", () =>
      selectScenario(button.dataset.scenario),
    ),
  );
selectScenario("day");

function resizePoster() {
  const scale = Math.min(1, (window.innerWidth - 96) / 1080);
  document.documentElement.style.setProperty("--poster-scale", scale);
}

window.addEventListener("resize", resizePoster);
resizePoster();
