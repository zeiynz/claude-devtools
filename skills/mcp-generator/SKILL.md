---
name: mcp-generator
description: Design, scaffold, validate, and debug Model Context Protocol (MCP) servers in Python (FastMCP) or TypeScript. Use whenever the user wants to build an MCP server, expose an API/database/CLI/internal tool to Claude, wrap a service as tools, fix an MCP server that returns garbage or won't connect, or review MCP tool design - even if they just say "let Claude call my API" or "make a connector".
---

# MCP Generator

Turn "I want Claude to use X" into a working, validated MCP server.

## Workflow

1. **Define the tools, not the endpoints.** Ask what tasks the user wants Claude to accomplish, then design 3-12 task-oriented tools. Read `references/patterns.md` before finalizing names, descriptions, and error handling.
2. **Write the spec** (`spec.json`). Format is in the header of `scripts/scaffold.py`. Choose `python` unless the user's stack is Node.
3. **Validate the spec:** `python scripts/validate.py spec.json`. Fix errors; they predict real failures (vague descriptions cause wrong tool selection; invalid identifiers break codegen).
4. **Scaffold:** `python scripts/scaffold.py spec.json --out ./my-server`. Output runs immediately with echo stubs.
5. **Implement each `TODO`.** Keep results short and structured. Catch exceptions and return actionable messages.
6. **Validate the code:** `python scripts/validate.py my-server/server.py` (or `src/index.ts`). It catches the #1 cause of broken stdio servers: writing to stdout.
7. **Test with the Inspector:** `npx @modelcontextprotocol/inspector python server.py`. Call each tool once with valid and invalid input.
8. **Register** with the user's client (config snippet is in the generated README).

## Decisions

| Question | Default |
|---|---|
| Language | Python/FastMCP (least boilerplate); TypeScript if the user's code is Node |
| Transport | stdio for local; Streamable HTTP + auth for remote |
| Auth/secrets | environment variables, never tool arguments |
| Destructive actions | separate, explicitly named tools; say the side effect in the description |

## Debugging checklist
- **Server connects then dies / "invalid JSON":** something printed to stdout. Run `validate.py`.
- **Claude never calls the tool:** description doesn't say *when* to use it. Rewrite it.
- **Claude passes wrong args:** param descriptions missing, or types too loose.
- **Tool times out:** return early with a job id, or paginate.
- **Works in Inspector, not in client:** use absolute paths in config; check the client's log for the real stderr.

## Output to user
Report: tool list (name → one line), the exact config snippet, how to test, and any assumptions made. Do not claim the server works until step 7 or an equivalent check has run.
