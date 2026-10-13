# repo-doctor

Score a repo 0-100, find committed secrets, and list fixes by impact. Stdlib only.

## Commands
```bash
python skills/repo-doctor/scripts/audit.py .                  # text
python skills/repo-doctor/scripts/audit.py . --md             # markdown + badge
python skills/repo-doctor/scripts/audit.py . --json           # tooling
python skills/repo-doctor/scripts/audit.py . --fail-under 90  # CI gate (exit 1)
```

## Checks
| Check | Weight |
|---|---|
| Tests exist | 15 |
| CI configured | 12 |
| README exists / substantive (≥ 40 lines) / has install+usage | 10 / 5 / 8 |
| LICENSE | 10 |
| `.env` not exposed (exists and not gitignored = fail) | 10 |
| `.gitignore`, lockfile per manifest, no files > 5 MB | 5 each |
| CONTRIBUTING | 4 |
| SECURITY, CHANGELOG | 3 each |

Each committed secret subtracts 15 points (max 45).

## Secret patterns
AWS access keys · GitHub tokens · Slack tokens · PEM private keys · generic `api_key/secret/token/password = "<16+ chars>"`. Lines containing `example`, `changeme`, `your_`, `placeholder`, `dummy` are skipped. Matches are **masked** in output (first 4 chars + length).

## Limits
- Working tree only; **git history is not scanned**. Use gitleaks/trufflehog for history.
- Pattern-based: misses custom formats, can false-positive. Read the flagged line.
- If a secret is found: rotate first, purge second (see `skills/repo-doctor/references/fixes.md`).

## CI badge
`audit.py . --md` prints a shields.io badge URL with your score.
