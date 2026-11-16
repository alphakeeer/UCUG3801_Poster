"use strict";
// 渲染 designs/*/index.html，导出预览 PNG（2160×3840）并检查内容是否溢出画布。
// 用法：node export.cjs [方案字母...]，例如 node export.cjs a c；加 --pdf 同时导出 PDF。
const fs = require("node:fs/promises");
const http = require("node:http");
const path = require("node:path");
const { chromium } = require(path.join(__dirname, "../海报v2/node_modules/playwright"));

const ROOT = path.resolve(__dirname, ".."); // 04_工作区：可同时读取 海报v2/fonts-src
const SELF = path.basename(__dirname);
const OUT = path.join(__dirname, "previews");
const TYPES = { ".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "text/javascript", ".jpg": "image/jpeg", ".png": "image/png", ".otf": "font/otf", ".ttf": "font/ttf", ".woff2": "font/woff2" };

const serve = () =>
  http.createServer(async (req, res) => {
    const rel = decodeURIComponent(new URL(req.url, "http://x").pathname).replace(/^\/+/, "");
    const file = path.join(ROOT, rel);
    if (!file.startsWith(ROOT)) return res.writeHead(403).end();
    try {
      res.writeHead(200, { "content-type": TYPES[path.extname(file)] || "application/octet-stream" }).end(await fs.readFile(file));
    } catch {
      res.writeHead(404).end();
    }
  });

async function main() {
  const args = process.argv.slice(2);
  const pdf = args.includes("--pdf");
  const all = (await fs.readdir(path.join(__dirname, "designs"))).filter((d) => !d.startsWith("."));
  const pick = args.filter((a) => !a.startsWith("--"));
  const designs = pick.length ? all.filter((d) => pick.some((p) => d.startsWith(p))) : all;
  const server = serve();
  await new Promise((r) => server.listen(0, "127.0.0.1", r));
  const browser = await chromium.launch();
  await fs.mkdir(OUT, { recursive: true });
  let failed = false;
  try {
    for (const d of designs) {
      const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 2 });
      const errors = [];
      page.on("pageerror", (e) => errors.push(e.message));
      page.on("requestfailed", (r) => errors.push("load failed: " + r.url()));
      page.on("response", (r) => r.status() >= 400 && errors.push(`${r.status()} ${r.url()}`));
      await page.goto(`http://127.0.0.1:${server.address().port}/${SELF}/designs/${d}/index.html`, { waitUntil: "networkidle" });
      await page.waitForSelector("body[data-ready='1']", { timeout: 60000 });
      // 检查：海报整体和每个 [data-fit] 区块都不得溢出
      const report = await page.evaluate(() => {
        const p = document.getElementById("poster");
        const out = [];
        if (p.scrollHeight > p.clientHeight + 1) out.push(`poster ${p.scrollHeight}/${p.clientHeight}`);
        const pb = p.getBoundingClientRect().bottom;
        document.querySelectorAll("#poster *").forEach((el) => {
          const b = el.getBoundingClientRect();
          if (el.closest("svg")) return;
          if (b.height && b.bottom > pb + 1) out.push(`below poster: ${el.className || el.tagName} (+${Math.round(b.bottom - pb)})`);
        });
        document.querySelectorAll("[data-fit]").forEach((el) => {
          if (el.scrollHeight > el.clientHeight + 1 || el.scrollWidth > el.clientWidth + 1)
            out.push(`overflow ${el.dataset.fit}: ${el.scrollHeight}/${el.clientHeight}h ${el.scrollWidth}/${el.clientWidth}w`);
        });
        const last = [...p.children].at(-1).getBoundingClientRect();
        const parts = [...p.children].map((c) => `${(c.className || c.tagName).split(" ")[0]}:${Math.round(c.getBoundingClientRect().height)}`).join(" ");
        return { issues: [...new Set(out)].slice(0, 6), slack: Math.round(pb - last.bottom), parts };
      });
      const png = path.join(OUT, `${d}.png`);
      await page.locator("#poster").screenshot({ path: png, animations: "disabled" });
      if (pdf) {
        await page.emulateMedia({ media: "print" });
        await page.pdf({ path: path.join(OUT, `${d}.pdf`), printBackground: true, preferCSSPageSize: true });
      }
      const bad = errors.length || report.issues.length;
      failed ||= bad;
      console.log(`${bad ? "✗" : "✓"} ${d}  slack ${report.slack}px\n   ${report.parts}`);
      [...errors, ...report.issues].forEach((m) => console.log("   " + m));
      await page.close();
    }
  } finally {
    await browser.close();
    server.close();
  }
  if (failed) process.exitCode = 1;
}
main().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
