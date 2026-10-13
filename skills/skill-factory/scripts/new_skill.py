#!/usr/bin/env python3
"""Scaffold a new skill folder.

Usage:
  new_skill.py NAME "What it does. Use when ..." [--out skills]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TEMPLATE = """---
name: {name}
description: {desc}
---

# {title}

One-sentence purpose.

## Workflow

1. Step one (imperative, explain *why* it matters).
2. Step two.
3. Verify the result before reporting.

## Output format

Describe the exact structure of the final answer.

## Scripts

- `scripts/example.py` - what it does, when to run it.
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name")
    ap.add_argument("description")
    ap.add_argument("--out", type=Path, default=Path("skills"))
    a = ap.parse_args()
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", a.name):
        sys.exit("name must be kebab-case, e.g. my-skill")
    d = a.out / a.name
    if d.exists():
        sys.exit(f"{d} already exists")
    (d / "scripts").mkdir(parents=True)
    (d / "references").mkdir()
    (d / "SKILL.md").write_text(
        TEMPLATE.format(name=a.name, desc=a.description, title=a.name.replace("-", " ").title()),
        encoding="utf-8",
    )
    # Template mentions scripts/example.py; create it so a new skill lints clean.
    (d / "scripts" / "example.py").write_text('print("replace me")\n', encoding="utf-8")
    print(f"created {d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
