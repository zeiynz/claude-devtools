# skill-factory

Create → lint → test → package Claude skills.

| Script | Purpose |
|---|---|
| `new_skill.py NAME "desc" [--out DIR]` | Scaffold a skill folder that lints clean |
| `lint_skill.py PATH [--json]` | Validate one skill, or every skill under a folder |
| `package_skill.py PATH [--out dist]` | Lint, then zip to `<name>.skill` |

## Lint rules
| Level | Rule |
|---|---|
| error | `SKILL.md` missing, frontmatter missing, `name`/`description` missing |
| error | name not kebab-case or > 64 chars; description > 1024 chars |
| error | `scripts/`, `references/`, `assets/` path mentioned in the body does not exist |
| warn | name ≠ folder name; description < 80 chars; no trigger phrase ("use when", "whenever", …) |
| warn | body > 500 lines; reference file > 300 lines without a table of contents |

Score = 100 − 25 × errors − 5 × warnings. Exit code 1 on any error (CI-friendly).

## Example
```bash
python skills/skill-factory/scripts/new_skill.py invoice-parser "Extract fields from invoices. Use when the user uploads invoices or asks for totals."
python skills/skill-factory/scripts/lint_skill.py skills/invoice-parser
python skills/skill-factory/scripts/package_skill.py skills/invoice-parser
```

## Limits
Lint checks structure, not whether the instructions are good. Use the trigger-test procedure in `SKILL.md` (10 should-trigger / 10 near-miss prompts) to measure description quality.
