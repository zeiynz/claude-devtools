# MCP design patterns

## Contents
1. Tool design
2. Errors
3. Pagination and size
4. Security
5. Transports and config

## 1. Tool design
- Name tools `verb_noun` in snake_case (`search_issues`, not `issues`).
- Write descriptions for the model: what it does, when to use it, what it returns. Include one disambiguating sentence when two tools look similar.
- Prefer few, task-oriented tools over one-per-endpoint. 5-12 tools per server is the sweet spot.
- Every param needs a type and a description; make optional what has a sane default.
- Return text the model can reason over: short, structured (JSON or markdown), no raw HTML dumps.

## 2. Errors
- Catch exceptions inside the tool and return a message that says what went wrong and how to fix the call ("city 'Jakrta' not found; try 'Jakarta'").
- TypeScript: set `isError: true` on the result. Python FastMCP: raise or return an `Error ...` string.

## 3. Pagination and size
- Accept `limit` (default 20) and `cursor`/`offset`. Return `next_cursor` when more exists.
- Truncate large payloads and say so ("showing 20 of 312; pass offset=20").

## 4. Security
- Treat all tool arguments as untrusted: validate paths (no `..`), allowlist hosts, never build shell commands by string concat.
- Secrets come from environment variables, never from arguments or source.
- Read-only by default; make destructive tools explicit (`delete_*`) and describe the side effect.

## 5. Transports and config
- stdio (local): `print`/`console.log` to stdout breaks the protocol. Log to stderr.
- Streamable HTTP (remote): needs auth; do not expose unauthenticated.
- Claude Desktop config: `claude_desktop_config.json` → `mcpServers`. Claude Code: `claude mcp add <name> -- python /abs/server.py`.
- Debug with the MCP Inspector: `npx @modelcontextprotocol/inspector python server.py`.
