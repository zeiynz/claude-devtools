#!/usr/bin/env python3
"""Generate a working MCP server project from a JSON spec.

Usage:
  scaffold.py spec.json [--out DIR]

Spec:
{
  "name": "weather-mcp",
  "description": "Weather lookups",
  "language": "python" | "typescript",
  "tools": [{
    "name": "get_forecast",
    "description": "Get the forecast for a city. Use when the user asks about weather.",
    "params": [{"name": "city", "type": "string", "description": "City name", "required": true}]
  }]
}
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TYPE_PY = {"string": "str", "integer": "int", "number": "float",
           "boolean": "bool", "array": "list", "object": "dict"}
TYPE_ZOD = {"string": "z.string()", "integer": "z.number().int()", "number": "z.number()",
            "boolean": "z.boolean()", "array": "z.array(z.string())",
            "object": "z.record(z.string(), z.unknown())"}


def _params(tool: dict) -> list:
    # Python requires defaulted params last; keep relative order otherwise.
    return sorted(tool.get("params", []), key=lambda p: not p.get("required", True))


def _q(s: str) -> str:
    return json.dumps(s)  # safe string literal for both Python and TS


# ---------------------------------------------------------------- python
def py_tool(t: dict) -> str:
    ps = _params(t)
    sig = ", ".join(
        f"{p['name']}: {TYPE_PY[p['type']]}" + ("" if p.get("required", True) else " | None = None")
        for p in ps
    )
    args_doc = "\n".join(f"        {p['name']}: {p.get('description', '')}" for p in ps)
    doc = f'    """{t["description"]}' + (f"\n\n    Args:\n{args_doc}\n    " if ps else "") + '"""'
    echo = ", ".join(f'"{p["name"]}": {p["name"]}' for p in ps)
    return f'''@mcp.tool()
def {t["name"]}({sig}) -> str:
{doc}
    try:
        # TODO: implement. Return concise, LLM-friendly text or JSON.
        return json.dumps({{"tool": "{t["name"]}", "args": {{{echo}}}}})
    except Exception as e:  # actionable errors let the model self-correct
        return f"Error in {t["name"]}: {{e}}"
'''


def gen_python(spec: dict, out: Path) -> None:
    tools = "\n\n".join(py_tool(t) for t in spec["tools"])
    (out / "server.py").write_text(f'''#!/usr/bin/env python3
"""{spec.get("description", spec["name"])}"""
import json
import sys  # noqa: F401  (use sys.stderr for logging)

from mcp.server.fastmcp import FastMCP

mcp = FastMCP({_q(spec["name"])})

# NEVER print() to stdout in a stdio server: it corrupts the JSON-RPC stream.
# Log to stderr instead: print("...", file=sys.stderr)


{tools}

if __name__ == "__main__":
    mcp.run()  # stdio transport
''', encoding="utf-8")
    (out / "pyproject.toml").write_text(f'''[project]
name = {_q(spec["name"])}
version = "0.1.0"
description = {_q(spec.get("description", ""))}
requires-python = ">=3.10"
dependencies = ["mcp>=1.2"]
''', encoding="utf-8")
    (out / "test_server.py").write_text('''import asyncio

import server


def test_tools_registered():
    tools = asyncio.run(server.mcp.list_tools())
    assert len(tools) > 0
    assert all(t.description for t in tools)
''', encoding="utf-8")
    cfg = {"mcpServers": {spec["name"]: {"command": "python", "args": ["/ABSOLUTE/PATH/server.py"]}}}
    (out / "README.md").write_text(
        f"# {spec['name']}\n\n{spec.get('description', '')}\n\n## Run\n```bash\npip install mcp\npython server.py\n```\n\n"
        f"## Claude Desktop / Claude Code config\n```json\n{json.dumps(cfg, indent=2)}\n```\n", encoding="utf-8")


# ------------------------------------------------------------ typescript
def ts_tool(t: dict) -> str:
    ps = _params(t)
    shape = ",\n".join(
        f"    {p['name']}: {TYPE_ZOD[p['type']]}"
        + ("" if p.get("required", True) else ".optional()")
        + f".describe({_q(p.get('description', ''))})"
        for p in ps
    )
    names = ", ".join(p["name"] for p in ps)
    destructure = "{ " + names + " }" if ps else ""
    echo = ", ".join(p["name"] for p in ps)
    shape_block = f"{{\n{shape}\n  }}" if ps else "{}"
    return f'''server.tool(
  {_q(t["name"])},
  {_q(t["description"])},
  {shape_block},
  async ({destructure}) => {{
    try {{
      // TODO: implement. Return concise, LLM-friendly text.
      return {{ content: [{{ type: "text", text: JSON.stringify({{ tool: {_q(t["name"])}, args: {{ {echo} }} }}) }}] }};
    }} catch (e) {{
      return {{ isError: true, content: [{{ type: "text", text: `Error in {t["name"]}: ${{(e as Error).message}}` }}] }};
    }}
  }}
);
'''


def gen_typescript(spec: dict, out: Path) -> None:
    (out / "src").mkdir(exist_ok=True)
    tools = "\n".join(ts_tool(t) for t in spec["tools"])
    (out / "src" / "index.ts").write_text(f'''import {{ McpServer }} from "@modelcontextprotocol/sdk/server/mcp.js";
import {{ StdioServerTransport }} from "@modelcontextprotocol/sdk/server/stdio.js";
import {{ z }} from "zod";

const server = new McpServer({{ name: {_q(spec["name"])}, version: "0.1.0" }});

// NEVER console.log() in a stdio server: it corrupts the JSON-RPC stream. Use console.error().

{tools}
await server.connect(new StdioServerTransport());
''', encoding="utf-8")
    (out / "package.json").write_text(json.dumps({
        "name": spec["name"], "version": "0.1.0", "type": "module",
        "bin": {spec["name"]: "dist/index.js"},
        "scripts": {"build": "tsc", "start": "node dist/index.js"},
        "dependencies": {"@modelcontextprotocol/sdk": "^1.0.0", "zod": "^3.23.0"},
        "devDependencies": {"typescript": "^5.4.0", "@types/node": "^20.0.0"},
    }, indent=2) + "\n", encoding="utf-8")
    (out / "tsconfig.json").write_text(json.dumps({"compilerOptions": {
        "target": "ES2022", "module": "Node16", "moduleResolution": "Node16",
        "outDir": "dist", "rootDir": "src", "strict": True, "esModuleInterop": True, "skipLibCheck": True},
        "include": ["src"]}, indent=2) + "\n", encoding="utf-8")
    cfg = {"mcpServers": {spec["name"]: {"command": "node", "args": ["/ABSOLUTE/PATH/dist/index.js"]}}}
    (out / "README.md").write_text(
        f"# {spec['name']}\n\n{spec.get('description', '')}\n\n## Run\n```bash\nnpm install && npm run build && npm start\n```\n\n"
        f"## Claude Desktop / Claude Code config\n```json\n{json.dumps(cfg, indent=2)}\n```\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    spec = json.loads(a.spec.read_text(encoding="utf-8"))

    sys.path.insert(0, str(Path(__file__).parent))
    from validate import validate_spec
    problems = [m for lvl, m in validate_spec(spec) if lvl == "error"]
    if problems:
        print("Spec errors:\n  - " + "\n  - ".join(problems), file=sys.stderr)
        return 1

    out = a.out or Path(spec["name"])
    out.mkdir(parents=True, exist_ok=True)
    {"python": gen_python, "typescript": gen_typescript}[spec.get("language", "python")](spec, out)
    print(f"generated {spec.get('language', 'python')} MCP server in {out}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
