// Runtime smoke test for dashboard-builder output using a minimal DOM stub (no browser needed).
// Usage: node dashboard_smoke.js dashboard.html EXPECTED_ROWS
const fs = require("fs"), vm = require("vm");
const html = fs.readFileSync(process.argv[2], "utf8");
const expectedRows = process.argv[3];
const payload = html.match(/<script id="payload" type="application\/json">([\s\S]*?)<\/script>/)[1].replace(/<\\\//g, "</");
const code = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const els = {};
const mk = id => els[id] = els[id] || { id, innerHTML: "", textContent: "", value: "", dataset: {} };
const doc = {
  getElementById: id => id === "payload" ? { textContent: payload } : mk(id),
  querySelectorAll: () => [],
  createElement: () => ({ click() { } }),
};
const ctx = { document: doc, URL: { createObjectURL: () => "blob:x" }, Blob: class { }, console };
vm.createContext(ctx);
vm.runInContext(code + "\n;globalThis.S_ = S; globalThis.update_ = update; globalThis.filtered_ = filtered; globalThis.cats_ = cats;", ctx);
const fail = m => { console.error("FAIL:", m); process.exit(1); };
const out = k => els[k].innerHTML;

if (!out("kpis").includes(`<b>${Number(expectedRows).toLocaleString()}</b>`)) fail("row KPI missing " + expectedRows);
if (!out("table").includes("<table")) fail("table not rendered");
if (!out("controls").includes("Export CSV")) fail("controls not rendered");

if (ctx.cats_.length) {                       // filter path
  const c = ctx.cats_[0];
  const v = String(ctx.filtered_()[0][c]);
  ctx.S_.f[c] = v; ctx.update_();
  const n = ctx.filtered_().length;
  if (!(n > 0 && n <= Number(expectedRows))) fail("filter produced bad count " + n);
}
ctx.S_.f = {}; ctx.S_.q = "zzzz-no-match-zzzz"; ctx.update_();      // empty-state path
if (!out("kpis").includes("<b>0</b>")) fail("empty search should give 0 rows");
ctx.S_.q = ""; ctx.S_.measure = "__count"; ctx.S_.sort = Object.keys(ctx.filtered_()[0])[0]; ctx.S_.dir = -1; ctx.update_();
if (!out("table").includes("▼")) fail("sort indicator missing");
if (out("table").includes("</script>")) fail("hostile cell not escaped");
console.log("smoke ok");
