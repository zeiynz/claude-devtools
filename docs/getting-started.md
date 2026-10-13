# Getting started

## Install

| Where | How |
|---|---|
| **Claude Code** (all projects) | `./install.sh` → `~/.claude/skills/` |
| **Claude Code** (one project) | `./install.sh --project` → `./.claude/skills/` |
| **claude.ai** | `make package`, then upload each `dist/*.skill` in Settings → Capabilities → Skills |
| **Manual** | Copy any `skills/<name>/` folder into a skills directory |

Restart Claude Code after installing. Skills need a code-execution environment to run their scripts (Claude Code, or claude.ai with code execution enabled). Requirements: Python 3.9+; Node 18+ only for the optional dashboard runtime test and for testing generated TypeScript servers.

## How triggering works
Claude sees only each skill's `name` + `description` until a task matches. Then it loads `SKILL.md`, and runs `scripts/` or reads `references/` only if needed. You never invoke skills by name; describe the task.

## Trigger prompts

| Skill | Say something like |
|---|---|
| skill-factory | "Turn this workflow into a skill", "why doesn't my skill trigger?" |
| mcp-generator | "Build an MCP server so Claude can query my Postgres", "my MCP server disconnects" |
| deep-research | "Research X and give me sourced, confidence-rated findings" |
| repo-doctor | "Is my repo ready to open-source?", "scan for leaked keys" |
| dashboard-builder | "Make a dashboard from sales.csv" |

## Verify the install
```bash
python skills/skill-factory/scripts/lint_skill.py skills   # all 5 should be ok, score=100
python -m unittest discover -s tests                     # 14 tests
```
