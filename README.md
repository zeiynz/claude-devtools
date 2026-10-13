<div align="center">

# Claude Devtools

**Five production-grade skills that turn Claude into a skill factory, MCP builder, research auditor, repo doctor, and dashboard generator.**

Zero dependencies · Offline-capable · Tested · Works in Claude Code and claude.ai

[![CI](https://github.com/zeiynz/claude-devtools/actions/workflows/ci.yml/badge.svg)](https://github.com/zeiynz/claude-devtools/actions)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Deps](https://img.shields.io/badge/dependencies-0-brightgreen)

</div>

---

## Why

Most skills are a prompt in a markdown file. These pair **judgment** (`SKILL.md`: when and how Claude should act) with **deterministic scripts** (parsing, validation, scoring) so results are repeatable instead of improvised. Each one solves a job people actually do weekly, and each is verified by tests.

## What's inside

| Skill | What it does | Key script |
|---|---|---|
| 🛠 [**skill-factory**](docs/skill-factory.md) | Create, lint, test, and package skills. Catches broken references, weak descriptions, oversized bodies. | `lint_skill.py` `package_skill.py` |
| 🔌 [**mcp-generator**](docs/mcp-generator.md) | JSON spec → working MCP server (Python or TypeScript) + validator for the bugs that break stdio servers. | `scaffold.py` `validate.py` |
| 🔎 [**deep-research**](docs/deep-research.md) | Evidence ledger: tiered sources, atomic claims, **computed** confidence, contradiction hunting, cited report. | `ledger.py` |
| 🩺 [**repo-doctor**](docs/repo-doctor.md) | Score a repo 0-100, detect committed secrets (masked), prioritized fixes, README badge. | `audit.py` |
| 📊 [**dashboard-builder**](docs/dashboard-builder.md) | CSV/JSON → one offline HTML dashboard: KPIs, charts, filters, search, sortable table, export. | `build_dashboard.py` |

## Install

```bash
git clone https://github.com/zeiynz/claude-devtools.git && cd claude-devtools
./install.sh              # Claude Code, all projects  (~/.claude/skills)
./install.sh --project    # Claude Code, this project only
make package              # claude.ai: upload dist/*.skill in Settings → Capabilities → Skills
```

Restart Claude Code. Nothing else to configure. Requires Python 3.9+.

## Use it

You never call a skill by name. Describe the task:

| Say | Skill that activates |
|---|---|
| "Turn this workflow into a reusable skill" | skill-factory |
| "Build an MCP server so Claude can query my database" | mcp-generator |
| "Research this and give me sourced, confidence-rated findings" | deep-research |
| "Is my repo ready to open-source? Check for leaked keys" | repo-doctor |
| "Make a dashboard from sales.csv" | dashboard-builder |

## See it work

**repo-doctor** finds a planted key and never prints it in full:
```text
$ python skills/repo-doctor/scripts/audit.py my-repo
Repo health: 69/100 (D)  my-repo

  PASS  LICENSE present
  PASS  Tests exist
  FAIL  CONTRIBUTING present  -> Add CONTRIBUTING.md
  ...
POSSIBLE SECRETS (1): rotate them, then purge from history
  leak.py:1  AWS access key  AKIA…(20 chars)
```

**deep-research** computes confidence from source independence, not from vibes:
```text
$ ledger.py claim "Fact A" --sources S1,S2     # primary + independent domain
C1 confidence=high
$ ledger.py claim "Fact B" --sources S3        # one unverified blog
C2 confidence=low
$ ledger.py check --strict                     # exits 1 while gaps remain
GAP  C2 low confidence: Fact B
```

**dashboard-builder** infers the schema, then builds a single file:
```text
$ build_dashboard.py sales.csv --title "Q3 Sales"
wrote dashboard.html (400 rows) [order_id:text, date:date, region:category, product:category, units:number, revenue:number, note:text]
```

**mcp-generator** catches the #1 reason MCP servers die:
```text
$ validate.py server.py
ERROR line 2: print() to stdout corrupts stdio transport; use file=sys.stderr
```

## How skills work

1. Claude reads only each skill's `name` + `description` at start (cheap).
2. When your task matches, it loads that `SKILL.md` (the playbook).
3. It runs `scripts/` (output only, code stays out of context) and reads `references/` only if needed.

This is *progressive disclosure*: many skills installed, tiny context cost.

## Design principles

- **Scripts for facts, prose for judgment.** Confidence ratings, lint scores, and schemas are computed, not guessed.
- **Zero dependencies.** Python stdlib only. `pip install` is never step one.
- **Safe by default.** Secrets are masked, HTML is escaped, no network calls, no telemetry.
- **Honest limits.** Every doc ends with what the tool can't do.
- **Dogfooded.** CI runs repo-doctor and skill-factory's linter on this repo.

## Repo layout

```text
skills/<name>/
├── SKILL.md        # trigger description + playbook (≤500 lines)
├── scripts/        # deterministic, stdlib-only, --help on every script
└── references/     # loaded only when needed
docs/               # one page per skill
tests/              # 14 tests (stdlib unittest; node optional)
```

## Develop

```bash
make test       # 14 tests, ~1s
make lint       # lint every skill
make audit      # dogfood: score this repo
make package    # build dist/*.skill
```

Add a skill: `python skills/skill-factory/scripts/new_skill.py my-skill "Does X. Use when ..."` → edit → `make lint test`. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Docs

[Getting started](docs/getting-started.md) · [skill-factory](docs/skill-factory.md) · [mcp-generator](docs/mcp-generator.md) · [deep-research](docs/deep-research.md) · [repo-doctor](docs/repo-doctor.md) · [dashboard-builder](docs/dashboard-builder.md)

## License

[MIT](LICENSE)
