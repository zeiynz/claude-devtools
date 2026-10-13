# dashboard-builder

CSV/JSON → one offline HTML file with KPIs, charts, filters, search, sortable table, CSV export. No CDN, no dependencies.

## Command
```bash
python skills/dashboard-builder/scripts/build_dashboard.py data.csv --title "Q3 Sales" --out dashboard.html
```
| Option | Default | Meaning |
|---|---|---|
| `--title` | file name | Page title |
| `--out` | `dashboard.html` | Output path |
| `--max-rows` | 50000 | Row cap (all rows are embedded in the HTML) |

Input: `.csv` (UTF-8, with or without BOM) or `.json` (array of objects, or an object whose first array value is the rows).

## Type inference
| Type | Rule |
|---|---|
| number | ≥ 90% parse (`1234`, `-5.2`, `1,234,000`) |
| date | ≥ 90% start with `YYYY-MM-DD` or `YYYY/MM/DD` |
| category | ≤ 30 unique values or ≤ 20% unique |
| text | everything else |

## Output
- KPI cards: row count, sum/avg of up to 3 numeric columns
- Line chart over the first date column (monthly if ≥ 3 months, else daily)
- Top-10 bars for the first two category columns; histogram of the measure
- Measure selector, category dropdowns, date range, free-text search
- Sortable, paged table; export of the **filtered** rows to CSV
- Light/dark by system preference; values escaped; safe against `</script>` in data

## Customize
Edit `scripts/template.html`. Add a chart: write `function myChart(rs){ return card("Title", "<svg…>") }` and append it in `renderCharts`.

## Limits
Year-first dates only. One time-series (first date column). Everything is client-side, so very large datasets should be aggregated before building. The file contains your data in plain text; share accordingly.
