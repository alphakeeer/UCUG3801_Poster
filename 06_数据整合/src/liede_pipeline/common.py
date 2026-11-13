from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from pathlib import Path

EDUCATION = Path("03_背景/教育专题")
HOUSING = Path("04_工作区/研究分析/房价分布")
TRANSPORT = Path("04_工作区/研究分析/交通可达性")
YEAR = 2026


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_id(prefix: str, *values: object) -> str:
    text = json.dumps(values, ensure_ascii=False, sort_keys=True)
    return prefix + hashlib.sha256(text.encode()).hexdigest()[:12]


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: cell(row.get(field)) for field in fields})


def cell(value: object) -> object:
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if isinstance(value, bool):
        return "true" if value else "false"
    return value


def number(value: object) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"Non-finite numeric value: {value!r}")
    return result


def ids(value: str) -> list[str]:
    return [v for v in re.split(r"[/;|]", value or "") if v]


def citation(table: str, record_id: str) -> str:
    return f"{table}:{record_id}"


class Context:
    def __init__(self, root: Path, module: Path):
        self.root, self.module = root, module
        self.tables: dict[str, list[dict]] = {}
        self.gaps: list[dict] = []
        self.source_manager = None

    def csv(self, path: Path) -> list[dict]:
        return read_csv(self.root / path)

    def table(self, name: str) -> list[dict]:
        return self.tables.setdefault(name, [])

    def gap(self, code: str, priority: str, subject: str, finding: str,
            needed: str, sources: list[str] | None = None,
            status: str = "open") -> None:
        key = stable_id("GAP-", code, subject)
        existing = next((r for r in self.gaps if r["id"]==key),None)
        if existing:
            existing["occurrences"] += 1
            existing["source_ids"] = sorted(set(existing["source_ids"]+(sources or [])))
            if finding not in existing["finding"]:
                existing["finding"] += " | "+finding
            if needed not in existing["needed_evidence"]:
                existing["needed_evidence"] += " | "+needed
            return
        self.gaps.append(dict(id=key, code=code,
            priority=priority, subject_id=subject, status=status, finding=finding,
            needed_evidence=needed, source_ids=sources or [],occurrences=1))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
