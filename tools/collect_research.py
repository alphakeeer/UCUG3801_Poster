"""Collect the registered research sources and preserve an auditable local archive."""

import concurrent.futures
import csv
import hashlib
import json
import logging
import re
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from lxml import html
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "03_背景/资料库"
RAW = LIBRARY / "原始文件"
TEXT = LIBRARY / "正文"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
logging.getLogger("pypdf").setLevel(logging.ERROR)


def download(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.read(), response.geturl(), "urllib"
    except (OSError, urllib.error.URLError):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "response"
            result = subprocess.run(
                [
                    "curl", "--http1.1", "--location", "--fail", "--silent",
                    "--show-error", "--connect-timeout", "10", "--max-time", "35",
                    "--user-agent", USER_AGENT, "--output", str(target),
                    "--write-out", "%{url_effective}", url,
                ],
                capture_output=True,
                text=True,
                timeout=45,
            )
            if result.returncode:
                raise RuntimeError(result.stderr.strip() or "HTTP download failed")
            return target.read_bytes(), result.stdout.strip(), "curl"


def html_document(data):
    head = data[:5000].decode("ascii", errors="ignore")
    match = re.search(r"charset\s*=\s*[\"']?([\w-]+)", head, re.IGNORECASE)
    encoding = match.group(1) if match else "utf-8"
    return html.fromstring(data, parser=html.HTMLParser(encoding=encoding))


def inspect_html(data, base_url):
    tree = html_document(data)
    title = tree.xpath("string(//title)").strip()
    publication_dates = tree.xpath(
        '//meta[@name="PubDate" or @name="pubdate" or @name="publishdate"]/@content'
    )
    nodes = tree.xpath(
        '//text()[not(ancestor::script) and not(ancestor::style) '
        'and not(ancestor::noscript)]'
    )
    lines = [re.sub(r"\s+", " ", str(node)).strip() for node in nodes]
    lines = [line for line in lines if line]
    text = "\n".join(lines)
    if len(text) < 100 or re.search(
        r"Access Denied|Just a moment|Error 403|502 Bad Gateway", title, re.IGNORECASE
    ):
        raise ValueError(f"Response is not a readable document: {title}")
    attachments = []
    for element in tree.xpath("//a[@href]"):
        url = urllib.parse.urljoin(base_url, element.get("href"))
        parsed = urllib.parse.urlparse(url)
        suffix = Path(parsed.path).suffix.lower()
        if parsed.scheme in ["http", "https"] and suffix in [".pdf", ".doc", ".docx", ".xls", ".xlsx"]:
            if url not in [item["url"] for item in attachments]:
                attachments.append({"url": url, "label": element.text_content().strip()})
    return text, {
        "page_title": title,
        "web_publication_date": publication_dates[0] if publication_dates else "",
        "attachments": attachments,
    }


def extract_pdf(path):
    reader = PdfReader(path)
    texts = [page.extract_text() or "" for page in reader.pages]
    content = "\n\n".join(
        f"[PDF第{index + 1}页]\n{text}" for index, text in enumerate(texts)
    )
    empty_pages = [index + 1 for index, text in enumerate(texts) if len(text.strip()) < 30]
    text_status = "partial" if empty_pages else "ok"
    if content.count("/G") * 3 > len(content) * 0.3:
        text_status = "font_encoding_unreadable"
        content = "注意：原PDF字体编码导致正文提取乱码，请阅读原PDF。以下内容仅保留提取诊断。\n\n" + content
    return content, {
        "page_count": len(reader.pages),
        "low_text_pages": empty_pages,
        "text_status": text_status,
    }


def acquire(source):
    record = dict(source)
    record["checked_at_utc"] = datetime.now(timezone.utc).isoformat()
    record["status"] = "failed"
    try:
        if source.get("existing_file"):
            raw_path = ROOT / source["existing_file"]
            data = raw_path.read_bytes()
            final_url, acquisition, status = source["url"], "existing_repository_file", "reused"
        else:
            candidates = sorted(RAW.glob(f'{source["source_id"]}_*'))
            if candidates:
                raw_path = candidates[0]
                data = raw_path.read_bytes()
                final_url, acquisition, status = source["url"], "existing_archive", "cached"
            else:
                try:
                    data, final_url, acquisition = download(source["url"])
                    status = "downloaded"
                except Exception as error:
                    cache = Path(source.get("session_cache", "/missing-cache"))
                    if not cache.is_file():
                        raise
                    data = cache.read_bytes()
                    final_url = source["url"]
                    acquisition, status = "earlier_session_cache", "cached"
                    record["live_download_error"] = str(error)
                    record["cache_mtime_utc"] = datetime.fromtimestamp(
                        cache.stat().st_mtime, timezone.utc
                    ).isoformat()
                is_pdf = data.startswith(b"%PDF")
                requested_suffix = Path(urllib.parse.urlparse(source["url"]).path).suffix.lower()
                if requested_suffix == ".pdf" and not is_pdf:
                    raise ValueError("PDF URL returned a non-PDF response")
                suffix = ".pdf" if is_pdf else ".html"
                if requested_suffix in [".doc", ".docx", ".xls", ".xlsx"]:
                    suffix = requested_suffix
                title = re.sub(r"[^\w\u4e00-\u9fff.-]", "_", source["title"])[:70]
                raw_path = RAW / f'{source["source_id"]}_{title}{suffix}'
                if suffix == ".html":
                    inspect_html(data, final_url)
                raw_path.write_bytes(data)

        if data.startswith(b"%PDF"):
            content, metadata = extract_pdf(raw_path)
        elif raw_path.suffix.lower() == ".html":
            content, metadata = inspect_html(data, final_url)
            metadata["text_status"] = "ok"
        else:
            content, metadata = "", {"text_status": "unsupported_binary"}

        text_path = TEXT / f'{source["source_id"]}.txt'
        if content:
            prefix = (
                f'来源编号 {source["source_id"]}\n标题 {source["title"]}\n'
                f'原始网址 {source["url"]}\n核对日期 {record["checked_at_utc"]}\n\n'
            )
            text_path.write_text(prefix + content + "\n", encoding="utf-8")
        record.update(metadata)
        record.update({
            "status": status,
            "acquisition": acquisition,
            "final_url": final_url,
            "local_file": str(raw_path.relative_to(ROOT)),
            "text_file": str(text_path.relative_to(ROOT)) if content else "",
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "extracted_characters": len(content),
        })
    except Exception as error:
        record["error"] = str(error)
    print(record["source_id"], record["status"], record.get("bytes", 0), flush=True)
    return record


def save_catalog(records):
    (LIBRARY / "下载清单.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    columns = [
        "source_id", "title", "kind", "direction", "document_date", "web_publication_date",
        "status", "acquisition", "local_file", "text_file", "page_count", "text_status",
        "ocr_text_file", "ocr_status", "extracted_characters", "bytes", "sha256", "url",
        "checked_at_utc", "scope_note", "error",
    ]
    with (LIBRARY / "下载清单.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    TEXT.mkdir(parents=True, exist_ok=True)
    sources = json.loads((LIBRARY / "来源清单.json").read_text())
    catalog_path = LIBRARY / "下载清单.json"
    previous = json.loads(catalog_path.read_text()) if catalog_path.exists() else []
    previous_by_id = {record["source_id"]: record for record in previous}
    history_path = LIBRARY / "下载尝试.jsonl"
    if previous and not history_path.exists():
        history_path.write_text(
            "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in previous)
        )
    records = []
    pending = []
    for source in sources:
        prior = previous_by_id.get(source["source_id"])
        local_file = ROOT / prior.get("local_file", "missing") if prior else None
        if (
            prior and prior["status"] != "failed" and prior["url"] == source["url"]
            and local_file.is_file()
            and hashlib.sha256(local_file.read_bytes()).hexdigest() == prior.get("sha256")
        ):
            records.append({**prior, **source})
        else:
            pending.append(source)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        jobs = {executor.submit(acquire, source): source for source in pending}
        for job in concurrent.futures.as_completed(jobs):
            record = job.result()
            records.append(record)
            with history_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            save_catalog(sorted(records, key=lambda item: item["source_id"]))
    records.sort(key=lambda item: item["source_id"])
    save_catalog(records)
    success = sum(record["status"] != "failed" for record in records)
    print(f"Complete: {success}/{len(records)} sources acquired", flush=True)


if __name__ == "__main__":
    main()
