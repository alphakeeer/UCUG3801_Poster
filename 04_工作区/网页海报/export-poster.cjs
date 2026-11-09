"use strict";

const fs = require("node:fs/promises");
const path = require("node:path");
const { chromium } = require("playwright");
const { createServer } = require("./server.cjs");

async function exportPoster() {
  const server = createServer();
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  let browser;
  try {
    browser = await chromium.launch({ headless: true });
    const page = await browser.newPage({
      viewport: { width: 1080, height: 1920 },
      deviceScaleFactor: 3,
    });
    const pageErrors = [];
    page.on("pageerror", (error) => pageErrors.push(error.message));
    await page.goto(`http://127.0.0.1:${server.address().port}/`, {
      waitUntil: "networkidle",
    });
    await page.evaluate(() => document.body.classList.add("capture-mode"));
    await page.evaluate(() => document.fonts.ready);
    await page.evaluate(
      () =>
        new Promise((resolve) =>
          requestAnimationFrame(() => requestAnimationFrame(resolve)),
        ),
    );
    if (pageErrors.length) throw new Error(pageErrors.join("\n"));
    const assetsReady = await page.evaluate(() => {
      return (
        [...document.images].every((image) => image.complete && image.naturalWidth > 0) &&
        document.fonts.check('600 20px "Poster Serif"') &&
        document.fonts.check('400 20px "Poster Sans"')
      );
    });
    if (!assetsReady) throw new Error("Poster image or fonts did not load.");

    const assets = path.join(__dirname, "dist", "assets");
    const submission = path.resolve(__dirname, "../../05_提交/poster_final");
    await fs.mkdir(submission, { recursive: true });
    const pngPath = path.join(assets, "liede-research-poster.png");
    const pdfPath = path.join(assets, "liede-research-poster.pdf");
    await page
      .locator("#poster")
      .screenshot({ path: pngPath, animations: "disabled" });
    await page.pdf({
      path: pdfPath,
      printBackground: true,
      preferCSSPageSize: true,
      tagged: true,
    });
    await fs.copyFile(
      pngPath,
      path.join(submission, "liede-research-poster.png"),
    );
    await fs.copyFile(
      pdfPath,
      path.join(submission, "liede-research-poster.pdf"),
    );
    console.log(
      "Exported 3240×5760 PNG and vector PDF to dist/assets and 05_提交/poster_final.",
    );
  } finally {
    if (browser) await browser.close();
    await new Promise((resolve) => server.close(resolve));
  }
}

exportPoster().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
