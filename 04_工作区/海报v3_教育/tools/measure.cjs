"use strict";
// 打印海报各区块内每一栏的自然高度，用于找出撑高区块的那一栏。用法：node tools/measure.cjs e-fieldreport
const fs = require("node:fs/promises"), http = require("node:http"), path = require("node:path");
const { chromium } = require(path.join(__dirname, "../../海报v2/node_modules/playwright"));
const ROOT = path.resolve(__dirname, "../..");
(async () => {
  const server = http.createServer(async (req, res) => {
    const file = path.join(ROOT, decodeURIComponent(new URL(req.url, "http://x").pathname));
    try { res.writeHead(200).end(await fs.readFile(file)); } catch { res.writeHead(404).end(); }
  });
  await new Promise((r) => server.listen(0, "127.0.0.1", r));
  const b = await chromium.launch(), p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  await p.goto(`http://127.0.0.1:${server.address().port}/海报v3_教育/designs/${process.argv[2]}/index.html`);
  await p.waitForSelector("body[data-ready='1']");
  const out = await p.evaluate(() => [...document.querySelectorAll("#poster > *")].map((sec) => {
    const cols = [...sec.querySelectorAll(":scope > *, :scope > * > .f1body > *, :scope > .f2body > *, :scope > .f1body > *")];
    const nat = (e) => { const r = e.getBoundingClientRect(); const kids = [...e.children]; if (!kids.length) return Math.round(r.height); return Math.round(Math.max(...kids.map((k) => k.getBoundingClientRect().bottom)) - r.top); };
    return (sec.className.split(" ")[0]) + " " + Math.round(sec.getBoundingClientRect().height) + " | " + cols.map((c) => (c.className || c.tagName).toString().split(" ")[0] + ":" + nat(c)).join(" ");
  }));
  console.log(out.join("\n"));
  await b.close(); server.close();
})();
