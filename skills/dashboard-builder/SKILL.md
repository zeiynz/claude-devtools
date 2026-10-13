---
name: dashboard-builder
description: Turn CSV or JSON data into a single-file interactive HTML dashboard (KPI cards, time-series, top-N bars, histogram, filters, search, sortable table, CSV export) that works offline with no CDN. Use whenever the user has tabular data and wants a dashboard, report, visual summary, charts, "something I can send to my boss", or an explorable view of a spreadsheet export - even if they never say "dashboard".
---

# Dashboard Builder

Data file in, one self-contained `.html` out. Opens by double-click, works offline, shareable as an email attachment.

## Workflow

1. **Inspect the data first.** Read the header and a few rows. Note the grain (what is one row?), the main measure(s), the date column, and the key categories. Ask the user only if the intended measure is ambiguous.
2. **Clean if needed.** Fix obviously broken input before building: mixed date formats, currency symbols in number columns, summary/total rows at the bottom, duplicate header rows. Save the cleaned file separately; never overwrite the original.
3. **Build:** `python scripts/build_dashboard.py data.csv --title "Q3 Sales" --out dashboard.html`
4. **Read the printed schema** (`name:type` per column). If a column is mis-typed (e.g. IDs detected as numbers, or a category detected as text), fix the data (prefix IDs with a letter, or trim unique values) and rebuild.
5. **Verify** by summarizing 2-3 numbers from the dashboard against the source (row count, one total). State the match in your answer.
6. **Deliver** the HTML file and 3-5 bullet insights drawn from the data (largest segment, trend direction, outliers). Insights must be numbers you checked, not impressions.

## What gets generated

| Detected type | Rule | Used for |
|---|---|---|
| number | ≥90% parse as numbers (thousand separators OK) | KPIs (sum/avg), measure selector, histogram, bar/line values |
| date | ≥90% start with `YYYY-MM-DD` or `YYYY/MM/DD` | time-series (monthly if ≥3 months, else daily), date-range filter |
| category | ≤30 unique values or ≤20% unique | dropdown filters, top-10 bar charts (first two) |
| text | everything else | search and table only |

## Limits and honest caveats
- Dates must be year-first. Convert `DD/MM/YYYY` beforehand; otherwise the column falls back to text.
- Default cap is 50,000 rows (`--max-rows`); the full dataset is embedded in the HTML, so file size grows with it. For millions of rows, aggregate first.
- Only the first date column drives the time-series; only the first two categories get bar charts. Filters work for all categories with ≤40 values.
- Data is embedded as plain JSON in the file. Do not share dashboards built from sensitive data.

## Customizing
Layout and styles live in `scripts/template.html` (CSS variables at the top control colors and dark mode). Add charts by writing a function that returns `card(title, svgString)` and calling it in `renderCharts`.
