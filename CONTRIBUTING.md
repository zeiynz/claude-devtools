# Contributing

1. Fork, then branch: `git checkout -b feat/my-skill`.
2. Scaffold: `python skills/skill-factory/scripts/new_skill.py my-skill "What it does. Use when ..."`.
3. Rules for a skill to be merged:
   - Description states what it does **and when to use it** (lint enforces a trigger phrase).
   - `SKILL.md` ≤ 500 lines; detail goes in `references/`.
   - Deterministic work lives in `scripts/`, stdlib-only, with `--help`.
   - At least one test in `tests/test_all.py`.
   - No network calls, no telemetry, nothing that surprises the user relative to the description.
4. Before opening a PR: `make lint test audit` must pass.
5. PR description: what problem it solves, one real example of input → output.
