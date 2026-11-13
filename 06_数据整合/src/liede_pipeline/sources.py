from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from .common import EDUCATION, Context, digest, stable_id

REGISTRIES = [Path("03_背景/资料库/下载清单.json"),
    EDUCATION / "下载清单.json",
    Path("03_背景/资料库/补充选题资料/补充来源清单.json")]


def canonical_url(url: str) -> str:
    p = urlsplit(url)
    return urlunsplit(("https" if p.scheme in {"http", "https"} else p.scheme,
                       p.netloc.lower(), p.path, p.query, ""))


class Sources:
    def __init__(self, context: Context):
        self.context = context
        self.rows: dict[str, dict] = {}
        self.url_ids: dict[str, str] = {}
        context.source_manager = self
        for registry in REGISTRIES:
            for row in json.loads((context.root / registry).read_text()):
                local = row.get("local_file", "")
                availability = "archived" if local and (context.root/local).is_file() else "unavailable"
                if row["source_id"] == "E016-A001":
                    availability = "multipart_archive"
                self.rows[row["source_id"]] = dict(id=row["source_id"],
                    canonical_source_id=row["source_id"], title=row["title"], url=row["url"],
                    document_date=row.get("document_date", ""),
                    publication_date=row.get("web_publication_date", ""),
                    retrieved_at=row.get("checked_at_utc", ""),
                    local_file=local, reference_path=str(registry),
                    sha256=row.get("sha256", ""), availability=availability,
                    source_kind=row.get("kind", "registered_source"),
                    provenance_status="archive_metadata", note=row.get("scope_note", ""))
        self._canonicalize()

    def _canonicalize(self):
        hashes, urls = {}, {}
        for key in sorted(self.rows):
            row = self.rows[key]
            url = canonical_url(row["url"]) if row["url"] else ""
            canonical = hashes.get(row["sha256"]) if row["sha256"] else None
            canonical = canonical or urls.get(url) or key
            row["canonical_source_id"] = canonical
            if row["sha256"]:
                hashes[row["sha256"]] = canonical
            if url:
                urls[url] = canonical
        self.url_ids = urls

    def reference(self, url: str, title: str, reference_path: str,
                  kind: str = "referenced_source", document_date: str = "",
                  requested_id: str = "") -> str:
        if not url:
            raise ValueError("A referenced source needs a URL")
        normalized = canonical_url(url)
        if requested_id and requested_id in self.rows:
            if canonical_url(self.rows[requested_id]["url"]) != normalized:
                raise ValueError(f"Source ID/URL conflict: {requested_id}")
            return requested_id
        if not requested_id and normalized in self.url_ids:
            return self.url_ids[normalized]
        key = requested_id or stable_id("URL-", normalized)
        self.rows[key] = dict(id=key, canonical_source_id=self.url_ids.get(normalized,key),
            title=title, url=url, document_date=document_date, publication_date="",
            retrieved_at="", local_file="", reference_path=reference_path, sha256="",
            availability="reference_only", source_kind=kind,
            provenance_status="reported_in_repository_or_import", note="本流水线未重新获取外部原始来源")
        self.url_ids.setdefault(normalized, key)
        return key

    def archive_local(self, relative_path: str, title: str, kind: str) -> str:
        key = stable_id("LOCAL-", relative_path)
        p = self.context.root / relative_path
        self.rows[key] = dict(id=key, canonical_source_id=key, title=title, url="",
            document_date="", publication_date="", retrieved_at="", local_file=relative_path,
            reference_path=relative_path, sha256=digest(p), availability="archived",
            source_kind=kind, provenance_status="local_snapshot", note="本地研究载体，不自动视为外部一手原件")
        return key

    def verify_archives(self) -> list[dict]:
        checks = []
        for row in sorted(self.rows.values(), key=lambda r:r["id"]):
            if row["availability"] == "archived":
                actual = digest(self.context.root/row["local_file"])
                checks.append(dict(id="archive:"+row["id"], passed=actual==row["sha256"],
                    detail=row["local_file"]))
            elif row["availability"] == "multipart_archive":
                folder = self.context.root/EDUCATION/"原始文件/E016-A001_分卷"
                manifest = json.loads((folder/"manifest.json").read_text())
                full = hashlib.sha256()
                valid = True
                for part in manifest["parts"]:
                    data = (folder/part["name"]).read_bytes()
                    valid &= hashlib.sha256(data).hexdigest() == part["sha256"]
                    full.update(data)
                checks.append(dict(id="archive:"+row["id"],
                    passed=bool(valid and full.hexdigest()==row["sha256"]), detail="内存中核验分卷，不还原或改写原文件"))
        return checks

    def export(self):
        self.context.tables["source_registry"] = sorted(self.rows.values(),key=lambda r:r["id"])
