const EARTH_RADIUS = 6378137;
const ORIGIN_LATITUDE = (23.121 * Math.PI) / 180;
const ORIGIN_MERCATOR = Math.log(Math.tan(Math.PI / 4 + ORIGIN_LATITUDE / 2));

export function project(lon, lat) {
  return [
    (EARTH_RADIUS * (lon - 113.332) * Math.PI) / 180,
    EARTH_RADIUS *
      (ORIGIN_MERCATOR -
        Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360))),
  ];
}

function addLine(path, coordinates, close = false) {
  if (!coordinates.length) return;
  path.moveTo(coordinates[0][0], coordinates[0][1]);
  for (const [x, y] of coordinates.slice(1)) path.lineTo(x, y);
  if (close) path.closePath();
}

export class AtlasMap {
  constructor(surface, canvas, geography, onView) {
    this.surface = surface;
    this.canvas = canvas;
    this.context = canvas.getContext("2d", { alpha: false });
    this.onView = onView;
    this.center = [0, 0];
    this.scale = 0.2;
    this.showBoundary = true;
    this.frame = null;
    this.pointers = new Map();
    this.labels = geography.labels;
    this.bounds = geography.bounds;
    this.roads = new Map();
    for (const [kind, coordinates] of geography.roads) {
      if (!this.roads.has(kind)) this.roads.set(kind, new Path2D());
      addLine(this.roads.get(kind), coordinates);
    }
    this.parks = new Path2D();
    for (const coordinates of geography.parks)
      addLine(this.parks, coordinates, true);
    this.waters = geography.water.map((rings) => {
      const path = new Path2D();
      for (const ring of rings) addLine(path, ring, true);
      return path;
    });
    this.boundaries = geography.boundaries.map((boundary) => {
      const path = new Path2D();
      for (const ring of boundary.rings) addLine(path, ring, true);
      return { ...boundary, path };
    });
    this.studyArea = this.boundaries.find(
      (boundary) => boundary.name === "猎德街道",
    );
    this.outsideStudyArea = new Path2D();
    this.outsideStudyArea.rect(-100000, -100000, 200000, 200000);
    if (this.studyArea) this.outsideStudyArea.addPath(this.studyArea.path);
    this.observe = new ResizeObserver(() => this.resize());
    this.observe.observe(surface);
    this.bindGestures();
    this.resize();
    this.reset(false);
  }

  resize() {
    const bounds = this.surface.getBoundingClientRect();
    this.width = bounds.width;
    this.height = bounds.height;
    // Limit the backing bitmap on high-density and large displays.
    this.ratio = Math.min(
      window.devicePixelRatio || 1,
      1.75,
      Math.sqrt(4000000 / Math.max(this.width * this.height, 1)),
    );
    this.canvas.width = Math.round(this.width * this.ratio);
    this.canvas.height = Math.round(this.height * this.ratio);
    this.requestDraw();
  }

  constrain() {
    const [low, high] = this.bounds;
    this.minimumScale = Math.max(
      this.width / (high[0] - low[0]),
      this.height / (high[1] - low[1]),
    );
    if (this.overviewScale)
      this.minimumScale = Math.min(this.minimumScale, this.overviewScale);
    this.scale = Math.max(this.minimumScale, Math.min(1.8, this.scale));
    const halfWidth = this.width / (2 * this.scale);
    const halfHeight = this.height / (2 * this.scale);
    const marginX = this.overviewScale ? 0 : halfWidth;
    const marginY = this.overviewScale ? 0 : halfHeight;
    this.center[0] =
      marginX * 2 >= high[0] - low[0]
        ? (low[0] + high[0]) / 2
        : Math.max(
            low[0] + marginX,
            Math.min(high[0] - marginX, this.center[0]),
          );
    this.center[1] =
      marginY * 2 >= high[1] - low[1]
        ? (low[1] + high[1]) / 2
        : Math.max(
            low[1] + marginY,
            Math.min(high[1] - marginY, this.center[1]),
          );
  }

  screen(point) {
    return [
      (point[0] - this.center[0]) * this.scale + this.width / 2,
      (point[1] - this.center[1]) * this.scale + this.height / 2,
    ];
  }

  world(x, y) {
    return [
      (x - this.width / 2) / this.scale + this.center[0],
      (y - this.height / 2) / this.scale + this.center[1],
    ];
  }

  requestDraw() {
    if (this.frame !== null) return;
    this.frame = requestAnimationFrame(() => {
      this.frame = null;
      this.draw();
      this.onView?.();
    });
  }

  draw() {
    this.constrain();
    const ctx = this.context;
    const { ratio, scale, width, height } = this;
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    ctx.fillStyle = "#f0f1e8";
    ctx.fillRect(0, 0, width, height);
    ctx.setTransform(
      ratio * scale,
      0,
      0,
      ratio * scale,
      ratio * (width / 2 - this.center[0] * scale),
      ratio * (height / 2 - this.center[1] * scale),
    );
    ctx.fillStyle = "#dfe7d5";
    ctx.fill(this.parks);
    ctx.fillStyle = "#cfdfda";
    for (const path of this.waters) ctx.fill(path, "evenodd");
    ctx.lineJoin = "round";
    ctx.lineCap = "round";
    const styles = {
      service: [1.2, "#e7e9dd"],
      footway: [0.6, "#e4e7d9"],
      pedestrian: [2.1, "#f8f8ef"],
      residential: [2.7, "#fbfbf4"],
      tertiary: [3.5, "#fbfbf4"],
      secondary: [5.0, "#fcfcf7"],
      primary: [5.7, "#fcfcf7"],
      trunk: [6.0, "#fcfcf7"],
      motorway: [6.5, "#fcfcf7"],
    };
    for (const [kind, [lineWidth, color]] of Object.entries(styles)) {
      const path = this.roads.get(kind);
      if (!path || (kind === "footway" && scale < 0.32)) continue;
      if (
        ["tertiary", "secondary", "primary", "trunk", "motorway"].includes(kind)
      ) {
        ctx.strokeStyle = "#dce1d2";
        ctx.lineWidth = (lineWidth + 1.1) / scale;
        ctx.stroke(path);
      }
      ctx.strokeStyle = color;
      ctx.lineWidth = lineWidth / scale;
      ctx.stroke(path);
    }
    if (this.showBoundary && this.studyArea) {
      ctx.fillStyle = "#34493710";
      ctx.fill(this.outsideStudyArea, "evenodd");
      ctx.fillStyle = "#36775929";
      ctx.fill(this.studyArea.path, "evenodd");
      ctx.strokeStyle = "#faf9f4";
      ctx.lineWidth = 5 / scale;
      ctx.stroke(this.studyArea.path);
      ctx.strokeStyle = "#39765a";
      ctx.lineWidth = 2 / scale;
      ctx.setLineDash([8 / scale, 4 / scale]);
      ctx.stroke(this.studyArea.path);
      ctx.setLineDash([]);
    }
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    this.drawLabels(ctx);
    const meters = width < 600 ? 200 : 500;
    const scaleElement = document.getElementById("map-scale");
    scaleElement.style.width = `${(meters * scale) / Math.cos(ORIGIN_LATITUDE)}px`;
    scaleElement.textContent = `${meters} m`;
  }

  drawLabels(ctx) {
    const placed = [];
    const named = new Set();
    const labels = [
      ...this.labels.filter((label) => label.kind === "park"),
      ...this.labels.filter((label) => label.kind === "road"),
    ];
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    for (const label of labels) {
      const [x, y] = this.screen(label.xy);
      if (x < 30 || y < 105 || x > this.width - 30 || y > this.height - 55)
        continue;
      if (named.has(label.name)) continue;
      const park = label.kind === "park";
      const minDistance = park ? 55 : 82;
      if (
        placed.some(
          (point) => Math.hypot(point[0] - x, point[1] - y) < minDistance,
        )
      )
        continue;
      ctx.font = `${park ? 12 : 10}px -apple-system, "PingFang SC", sans-serif`;
      ctx.fillStyle = park ? "#839475" : "#a5ac9b";
      ctx.fillText(label.name, x, y);
      placed.push([x, y]);
      named.add(label.name);
    }
    const [x, y] = this.screen(project(113.332, 23.1125));
    ctx.font = 'italic 18px Georgia, "Songti SC", serif';
    ctx.fillStyle = "#8ca8a0";
    ctx.fillText("珠  江", x, y);
    ctx.font = "9px sans-serif";
    ctx.fillText("PEARL RIVER", x, y + 24);
  }

  changeView(center, scale, animate = true) {
    scale = Math.max(this.minimumScale || 0.065, Math.min(1.8, scale));
    const shouldAnimate =
      animate && !matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (this.animation) cancelAnimationFrame(this.animation);
    this.animation = null;
    if (!shouldAnimate) {
      this.center = center;
      this.scale = scale;
      this.requestDraw();
      return;
    }
    const startCenter = [...this.center];
    const startScale = this.scale;
    const started = performance.now();
    const tick = (now) => {
      const progress = Math.min(1, (now - started) / 320);
      const eased = 1 - (1 - progress) ** 3;
      this.center = startCenter.map(
        (value, index) => value + (center[index] - value) * eased,
      );
      this.scale = startScale + (scale - startScale) * eased;
      this.requestDraw();
      this.animation = progress < 1 ? requestAnimationFrame(tick) : null;
    };
    this.animation = requestAnimationFrame(tick);
  }

  zoom(factor, x = this.width / 2, y = this.height / 2, animate = false) {
    const anchor = this.world(x, y);
    const scale = Math.max(
      this.minimumScale || 0.065,
      Math.min(1.8, this.scale * factor),
    );
    const center = [
      anchor[0] - (x - this.width / 2) / scale,
      anchor[1] - (y - this.height / 2) / scale,
    ];
    this.changeView(center, scale, animate);
  }

  focus(point, zoom = Math.max(this.scale, 0.3)) {
    let anchorX, anchorY;
    if (this.width <= 900) {
      anchorX = this.width / 2;
      anchorY = Math.max(265, this.height * 0.34);
    } else {
      const left = this.width > 1600 ? 360 : this.width > 1150 ? 320 : 280;
      const right = document.getElementById("detail-panel").hidden
        ? 60
        : this.width > 1150
          ? 380
          : 330;
      anchorX = left + (this.width - left - right) / 2;
      anchorY = this.height * 0.47;
      const analysis = document.getElementById("analysis-panel");
      if (analysis.classList.contains("expanded"))
        anchorY = Math.min(
          anchorY,
          (190 + analysis.getBoundingClientRect().top) / 2,
        );
    }
    this.changeView(
      [
        point[0] - (anchorX - this.width / 2) / zoom,
        point[1] - (anchorY - this.height / 2) / zoom,
      ],
      zoom,
    );
  }

  reset(animate = true) {
    this.overviewScale = null;
    const left = this.width <= 900 ? 25 : this.width > 1150 ? 330 : 280;
    const right =
      this.width <= 900
        ? 25
        : document.getElementById("detail-panel").hidden
          ? 70
          : 380;
    const low = project(113.31, 23.133);
    const high = project(113.353, 23.11);
    const availableWidth = Math.max(300, this.width - left - right);
    const scale = Math.min(
      availableWidth / (high[0] - low[0]),
      Math.max(this.height - 300, 250) / (high[1] - low[1]),
    );
    const anchorX = left + availableWidth / 2;
    const center = [
      (low[0] + high[0]) / 2 - (anchorX - this.width / 2) / scale,
      (low[1] + high[1]) / 2,
    ];
    this.changeView(center, scale, animate);
  }

  containsStudyArea(point) {
    let inside = false;
    for (const ring of this.studyArea?.rings || []) {
      for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
        const first = ring[i],
          second = ring[j];
        if (
          first[1] > point[1] !== second[1] > point[1] &&
          point[0] <
            ((second[0] - first[0]) * (point[1] - first[1])) /
              (second[1] - first[1]) +
              first[0]
        )
          inside = !inside;
      }
    }
    return inside;
  }

  fitStudyArea(animate = true) {
    if (!this.studyArea) return;
    const points = this.studyArea.rings.flat();
    const low = [
      Math.min(...points.map((point) => point[0])),
      Math.min(...points.map((point) => point[1])),
    ];
    const high = [
      Math.max(...points.map((point) => point[0])),
      Math.max(...points.map((point) => point[1])),
    ];
    const narrow = this.width <= 900;
    const left = narrow
      ? 28
      : document.getElementById("sidebar").getBoundingClientRect().right + 30;
    const right = this.width - (narrow ? 28 : 80);
    const top = narrow ? 350 : 270;
    const bottom = this.height - (narrow ? 145 : 150);
    const scale = Math.min(
      (right - left) / (high[0] - low[0]),
      Math.max(bottom - top, 160) / (high[1] - low[1]),
    );
    this.overviewScale = scale;
    this.minimumScale = scale;
    this.changeView(
      [
        (low[0] + high[0]) / 2 - ((left + right) / 2 - this.width / 2) / scale,
        (low[1] + high[1]) / 2 - ((top + bottom) / 2 - this.height / 2) / scale,
      ],
      scale,
      animate,
    );
  }

  bindGestures() {
    this.surface.addEventListener(
      "wheel",
      (event) => {
        event.preventDefault();
        const bounds = this.surface.getBoundingClientRect();
        this.zoom(
          Math.exp(-Math.max(-120, Math.min(120, event.deltaY)) * 0.002),
          event.clientX - bounds.left,
          event.clientY - bounds.top,
        );
      },
      { passive: false },
    );
    this.surface.addEventListener("pointerdown", (event) => {
      if (
        event.target.closest('button, a, [role="button"]') ||
        event.button > 0
      )
        return;
      if (this.animation) cancelAnimationFrame(this.animation);
      this.pointers.set(event.pointerId, [event.clientX, event.clientY]);
      this.surface.setPointerCapture(event.pointerId);
      this.surface.classList.add("is-dragging");
    });
    this.surface.addEventListener("pointermove", (event) => {
      const previous = this.pointers.get(event.pointerId);
      if (!previous) return;
      if (this.pointers.size === 1) {
        this.center[0] -= (event.clientX - previous[0]) / this.scale;
        this.center[1] -= (event.clientY - previous[1]) / this.scale;
        this.pointers.set(event.pointerId, [event.clientX, event.clientY]);
        this.requestDraw();
      } else {
        const other = [...this.pointers.entries()].find(
          ([id]) => id !== event.pointerId,
        )[1];
        const oldDistance = Math.hypot(
          previous[0] - other[0],
          previous[1] - other[1],
        );
        const newDistance = Math.hypot(
          event.clientX - other[0],
          event.clientY - other[1],
        );
        if (oldDistance > 5)
          this.zoom(
            newDistance / oldDistance,
            (other[0] + event.clientX) / 2,
            (other[1] + event.clientY) / 2,
          );
        this.pointers.set(event.pointerId, [event.clientX, event.clientY]);
      }
    });
    const release = (event) => {
      this.pointers.delete(event.pointerId);
      if (!this.pointers.size) this.surface.classList.remove("is-dragging");
    };
    this.surface.addEventListener("pointerup", release);
    this.surface.addEventListener("pointercancel", release);
    this.surface.addEventListener("dblclick", (event) => {
      if (event.target.closest('button, a, [role="button"]')) return;
      this.zoom(1.5, event.clientX, event.clientY, true);
    });
    this.surface.addEventListener("keydown", (event) => {
      if (event.target !== this.surface) return;
      const directions = {
        ArrowLeft: [-60, 0],
        ArrowRight: [60, 0],
        ArrowUp: [0, -60],
        ArrowDown: [0, 60],
      };
      if (directions[event.key]) {
        event.preventDefault();
        const delta = directions[event.key];
        this.changeView(
          [
            this.center[0] + delta[0] / this.scale,
            this.center[1] + delta[1] / this.scale,
          ],
          this.scale,
          false,
        );
      }
      if (event.key === "+" || event.key === "=") this.zoom(1.3);
      if (event.key === "-") this.zoom(1 / 1.3);
    });
  }
}
