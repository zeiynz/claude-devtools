---
name: repo-doctor
description: Audit a code repository for health and release-readiness - README quality, license, CI, tests, lockfiles, oversized files, exposed .env, and committed secrets - then produce a scored report with prioritized fixes. Use whenever the user wants to review, audit, polish, or prepare a repo for open-source release or GitHub launch, asks "is my repo ready", "why won't people star/use my project", wants a security sweep for leaked keys, or needs a health badge.
---

# Repo Doctor

Score a repo 0-100, find leaked secrets, and fix the highest-impact gaps first.

## Workflow

1. **Run the audit** on the repo root: `python scripts/audit.py <path>`. Use `--md` for a report with a badge, `--json` for tooling, `--fail-under 80` for CI gating.
2. **Triage in this order** (impact per minute):
   1. **Secrets.** Any hit outranks everything. Tell the user to rotate the credential first, then purge it from history. Recipe in `references/fixes.md`. Hits are masked; never print the full value.
   2. **Exposed `.env`**, then **license** (without one, nobody can legally use the code), **README**, **CI + tests**, then the rest.
3. **Verify hits by reading the line.** The scanner is pattern-based; test fixtures and docs can false-positive. Confirm before alarming the user.
4. **Fix, don't just list.** Offer to create the missing files (LICENSE, CONTRIBUTING, CI workflow, .gitignore) and write the README. Use the recipes in `references/fixes.md`.
5. **Re-run the audit** and report the before/after score.

## README review (beyond the score)
The score checks presence, not quality. Read the README and judge:
- Can a stranger understand what this does in 10 seconds?
- Is there a demo (screenshot, GIF, sample output)?
- Does install work in ≤3 commands, copy-paste?
- Is there one realistic usage example?

## Output format
```
Score: 62 → 91 (D → A)
Critical: <secrets / .env, or "none">
Fixed: <bullets of what changed>
Still open: <bullets, ordered by impact>
```

## Limits
Pattern matching finds common key formats, not every secret; absence of hits is not proof of safety. It does not scan git history, only the working tree. For history, recommend a dedicated scanner (gitleaks, trufflehog).
