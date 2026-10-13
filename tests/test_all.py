"""Test suite. Run: python -m unittest discover -s tests -v   (stdlib only)"""
import csv
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SK = ROOT / "skills"
PY = sys.executable


def run(*args, cwd=None):
    return subprocess.run([PY, *map(str, args)], capture_output=True, text=True, cwd=cwd)


class TestSkillFactory(unittest.TestCase):
    def test_all_skills_lint_clean(self):
        r = run(SK / "skill-factory/scripts/lint_skill.py", SK, "--json")
        self.assertEqual(r.returncode, 0, r.stdout)
        res = json.loads(r.stdout)
        self.assertEqual(len(res), 5)
        for s in res:
            self.assertEqual([i for i in s["issues"] if i["level"] == "error"], [], s["skill"])
            self.assertGreaterEqual(s["score"], 90, s["skill"])

    def test_lint_catches_problems(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "Bad_Name"
            d.mkdir()
            (d / "SKILL.md").write_text("---\nname: Bad_Name\ndescription: short\n---\nsee scripts/missing.py\n")
            r = run(SK / "skill-factory/scripts/lint_skill.py", d, "--json")
            self.assertEqual(r.returncode, 1)
            msgs = " ".join(i["msg"] for i in json.loads(r.stdout)[0]["issues"])
            self.assertIn("kebab-case", msgs)
            self.assertIn("broken reference: scripts/missing.py", msgs)

    def test_new_and_package(self):
        with tempfile.TemporaryDirectory() as t:
            r = run(SK / "skill-factory/scripts/new_skill.py", "my-skill",
                    "Does a thing. Use when the user wants the thing done properly and quickly.", "--out", t)
            self.assertEqual(r.returncode, 0, r.stderr)
            r = run(SK / "skill-factory/scripts/package_skill.py", Path(t) / "my-skill", "--out", Path(t) / "dist")
            self.assertEqual(r.returncode, 0, r.stderr)
            with zipfile.ZipFile(Path(t) / "dist/my-skill.skill") as z:
                self.assertIn("my-skill/SKILL.md", z.namelist())


class TestMcpGenerator(unittest.TestCase):
    SPEC = {"name": "demo-mcp", "description": "Demo", "language": "python", "tools": [
        {"name": "get_item", "description": "Fetch one item by id. Use when the user names an item.",
         "params": [{"name": "limit", "type": "integer", "description": "max", "required": False},
                    {"name": "item_id", "type": "string", "description": "id", "required": True}]}]}

    def gen(self, lang):
        t = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, t, True)
        spec = dict(self.SPEC, language=lang)
        (t / "spec.json").write_text(json.dumps(spec))
        r = run(SK / "mcp-generator/scripts/scaffold.py", t / "spec.json", "--out", t / "out")
        self.assertEqual(r.returncode, 0, r.stderr)
        return t / "out"

    def test_python_output_compiles_and_validates(self):
        out = self.gen("python")
        src = (out / "server.py").read_text()
        compile(src, "server.py", "exec")
        self.assertIn("def get_item(item_id: str, limit: int | None = None)", src)  # required first
        self.assertEqual(run(SK / "mcp-generator/scripts/validate.py", out / "server.py").returncode, 0)

    def test_typescript_output(self):
        out = self.gen("typescript")
        src = (out / "src/index.ts").read_text()
        self.assertIn("z.number().int().optional()", src)
        self.assertTrue((out / "package.json").exists() and (out / "tsconfig.json").exists())
        self.assertEqual(run(SK / "mcp-generator/scripts/validate.py", out / "src/index.ts").returncode, 0)

    def test_validator_rejects_bad_spec_and_stdout_print(self):
        t = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, t, True)
        bad = {"name": "Bad Name", "tools": [{"name": "class", "description": "x", "params": []}]}
        (t / "s.json").write_text(json.dumps(bad))
        self.assertEqual(run(SK / "mcp-generator/scripts/validate.py", t / "s.json").returncode, 1)
        (t / "x.py").write_text('print("hi")\n')
        r = run(SK / "mcp-generator/scripts/validate.py", t / "x.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("stdout", r.stdout)
        (t / "y.ts").write_text('console.log("hi"); server.tool(')
        self.assertEqual(run(SK / "mcp-generator/scripts/validate.py", t / "y.ts").returncode, 1)


class TestDeepResearch(unittest.TestCase):
    def test_confidence_is_computed(self):
        L = SK / "deep-research/scripts/ledger.py"
        with tempfile.TemporaryDirectory() as t:
            run(L, "init", "T", cwd=t)
            run(L, "source", "https://www.who.int/a", "--title", "W", "--tier", "primary", "--date", "2026-01-01", cwd=t)
            run(L, "source", "https://www.bbc.co.uk/b", "--title", "B", "--tier", "secondary", "--date", "2026-01-01", cwd=t)
            run(L, "source", "https://news.bbc.co.uk/c", "--title", "B2", "--tier", "secondary", "--date", "2026-01-01", cwd=t)
            self.assertIn("confidence=high", run(L, "claim", "a", "--sources", "S1,S2", cwd=t).stdout)
            self.assertIn("confidence=medium", run(L, "claim", "b", "--sources", "S1", cwd=t).stdout)
            # same registrable domain twice = one independent source
            self.assertIn("confidence=low", run(L, "claim", "c", "--sources", "S2,S3", cwd=t).stdout)
            self.assertIn("confidence=low", run(L, "claim", "d", "--sources", "S1,S2", "--disputed", cwd=t).stdout)
            self.assertEqual(run(L, "check", "--strict", cwd=t).returncode, 1)
            rep = run(L, "report", cwd=t).stdout
            self.assertIn("| C1 | a | high |", rep)

    def test_rejects_unknown_source(self):
        L = SK / "deep-research/scripts/ledger.py"
        with tempfile.TemporaryDirectory() as t:
            run(L, "init", "T", cwd=t)
            self.assertNotEqual(run(L, "claim", "x", "--sources", "S9", cwd=t).returncode, 0)


class TestRepoDoctor(unittest.TestCase):
    def test_detects_and_masks_secret(self):
        fake = "AKIA" + "ABCDEFGHIJKLMNOP"  # built at runtime so this file holds no secret-shaped literal
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / "app.py").write_text(f'KEY = "{fake}"\n')
            r = run(SK / "repo-doctor/scripts/audit.py", t, "--json")
            data = json.loads(r.stdout)
            self.assertEqual(len(data["secrets"]), 1)
            self.assertNotIn(fake, r.stdout)  # never echo the secret
            self.assertEqual(data["secrets"][0]["file"], "app.py")

    def test_clean_repo_scores_high_and_fail_under_works(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t)
            (p / "README.md").write_text("# X\n\n## Install\n```\npip install x\n```\n## Usage\n" + "line\n" * 40)
            for f in ("LICENSE", "CONTRIBUTING.md", "SECURITY.md", "CHANGELOG.md"):
                (p / f).write_text("x")
            (p / ".gitignore").write_text(".env\n")
            (p / ".github/workflows").mkdir(parents=True)
            (p / ".github/workflows/ci.yml").write_text("x")
            (p / "tests").mkdir()
            (p / "tests/test_a.py").write_text("x")
            data = json.loads(run(SK / "repo-doctor/scripts/audit.py", t, "--json").stdout)
            self.assertEqual(data["score"], 100)
            self.assertEqual(run(SK / "repo-doctor/scripts/audit.py", t, "--fail-under", "101").returncode, 1)

    def test_exposed_env_flagged(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / ".env").write_text("A=1\n")
            data = json.loads(run(SK / "repo-doctor/scripts/audit.py", t, "--json").stdout)
            self.assertFalse(next(c for c in data["checks"] if c["id"] == "env")["passed"])


class TestDashboardBuilder(unittest.TestCase):
    def make_csv(self, d: Path) -> Path:
        p = d / "sales.csv"
        with p.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["id", "date", "region", "units", "revenue", "note"])
            for i in range(120):
                w.writerow([f"O{i}", f"2026-{(i % 9) + 1:02d}-{(i % 27) + 1:02d}", ["A", "B", "C"][i % 3],
                            i % 7 + 1, f"{(i + 1) * 1000:,}", f"n{i}</script><b>"])
        return p

    def test_type_inference_and_escaping(self):
        with tempfile.TemporaryDirectory() as t:
            out = Path(t) / "d.html"
            r = run(SK / "dashboard-builder/scripts/build_dashboard.py", self.make_csv(Path(t)), "--title", "A <b>", "--out", out)
            self.assertEqual(r.returncode, 0, r.stderr)
            for frag in ("date:date", "region:category", "revenue:number", "units:number"):
                self.assertIn(frag, r.stdout)
            html = out.read_text()
            self.assertIn("<title>A &lt;b&gt;</title>", html)
            self.assertEqual(html.count("</script>"), 2)      # only the two real closing tags
            self.assertIn("<\\/script>", html)                # hostile cell neutralized

    def test_json_input(self):
        with tempfile.TemporaryDirectory() as t:
            src = Path(t) / "d.json"
            src.write_text(json.dumps({"data": [{"a": "x", "n": 1}, {"a": "y", "n": 2}]}))
            r = run(SK / "dashboard-builder/scripts/build_dashboard.py", src, "--out", Path(t) / "o.html")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("n:number", r.stdout)

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_runtime_in_node(self):
        with tempfile.TemporaryDirectory() as t:
            out = Path(t) / "d.html"
            run(SK / "dashboard-builder/scripts/build_dashboard.py", self.make_csv(Path(t)), "--out", out)
            r = subprocess.run(["node", ROOT / "tests/dashboard_smoke.js", out, "120"], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
