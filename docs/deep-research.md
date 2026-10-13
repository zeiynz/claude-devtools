# deep-research

An evidence ledger that makes research auditable: sources are tiered, claims cite sources, and **confidence is computed, not asserted**.

## Commands
```bash
L=skills/deep-research/scripts/ledger.py
python $L init "Is X safe?"
python $L source https://who.int/x --title "WHO report" --tier primary --date 2026-01-10
python $L claim "X is approved for adults" --sources S1,S2
python $L check [--max-age-years 3] [--strict]
python $L report --out research/report.md
```
Data lives in `research/ledger.json` (change with `--file`).

## Confidence
| Level | Condition |
|---|---|
| high | ≥ 2 independent domains **and** ≥ 1 primary source |
| medium | ≥ 2 independent domains **or** ≥ 1 primary source |
| low | anything else, or the claim is `--disputed` |

Independence is by registrable domain: `bbc.co.uk` and `news.bbc.co.uk` count once.

## Source tiers
`primary` (original data, filings, papers, first-party docs) · `secondary` (reporting that cites primaries) · `tertiary` (encyclopedias, aggregators) · `unverified` (blogs, forums, undated).

## `check` flags
`GAP` low-confidence claim · `WARN` source older than N years / undated / unverified / recorded but never cited. `--strict` exits 1 if any GAP exists.

## Limits
The ledger enforces discipline; it does not judge whether a source is truthful, and tier labels are your judgment. Domain independence does not detect two sites repeating one press release.
