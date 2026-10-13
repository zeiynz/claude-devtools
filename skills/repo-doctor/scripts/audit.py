#!/usr/bin/env python3
"""Audit a repository's health: docs, license, CI, tests, hygiene, and committed secrets.

Usage:
  audit.py [PATH] [--json | --md] [--fail-under N]
Zero dependencies. Secrets are masked in all output.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build", ".next", "target", ".idea", ".tox"}
BINARY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".gz", ".tar", ".skill",
              ".woff", ".woff2", ".ttf", ".mp4", ".mp3", ".pyc", ".so", ".dll", ".exe", ".lock"}
SECRET_PATTERNS = {
    "AWS access key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "GitHub token": re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"),
    "Slack token": re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    "Private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "Generic secret": re.compile(r"""(?i)(?:api[_-]?key|secret|token|passwd|password)\s*[:=]\s*['"][A-Za-z0-9/+_\-]{16,}['"]"""),
}
IGNORE_LINE = re.compile(r"(?i)example|changeme|your[_-]|placeholder|dummy|xxxx|<.*>")
MAX_SCAN_BYTES = 1_000_000
BIG_FILE = 5_000_000


def walk(root: Path):
    for p in root.rglob("*"):
        if p.is_file() and not (SKIP_DIRS & set(p.relative_to(root).parts)):
            yield p


def mask(s: str) -> str:
    return s[:4] + "…" + f"({len(s)} chars)"


def scan_secrets(root: Path) -> list:
    hits = []
    for p in walk(root):
        if p.suffix.lower() in BINARY_EXT or p.stat().st_size > MAX_SCAN_BYTES:
            continue
        try:
            lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for n, line in enumerate(lines, 1):
            if IGNORE_LINE.search(line):
                continue
            for label, rx in SECRET_PATTERNS.items():
                m = rx.search(line)
                if m:
                    hits.append({"file": str(p.relative_to(root)), "line": n, "type": label, "match": mask(m.group(0))})
                    break
    return hits


def has_any(root: Path, names) -> bool:
    lower = {p.name.lower() for p in root.iterdir()}
    return any(n.lower() in lower for n in names)


def gitignored(root: Path, entry: str) -> bool:
    gi = root / ".gitignore"
    return gi.exists() and any(l.strip().rstrip("/") == entry for l in gi.read_text(errors="ignore").splitlines())


def checks(root: Path) -> list:
    """(id, label, weight, passed, fix)"""
    readme = next((p for p in root.iterdir() if p.name.lower().startswith("readme")), None)
    rtext = readme.read_text(encoding="utf-8", errors="ignore") if readme else ""
    rl = rtext.lower()
    files = list(walk(root))
    names = {p.name for p in files}
    ci = (root / ".github" / "workflows").is_dir() and any((root / ".github" / "workflows").iterdir()) \
        or (root / ".gitlab-ci.yml").exists() or (root / ".circleci").is_dir()
    tests = any(re.match(r"(test_.*|.*_test|.*\.test|.*\.spec)\.\w+$", n) for n in names) \
        or any(d.is_dir() and d.name in ("tests", "test", "__tests__") for d in root.rglob("*") if not (SKIP_DIRS & set(d.relative_to(root).parts)))
    manifests = {"package.json": ["package-lock.json", "yarn.lock", "pnpm-lock.yaml"],
                 "pyproject.toml": ["poetry.lock", "uv.lock", "pdm.lock"],
                 "Cargo.toml": ["Cargo.lock"], "go.mod": ["go.sum"], "Gemfile": ["Gemfile.lock"]}
    lock_ok = all(any((root / l).exists() for l in locks) for m, locks in manifests.items() if (root / m).exists())
    big = [p for p in files if p.stat().st_size > BIG_FILE]
    return [
        ("readme", "README exists", 10, bool(readme), "Add a README.md"),
        ("readme_len", "README is substantive (>=40 lines)", 5, len(rtext.splitlines()) >= 40, "Expand README: what, why, install, usage"),
        ("readme_install", "README has install/usage", 8, ("install" in rl or "quick start" in rl or "getting started" in rl) and "usage" in rl or "```" in rtext and "install" in rl,
         "Add Install and Usage sections with code blocks"),
        ("license", "LICENSE present", 10, has_any(root, ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"]), "Add a LICENSE (MIT/Apache-2.0)"),
        ("gitignore", ".gitignore present", 5, (root / ".gitignore").exists(), "Add .gitignore"),
        ("ci", "CI configured", 12, bool(ci), "Add .github/workflows/ci.yml running tests"),
        ("tests", "Tests exist", 15, bool(tests), "Add tests; CI should run them"),
        ("contributing", "CONTRIBUTING present", 4, has_any(root, ["CONTRIBUTING.md"]), "Add CONTRIBUTING.md"),
        ("security", "SECURITY policy present", 3, has_any(root, ["SECURITY.md"]) or (root / ".github" / "SECURITY.md").exists(), "Add SECURITY.md"),
        ("changelog", "CHANGELOG present", 3, has_any(root, ["CHANGELOG.md", "CHANGES.md", "HISTORY.md"]), "Add CHANGELOG.md"),
        ("lockfile", "Dependency lockfile for each manifest", 5, lock_ok, "Commit the lockfile"),
        ("env", ".env not exposed", 10, not ((root / ".env").exists() and not gitignored(root, ".env")), "Add .env to .gitignore and rotate its values"),
        ("bigfiles", "No files >5MB", 5, not big, f"Remove or LFS: {', '.join(str(b.relative_to(root)) for b in big[:3])}"),
    ]


def grade(score: int) -> str:
    return "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "D" if score >= 60 else "F"


def audit(root: Path) -> dict:
    cs = checks(root)
    total = sum(w for _, _, w, _, _ in cs)
    got = sum(w for _, _, w, ok, _ in cs if ok)
    secrets = scan_secrets(root)
    score = max(0, round(100 * got / total) - min(45, 15 * len(secrets)))
    return {
        "path": str(root), "score": score, "grade": grade(score),
        "checks": [{"id": i, "label": l, "weight": w, "passed": bool(ok), "fix": None if ok else fix} for i, l, w, ok, fix in cs],
        "secrets": secrets,
    }


def render_text(r: dict) -> str:
    out = [f"Repo health: {r['score']}/100 ({r['grade']})  {r['path']}", ""]
    for c in r["checks"]:
        out.append(f"  {'PASS' if c['passed'] else 'FAIL'}  {c['label']}" + ("" if c["passed"] else f"  -> {c['fix']}"))
    if r["secrets"]:
        out += ["", f"POSSIBLE SECRETS ({len(r['secrets'])}): rotate them, then purge from history"]
        out += [f"  {s['file']}:{s['line']}  {s['type']}  {s['match']}" for s in r["secrets"]]
    return "\n".join(out)


def render_md(r: dict) -> str:
    color = {"A": "brightgreen", "B": "green", "C": "yellow", "D": "orange", "F": "red"}[r["grade"]]
    out = [f"![repo health](https://img.shields.io/badge/repo%20health-{r['score']}%25-{color})", "",
           f"## Repo health: {r['score']}/100 ({r['grade']})", "", "| Check | Status | Fix |", "|---|---|---|"]
    out += [f"| {c['label']} | {'✅' if c['passed'] else '❌'} | {c['fix'] or ''} |" for c in r["checks"]]
    if r["secrets"]:
        out += ["", "### Possible secrets", ""] + [f"- `{s['file']}:{s['line']}` {s['type']} `{s['match']}`" for s in r["secrets"]]
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?", type=Path, default=Path("."))
    fmt = ap.add_mutually_exclusive_group()
    fmt.add_argument("--json", action="store_true")
    fmt.add_argument("--md", action="store_true")
    ap.add_argument("--fail-under", type=int, default=0)
    a = ap.parse_args()
    root = a.path.resolve()
    if not root.is_dir():
        sys.exit(f"{root} is not a directory")
    r = audit(root)
    print(json.dumps(r, indent=2) if a.json else render_md(r) if a.md else render_text(r))
    return 1 if r["score"] < a.fail_under else 0


if __name__ == "__main__":
    sys.exit(main())
