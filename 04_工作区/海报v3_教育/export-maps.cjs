"use strict";
// 导出 map-lab/index.html 里的每个地图方案（.block）为 2 倍 PNG：previews/map-<id>.png
const fs = require("node:fs/promises");
const http = require("node:http");
const path = require("node:path");
const { chromium } = require(path.join(__dirname, "../海报v2/node_modules/playwright"));
const ROOT = path.resolve(__dirname, "..");
const TYPES = { ".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "text/javascript", ".jpg": "image/jpeg", ".png": "image/png", ".otf": "font/otf", ".ttf": "font/ttf" };
(async () => {
  const server = http.createServer(async (req, res) => {
    const file = path.join(ROOT, decodeURIComponent(new URL(req.url, "http://x").pathname));
    try { res.writeHead(200, { "content-type": TYPES[path.extname(file)] || "application/octet-stream" }).end(await fs.readFile(file)); }
    catch { res.writeHead(404).end(); }
  });
  await new Promise((r) => server.listen(0, "127.0.0.1", r));
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1200 }, deviceScaleFactor: 2 });
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("response", (r) => r.status() >= 400 && errors.push(`${r.status()} ${r.url()}`));
  await page.goto(`http://127.0.0.1:${server.address().port}/${path.basename(__dirname)}/map-lab/index.html`, { waitUntil: "networkidle" });
  await page.waitForSelector("body[data-ready='1']", { timeout: 60000 });
  await page.screenshot({ path: path.join(__dirname, "previews/map-lab.png"), fullPage: true });
  for (const el of await page.locator(".block").all()) {
    const id = await el.getAttribute("id");
    await el.screenshot({ path: path.join(__dirname, `previews/map-${id}.png`) });
    console.log("✓ map-" + id);
  }
  errors.forEach((e) => console.log("  ✗ " + e));
  await browser.close(); server.close();
})();
