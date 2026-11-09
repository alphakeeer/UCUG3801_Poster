"use strict";

// Render src/index.html and export a 3240×5760 PNG and a single-page PDF.
const fs = require("node:fs/promises");
const http = require("node:http");
const path = require("node:path");
const { chromium } = require("playwright");

const SRC = path.join(__dirname, "src");
const OUT = path.resolve(__dirname, "../../05_提交/poster_final");
const TYPES = { ".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "text/javascript", ".jpg": "image/jpeg", ".woff2": "font/woff2" };

function serve() {
  return http.createServer(async (req, res) => {
    const rel = decodeURIComponent(new URL(req.url, "http://x").pathname).replace(/^\/+/, "") || "index.html";
    const file = path.join(SRC, rel);
    if (!file.startsWith(SRC)) return res.writeHead(403).end();
    try {
      const body = await fs.readFile(file);
      res.writeHead(200, { "content-type": TYPES[path.extname(file)] || "application/octet-stream" }).end(body);
    } catch {
      res.writeHead(404).end();
    }
  });
}

async function main() {
  const server = serve();
  await new Promise((r) => server.listen(0, "127.0.0.1", r));
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 3 });
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.goto(`http://127.0.0.1:${server.address().port}/`, { waitUntil: "networkidle" });
    await page.waitForSelector("body[data-ready='1']");
    await page.evaluate(() => document.fonts.ready);
    if (errors.length) throw new Error(errors.join("\n"));

    // Layout check: nothing may spill past the poster's bottom edge.
    const overflow = await page.evaluate(() => {
      const poster = document.getElementById("poster");
      const used = [...poster.children].reduce((h, c) => h + c.getBoundingClientRect().height, 0);
      return { used: Math.round(used), height: poster.clientHeight };
    });
    console.log(`content height ${overflow.used} / ${overflow.height}`);
    if (overflow.used > overflow.height) console.warn("WARNING: content overflows the poster.");

    await fs.mkdir(OUT, { recursive: true });
    const png = path.join(OUT, "liede-research-poster-v2.png");
    const pdf = path.join(OUT, "liede-research-poster-v2.pdf");
    await page.locator("#poster").screenshot({ path: png, animations: "disabled" });
    await page.emulateMedia({ media: "print" });
    await page.pdf({ path: pdf, printBackground: true, preferCSSPageSize: true, tagged: true });
    console.log(`exported\n  ${png}\n  ${pdf}`);
  } finally {
    await browser.close();
    server.close();
  }
}

main().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
