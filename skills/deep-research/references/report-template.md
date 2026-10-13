# Report template

Use this exact structure for the final answer when the user wants a research report.

```markdown
# <Question as a title>

**Bottom line:** 2-3 sentences that directly answer the question, with the confidence level.

## Key findings
1. <Finding> - <confidence> [S1][S3]
2. ...

## Evidence and nuance
Short sections only where the evidence is non-obvious: conflicts between sources, caveats, scope limits.

## What is uncertain
- Claims rated low, disputed points, and what evidence would settle them.

## Sources
Table from `ledger.py report` (tier, title, date, URL).
```

Rules:
- Every factual sentence maps to a ledger claim ID or a cited source.
- Paraphrase; quote at most one short phrase per source, in quotation marks.
- Lead with the answer. No methodology essay unless asked.
