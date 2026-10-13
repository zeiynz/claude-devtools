---
name: skill-factory
description: Create, lint, test, and package Claude skills (SKILL.md folders) with a measurable quality loop. Use whenever the user wants to create a skill, turn a workflow or conversation into a reusable skill, improve or debug a skill that doesn't trigger, review a skill, write trigger evals, or package a skill as a .skill file for claude.ai or Claude Code - even if they only say "make this repeatable" or "save this as a skill".
---

# Skill Factory

Build skills that trigger reliably and stay small. Loop: **capture → draft → lint → test → iterate → package**.

## 1. Capture intent
If the conversation already contains a workflow, extract it first (tools used, steps, user corrections, output format). Then confirm only what is missing:
1. What should Claude be able to do?
2. What phrases/contexts should trigger it?
3. What is the exact output format?
4. Is output objectively checkable? (yes → write tests; no, e.g. writing style → skip tests)

## 2. Draft
Create the folder: `python scripts/new_skill.py <kebab-name> "<description>"`.

Rules that matter (and why):
- **Description is the trigger.** Claude decides to load a skill from name + description alone. State what it does AND when to use it, and be pushy: list synonyms and adjacent phrasings, because skills under-trigger by default. Max 1024 chars.
- **Body ≤ 500 lines.** The body is loaded on every trigger; extra length costs context every time. Push detail into `references/` and say *when* to read each file.
- **Scripts for deterministic work.** Parsing, validation, scaffolding, scoring belong in `scripts/` (executed without loading into context). Judgment belongs in SKILL.md.
- **Imperative voice, explain why.** "Check X because Y breaks otherwise" generalizes; shouty MUST lists do not.
- **Define output formats with a literal template** when the format matters.
- **Never include** malware, exfiltration, or surprising behavior. A skill must do what its description says.

## 3. Lint
```bash
python scripts/lint_skill.py skills/my-skill        # one skill
python scripts/lint_skill.py skills --json          # all skills, machine-readable
```
Checks: frontmatter, kebab-case name, description length/trigger phrase, body size, broken `scripts/` `references/` `assets/` paths, long references without a table of contents. Fix every error; treat warnings as review items. Score = 100 − 25·errors − 5·warnings.

## 4. Test
Write 3 realistic prompts a real user would type (not "read file X" - trivial tasks never trigger skills). Save as `evals/evals.json`:
```json
{"skill_name": "my-skill", "evals": [
  {"id": 1, "prompt": "...", "expected_output": "...", "files": []}
]}
```
Run each prompt with the skill, show prompt + output to the user, collect feedback. Add assertions only for objectively checkable outputs.

**Trigger test:** write 10 prompts that should trigger and 10 near-misses that should not (same keywords, different intent). If a should-trigger prompt fails to load the skill, add its phrasing to the description. If a near-miss loads it, narrow the description.

## 5. Iterate
Generalize from feedback instead of patching one example. Remove instructions that did no work. Re-lint after each edit.

## 6. Package
```bash
python scripts/package_skill.py skills/my-skill --out dist   # → dist/my-skill.skill
```
Packaging refuses to run if lint reports errors. Hand the `.skill` file to the user; they upload it in claude.ai (Settings → Capabilities → Skills) or unzip into `~/.claude/skills/` for Claude Code.

## Anti-patterns
| Symptom | Fix |
|---|---|
| Never triggers | Description lacks user phrasings; add "Use whenever..." with synonyms |
| Triggers on everything | Description too broad; add explicit exclusions |
| Claude ignores half the body | Body too long; move detail to `references/` |
| Output format drifts | Add a literal template or a script that emits it |
