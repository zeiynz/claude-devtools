#!/usr/bin/env python3
"""Evidence ledger for research: track sources and claims, compute confidence, emit a report.

Usage:
  ledger.py init "Topic"
  ledger.py source URL --title T --tier primary|secondary|tertiary|unverified [--date YYYY-MM-DD]
  ledger.py claim "Statement" --sources S1,S2 [--disputed]
  ledger.py check [--max-age-years 3] [--strict]
  ledger.py report [--out research/report.md]
Ledger file: research/ledger.json (override with --file).

Confidence is computed, never self-assigned:
  high   = >=2 independent domains AND >=1 primary source
  medium = >=2 independent domains OR  >=1 primary source
  low    = otherwise (or the claim is disputed)
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

TIERS = ("primary", "secondary", "tertiary", "unverified")
DEFAULT_FILE = Path("research/ledger.json")


def load(path: Path) -> dict:
    if not path.exists():
        sys.exit(f"{path} not found. Run: ledger.py init \"Topic\"")
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def domain(url: str) -> str:
    host = (urlparse(url).netloc or url).lower().split(":")[0]
    parts = host.split(".")
    if len(parts) >= 3 and parts[-2] in ("co", "com", "org", "gov", "ac", "net") and len(parts[-1]) == 2:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def confidence(claim: dict, sources: dict) -> str:
    srcs = [sources[s] for s in claim["sources"] if s in sources]
    domains = {domain(s["url"]) for s in srcs}
    primary = any(s["tier"] == "primary" for s in srcs)
    if claim.get("disputed"):
        return "low"
    if len(domains) >= 2 and primary:
        return "high"
    if len(domains) >= 2 or primary:
        return "medium"
    return "low"


def age_years(d: str | None) -> float | None:
    try:
        return (date.today() - date.fromisoformat(d)).days / 365.25 if d else None
    except ValueError:
        return None


def cmd_init(a, f):
    if f.exists():
        sys.exit(f"{f} already exists")
    save(f, {"topic": a.topic, "created": date.today().isoformat(), "sources": {}, "claims": {}})
    print(f"initialized {f}")


def cmd_source(a, f):
    d = load(f)
    if a.tier not in TIERS:
        sys.exit(f"tier must be one of {TIERS}")
    if any(s["url"] == a.url for s in d["sources"].values()):
        sys.exit("source already recorded")
    sid = f"S{len(d['sources']) + 1}"
    d["sources"][sid] = {"url": a.url, "title": a.title, "tier": a.tier, "date": a.date}
    save(f, d)
    print(sid)


def cmd_claim(a, f):
    d = load(f)
    ids = [s.strip() for s in a.sources.split(",") if s.strip()]
    missing = [s for s in ids if s not in d["sources"]]
    if missing or not ids:
        sys.exit(f"unknown/empty sources: {missing or 'none given'}")
    cid = f"C{len(d['claims']) + 1}"
    d["claims"][cid] = {"text": a.text, "sources": ids, "disputed": a.disputed}
    save(f, d)
    print(f"{cid} confidence={confidence(d['claims'][cid], d['sources'])}")


def issues(d: dict, max_age: float) -> list:
    out, cited = [], set()
    for cid, c in d["claims"].items():
        cited.update(c["sources"])
        conf = confidence(c, d["sources"])
        if conf == "low":
            out.append(("gap", f"{cid} low confidence: {c['text'][:80]}"))
        for sid in c["sources"]:
            s = d["sources"][sid]
            ag = age_years(s.get("date"))
            if ag is None:
                out.append(("warn", f"{cid}/{sid} source has no date"))
            elif ag > max_age:
                out.append(("warn", f"{cid}/{sid} source is {ag:.1f}y old"))
            if s["tier"] == "unverified":
                out.append(("warn", f"{cid}/{sid} source is unverified"))
    for sid in d["sources"]:
        if sid not in cited:
            out.append(("warn", f"{sid} recorded but never cited"))
    return out


def cmd_check(a, f):
    d = load(f)
    found = issues(d, a.max_age_years)
    for kind, msg in found:
        print(f"{kind.upper():4} {msg}")
    print(f"{len(d['claims'])} claims, {len(d['sources'])} sources, {len(found)} issues")
    return 1 if a.strict and any(k == "gap" for k, _ in found) else 0


def cmd_report(a, f):
    d = load(f)
    order = {"high": 0, "medium": 1, "low": 2}
    rows = sorted(((confidence(c, d["sources"]), cid, c) for cid, c in d["claims"].items()), key=lambda r: (order[r[0]], r[1]))
    L = [f"# {d['topic']}", "", f"_Generated {date.today().isoformat()} from {len(d['sources'])} sources, {len(d['claims'])} claims._", "",
         "## Findings", "", "| ID | Claim | Confidence | Sources |", "|---|---|---|---|"]
    for conf, cid, c in rows:
        flag = " (disputed)" if c.get("disputed") else ""
        L.append(f"| {cid} | {c['text']} | {conf}{flag} | {', '.join(c['sources'])} |")
    gaps = [(cid, c) for conf, cid, c in rows if conf == "low"]
    L += ["", "## Gaps and open conflicts", ""]
    L += [f"- {cid}: {c['text']}" for cid, c in gaps] or ["- None."]
    L += ["", "## Sources", "", "| ID | Tier | Title | Date | URL |", "|---|---|---|---|---|"]
    for sid, s in d["sources"].items():
        L.append(f"| {sid} | {s['tier']} | {s['title']} | {s.get('date') or 'n/a'} | {s['url']} |")
    text = "\n".join(L) + "\n"
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(text, encoding="utf-8")
        print(f"wrote {a.out}")
    else:
        print(text)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", type=Path, default=DEFAULT_FILE)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init"); p.add_argument("topic")
    p = sub.add_parser("source"); p.add_argument("url"); p.add_argument("--title", required=True)
    p.add_argument("--tier", required=True); p.add_argument("--date")
    p = sub.add_parser("claim"); p.add_argument("text"); p.add_argument("--sources", required=True)
    p.add_argument("--disputed", action="store_true")
    p = sub.add_parser("check"); p.add_argument("--max-age-years", type=float, default=3.0)
    p.add_argument("--strict", action="store_true")
    p = sub.add_parser("report"); p.add_argument("--out", type=Path)
    a = ap.parse_args()
    fn = {"init": cmd_init, "source": cmd_source, "claim": cmd_claim, "check": cmd_check, "report": cmd_report}[a.cmd]
    return fn(a, a.file) or 0


if __name__ == "__main__":
    sys.exit(main())
