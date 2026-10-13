#!/usr/bin/env python3
"""Lint Claude skills: frontmatter, description quality, size, broken references.

Usage:
  lint_skill.py PATH [--json]
PATH = one skill folder, or a folder that contains skill folders.
Exit code 1 if any error is found.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TRIGGERS = ("use when", "use this", "use for", "whenever", "trigger")
REF_RE = re.compile(r"\b((?:scripts|references|assets)/[\w.\-/]*\w)")
MAX_BODY_LINES = 500


def parse_frontmatter(text: str):
    m = re.match(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", text, re.S)
    if not m:
        return None, text
    meta, key = {}, None
    for line in m.group(1).splitlines():
        km = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if km:
            key, val = km.group(1), km.group(2).strip()
            if val in (">", "|", ">-", "|-"):
                val = ""
            meta[key] = val.strip("'\"")
        elif key and line.strip():
            meta[key] = f"{meta[key]} {line.strip()}".strip()
    return meta, text[m.end():]


def _result(skill_dir: Path, issues: list) -> dict:
    errors = sum(i["level"] == "error" for i in issues)
    warns = sum(i["level"] == "warn" for i in issues)
    return {"skill": skill_dir.name, "score": max(0, 100 - 25 * errors - 5 * warns), "issues": issues}


def lint_skill(skill_dir: Path) -> dict:
    issues: list = []

    def err(m): issues.append({"level": "error", "msg": m})
    def warn(m): issues.append({"level": "warn", "msg": m})

    f = skill_dir / "SKILL.md"
    if not f.is_file():
        err("SKILL.md missing")
        return _result(skill_dir, issues)

    meta, body = parse_frontmatter(f.read_text(encoding="utf-8"))
    if meta is None:
        err("frontmatter missing (--- name/description ---)")
        meta = {}

    name, desc = meta.get("name", ""), meta.get("description", "")
    if not name:
        err("name missing")
    else:
        if not NAME_RE.match(name):
            err(f"name '{name}' must be kebab-case")
        if len(name) > 64:
            err("name longer than 64 chars")
        if name != skill_dir.name:
            warn(f"name '{name}' differs from folder '{skill_dir.name}'")

    if not desc:
        err("description missing")
    else:
        if len(desc) > 1024:
            err(f"description is {len(desc)} chars (max 1024)")
        if len(desc) < 80:
            warn("description too short: state what it does AND when to use it")
        if not any(t in desc.lower() for t in TRIGGERS):
            warn("description has no trigger phrase (e.g. 'Use when ...')")
        if "<" in desc or ">" in desc:
            warn("description contains angle brackets")

    lines = body.count("\n") + 1
    if lines > MAX_BODY_LINES:
        warn(f"SKILL.md body is {lines} lines (>{MAX_BODY_LINES}); move detail to references/")

    for ref in sorted(set(REF_RE.findall(body))):
        if not (skill_dir / ref).exists():
            err(f"broken reference: {ref}")

    refs = skill_dir / "references"
    if refs.is_dir():
        for p in sorted(refs.glob("*.md")):
            txt = p.read_text(encoding="utf-8")
            n = len(txt.splitlines())
            if n > 300 and not re.search(r"(?im)^#+\s*(table of contents|contents)", txt):
                warn(f"references/{p.name}: {n} lines without a table of contents")

    return _result(skill_dir, issues)


def collect(path: Path) -> list:
    if path.is_dir() and any((c / "SKILL.md").exists() for c in path.iterdir() if c.is_dir()):
        return sorted(c for c in path.iterdir() if c.is_dir() and not c.name.startswith("."))
    return [path]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", type=Path)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    results = [lint_skill(p) for p in collect(a.path.resolve())]
    failed = any(i["level"] == "error" for r in results for i in r["issues"])

    if a.json:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            bad = any(i["level"] == "error" for i in r["issues"])
            print(f"{'x' if bad else 'ok'} {r['skill']}  score={r['score']}")
            for i in r["issues"]:
                print(f"    {i['level'].upper():5} {i['msg']}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
