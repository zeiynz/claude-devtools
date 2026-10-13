#!/usr/bin/env python3
"""Build a single-file, offline HTML dashboard from CSV or JSON.

Usage:
  build_dashboard.py DATA.csv|DATA.json [--title T] [--out dashboard.html] [--max-rows N]

Auto-detects column types (number / date / category / text), then renders KPIs,
time-series, top-N bars, histogram, filters, search, sortable paged table, CSV export.
No CDN, no dependencies: the output opens from disk and works offline.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import date
from pathlib import Path

NUM_RE = re.compile(r"^-?\d{1,3}(,\d{3})+(\.\d+)?$|^-?\d+(\.\d+)?$")
DATE_RE = re.compile(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})")
THRESH = 0.9


def load_rows(path: Path) -> list:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(data, dict):
            data = next((v for v in data.values() if isinstance(v, list)), [data])
        return [r for r in data if isinstance(r, dict)]
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def to_num(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    return float(s.replace(",", "")) if NUM_RE.match(s) else None


def to_date(v):
    m = DATE_RE.match(str(v).strip())
    if not m:
        return None
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try:
        return date(y, mo, d).isoformat()
    except ValueError:
        return None


def infer(values: list) -> str:
    vals = [v for v in values if v not in (None, "")]
    if not vals:
        return "text"
    n = len(vals)
    if sum(to_num(v) is not None for v in vals) / n >= THRESH:
        return "number"
    if sum(to_date(v) is not None for v in vals) / n >= THRESH:
        return "date"
    uniq = len({str(v) for v in vals})
    return "category" if uniq <= 30 or uniq / n <= 0.2 else "text"


def build(rows: list, max_rows: int) -> dict:
    if not rows:
        raise SystemExit("no rows found")
    rows = rows[:max_rows]
    names = list(dict.fromkeys(k for r in rows for k in r))
    cols, conv = [], {}
    for name in names:
        t = infer([r.get(name) for r in rows])
        cols.append({"name": name, "type": t})
        conv[name] = {"number": to_num, "date": to_date}.get(t, lambda v: None if v in (None, "") else str(v))
    out = [{n: conv[n](r.get(n)) for n in names} for r in rows]
    return {"cols": cols, "rows": out, "generated": date.today().isoformat()}


def render(payload: dict, title: str) -> str:
    tpl = (Path(__file__).parent / "template.html").read_text(encoding="utf-8")
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")  # cannot close the <script> tag
    esc_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return tpl.replace("__TITLE__", esc_title).replace("__PAYLOAD__", data)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("data", type=Path)
    ap.add_argument("--title")
    ap.add_argument("--out", type=Path, default=Path("dashboard.html"))
    ap.add_argument("--max-rows", type=int, default=50000)
    a = ap.parse_args()
    payload = build(load_rows(a.data), a.max_rows)
    a.out.write_text(render(payload, a.title or a.data.stem.replace("_", " ").title()), encoding="utf-8")
    kinds = ", ".join(f"{c['name']}:{c['type']}" for c in payload["cols"])
    print(f"wrote {a.out} ({len(payload['rows'])} rows) [{kinds}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
