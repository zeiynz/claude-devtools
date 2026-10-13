# mcp-generator

Spec → working MCP server (Python FastMCP or TypeScript SDK) → validated.

## Spec format
```json
{
  "name": "weather-mcp",
  "description": "Weather lookups",
  "language": "python",
  "tools": [{
    "name": "get_forecast",
    "description": "Get the forecast for a city. Use when the user asks about weather.",
    "params": [
      {"name": "city", "type": "string", "description": "City name", "required": true},
      {"name": "days", "type": "integer", "description": "Days ahead", "required": false}
    ]
  }]
}
```
Types: `string integer number boolean array object`.

## Commands
```bash
python skills/mcp-generator/scripts/validate.py spec.json                  # check the spec
python skills/mcp-generator/scripts/scaffold.py spec.json --out ./server   # generate project
python skills/mcp-generator/scripts/validate.py ./server/server.py         # check the code
```

## Generated
| Language | Files |
|---|---|
| python | `server.py`, `pyproject.toml`, `test_server.py`, `README.md` (with client config) |
| typescript | `src/index.ts`, `package.json`, `tsconfig.json`, `README.md` |

Each tool is a stub that echoes its arguments and has error handling. Replace the `TODO`.

## Validator rules
| Target | Rule |
|---|---|
| spec | kebab-case server name; snake_case tool names; no keywords; no duplicates; description ≥ 20 chars; valid types; warns above 15 tools |
| `.py` | no `print()` to stdout; tool docstring ≥ 20 chars; every param annotated; return annotated |
| `.ts` | no `console.log()` (stdout corrupts the stdio protocol) |

## Test the result
```bash
npx @modelcontextprotocol/inspector python server.py
```
Generated code was checked for syntax and validator compliance, not run against a live MCP client in CI; pin SDK versions after confirming the current API.
