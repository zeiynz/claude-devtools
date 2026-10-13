#!/usr/bin/env python3
"""Lint then package skill folder(s) into <name>.skill (a zip) for claude.ai upload.

Usage:
  package_skill.py PATH [--out dist]
PATH = one skill folder, or a folder containing skill folders.
"""
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lint_skill import collect, lint_skill  # noqa: E402

EXCLUDE = {"__pycache__", ".DS_Store", ".git", "node_modules", ".pytest_cache"}


def package(skill_dir: Path, out_dir: Path) -> Path:
    res = lint_skill(skill_dir)
    errs = [i["msg"] for i in res["issues"] if i["level"] == "error"]
    if errs:
        raise SystemExit(f"{skill_dir.name}: lint errors\n" + "\n".join(f"  - {e}" for e in errs))
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{skill_dir.name}.skill"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(skill_dir.rglob("*")):
            rel = p.relative_to(skill_dir)
            if p.is_dir() or EXCLUDE & set(rel.parts) or p.suffix == ".pyc":
                continue
            z.write(p, Path(skill_dir.name) / rel)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", type=Path)
    ap.add_argument("--out", type=Path, default=Path("dist"))
    a = ap.parse_args()
    for d in collect(a.path.resolve()):
        print(f"packaged {package(d, a.out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
