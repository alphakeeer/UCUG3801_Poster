"use strict";

const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");

const staticRoot = path.join(__dirname, "dist");
const mimeTypes = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".jpg": "image/jpeg",
  ".png": "image/png",
  ".pdf": "application/pdf",
  ".woff2": "font/woff2",
  ".txt": "text/plain; charset=utf-8",
};

function createServer() {
  return http.createServer(async (request, response) => {
    if (!["GET", "HEAD"].includes(request.method)) {
      response.writeHead(405, { Allow: "GET, HEAD" }).end();
      return;
    }
    let filePath;
    try {
      const pathname = decodeURIComponent(
        new URL(request.url, "http://localhost").pathname,
      );
      filePath = path.resolve(
        staticRoot,
        `.${pathname.endsWith("/") ? `${pathname}index.html` : pathname}`,
      );
      if (!filePath.startsWith(`${staticRoot}${path.sep}`)) {
        response.writeHead(403).end();
        return;
      }
      const stats = await fs.promises.stat(filePath);
      if (!stats.isFile()) {
        response.writeHead(404).end();
        return;
      }
      response.writeHead(200, {
        "Content-Type":
          mimeTypes[path.extname(filePath)] || "application/octet-stream",
        "Content-Length": stats.size,
        "Cache-Control": "no-cache",
      });
      if (request.method === "HEAD") {
        response.end();
        return;
      }
      fs.createReadStream(filePath)
        .on("error", () => response.destroy())
        .pipe(response);
    } catch {
      response.writeHead(404).end();
    }
  });
}

if (require.main === module) {
  const port = Number(process.env.PORT || 8765);
  createServer().listen(port, "127.0.0.1", () => {
    console.log(`Local: http://127.0.0.1:${port}/`);
  });
}

module.exports = { createServer };
