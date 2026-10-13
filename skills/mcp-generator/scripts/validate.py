#!/usr/bin/env python3
"""Validate an MCP spec (.json) or a server file (.py / .ts) against MCP best practices.

Usage:
  validate.py spec.json | server.py | index.ts
Exit code 1 on errors.
"""
from __future__ import annotations

import ast
import json
import keyword
import re
import sys
from pathlib import Path

VALID_TYPES = {"string", "integer", "number", "boolean", "array", "object"}
NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
MAX_TOOLS = 15


def validate_spec(spec: dict) -> list:
    out = []
    e = lambda m: out.append(("error", m))
    w = lambda m: out.append(("warn", m))
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", str(spec.get("name", ""))):
        e("name must be kebab-case")
    if spec.get("language", "python") not in ("python", "typescript"):
        e("language must be python or typescript")
    tools = spec.get("tools")
    if not tools:
        e("tools[] is empty")
        return out
    if len(tools) > MAX_TOOLS:
        w(f"{len(tools)} tools: too many choices degrade tool selection; merge or split the server")
    seen = set()
    for t in tools:
        n = t.get("name", "")
        if not NAME_RE.match(n) or keyword.iskeyword(n):
            e(f"tool '{n}': use snake_case and not a Python keyword")
        if n in seen:
            e(f"duplicate tool '{n}'")
        seen.add(n)
        if len(t.get("description", "")) < 20:
            e(f"tool '{n}': description < 20 chars (the model picks tools by description)")
        for p in t.get("params", []):
            pn = p.get("name", "")
            if not pn.isidentifier() or keyword.iskeyword(pn):
                e(f"tool '{n}': invalid param name '{pn}'")
            if p.get("type") not in VALID_TYPES:
                e(f"tool '{n}': param '{pn}' type must be one of {sorted(VALID_TYPES)}")
            if not p.get("description"):
                w(f"tool '{n}': param '{pn}' has no description")
    return out


def validate_python(src: str) -> list:
    out = []
    try:
        tree = ast.parse(src)
    except SyntaxError as ex:
        return [("error", f"syntax error: {ex}")]
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print":
            if not any(k.arg == "file" for k in node.keywords):
                out.append(("error", f"line {node.lineno}: print() to stdout corrupts stdio transport; use file=sys.stderr"))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            is_tool = any(
                (isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr == "tool")
                or (isinstance(d, ast.Attribute) and d.attr == "tool")
                for d in node.decorator_list
            )
            if not is_tool:
                continue
            if len(ast.get_docstring(node) or "") < 20:
                out.append(("error", f"tool '{node.name}': docstring < 20 chars (it becomes the tool description)"))
            if node.returns is None:
                out.append(("warn", f"tool '{node.name}': missing return annotation"))
            for a in node.args.args + node.args.kwonlyargs:
                if a.annotation is None:
                    out.append(("error", f"tool '{node.name}': param '{a.arg}' lacks a type annotation (schema is derived from it)"))
    return out


def validate_ts(src: str) -> list:
    out = []
    for i, line in enumerate(src.splitlines(), 1):
        if re.search(r"\bconsole\.log\(", line) and not line.lstrip().startswith("//"):
            out.append(("error", f"line {i}: console.log() corrupts stdio transport; use console.error()"))
    if "server.tool(" not in src and "registerTool(" not in src:
        out.append(("warn", "no tool registrations found"))
    return out


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    p = Path(sys.argv[1])
    text = p.read_text(encoding="utf-8")
    if p.suffix == ".json":
        res = validate_spec(json.loads(text))
    elif p.suffix == ".py":
        res = validate_python(text)
    elif p.suffix in (".ts", ".js", ".mjs"):
        res = validate_ts(text)
    else:
        print("unsupported file type")
        return 2
    for lvl, m in res:
        print(f"{lvl.upper():5} {m}")
    if not res:
        print("ok")
    return 1 if any(l == "error" for l, _ in res) else 0


if __name__ == "__main__":
    sys.exit(main())
