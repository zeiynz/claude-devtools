---
name: deep-research
description: Run rigorous multi-source research with an evidence ledger, computed confidence ratings, contradiction checks, and a cited report. Use whenever the user asks to research, investigate, compare, fact-check, verify a claim, do due diligence, write a literature or market review, or "find out everything about" a topic - especially when accuracy and sources matter more than speed.
---

# Deep Research

Produce answers whose every claim is traceable to a source and rated by evidence strength, not by tone.

## Workflow

1. **Frame.** Restate the question in one sentence. List 3-6 sub-questions that, answered, resolve it. If the question is ambiguous in a way that changes the search, ask one question; otherwise proceed with stated assumptions.
2. **Init ledger.** `python scripts/ledger.py init "<topic>"`.
3. **Search breadth first.** Run diverse queries per sub-question (different wording, different source types). Open the best pages fully; snippets alone are not evidence.
4. **Record as you go.** For each useful page: `ledger.py source <url> --title "<t>" --tier <primary|secondary|tertiary|unverified> --date <YYYY-MM-DD>`. Tiers:
   - **primary**: original data, official filings, standards, peer-reviewed papers, first-party docs
   - **secondary**: reputable reporting or analysis that cites primary sources
   - **tertiary**: encyclopedias, summaries, aggregators
   - **unverified**: blogs, forums, social posts, undated pages
5. **Log claims.** `ledger.py claim "<one atomic statement>" --sources S1,S2`. One fact per claim. Confidence is computed from source independence and tier; do not argue with it, find better sources.
6. **Hunt contradictions.** For each important claim, run one search designed to *disprove* it. If credible sources disagree, log with `--disputed` and report both sides.
7. **Check.** `ledger.py check`. Every `GAP` (low confidence) needs either another independent source or an explicit "uncertain" in the report. Stale (>3y) sources are fine for history, suspect for prices, versions, laws, and statistics.
8. **Report.** Follow `references/report-template.md`. Generate the sources table with `ledger.py report --out research/report.md`.

## Rules that protect accuracy
- Two pages that copy each other are one source. Independence = different domains with separate origin.
- Prefer the original over the article about it. Follow citations upstream.
- Numbers need a unit, a date, and a source in the same sentence.
- Say "not found" when it is not found. Never fill a gap from memory and present it as sourced.
- Time-sensitive facts (prices, versions, officeholders, laws): check the date of the source against today.
- Paraphrase. At most one short quotation per source.

## Effort scaling
| Question type | Searches | Ledger |
|---|---|---|
| Single fact | 1-2 | skip |
| Comparison / explainer | 5-10 | yes |
| Due diligence / review | 15-30 | yes, strict check |

## Output
Lead with the bottom line and its confidence. Then findings, uncertainties, sources. Offer the ledger JSON when the user may want to audit it.
