import csv
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from vft import analyse, load
from vft.report import issues_csv, open_csv, to_markdown
from helpers import AS_OF

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "examples" / "sample_findings.json"
EXPECTED = {("F01", "FINDING_OVERDUE"), ("F02", "FINDING_OVERDUE"), ("F02", "ESCALATION_MISSING"), ("F03", "FINDING_OVERDUE"),
            ("F04", "NO_DUE_DATE"), ("F05", "DUE_BEYOND_SLA"), ("F06", "ACCEPTANCE_EXPIRED"), ("F07", "ACCEPTANCE_INVALID"),
            ("F08", "ACCEPTANCE_TOO_LONG"), ("F09", "CLOSED_NO_EVIDENCE"), ("F10", "UNKNOWN_VENDOR")}


class TestSample(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.res = analyse(load(SAMPLE), as_of=AS_OF)

    def test_finds_exactly_the_injected_problems(self):
        got = {(i["ref"], i["check"]) for i in self.res["issues"]}
        self.assertEqual(got - EXPECTED, set(), "false positives")
        self.assertEqual(EXPECTED - got, set(), "missed")

    def test_clean_findings_are_quiet(self):
        self.assertEqual({i["ref"] for i in self.res["issues"] if i["ref"] >= "F11"}, set())

    def test_sorted_by_severity_and_critical_first(self):
        order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        s = [order[i["severity"]] for i in self.res["issues"]]
        self.assertEqual(s, sorted(s))
        self.assertEqual(self.res["issues"][0]["ref"], "F01")

    def test_escalation_levels_in_open_list(self):
        r = {x["id"]: x for x in self.res["open_findings"]}
        self.assertEqual((r["F01"]["required_level"], r["F01"]["recorded_level"]), ("senior leadership", "senior leadership"))
        self.assertEqual((r["F02"]["required_level"], r["F02"]["recorded_level"]), ("senior leadership", "owner"))
        self.assertEqual(r["F03"]["required_level"], "owner")

    def test_outputs(self):
        self.assertEqual(len(list(csv.reader(io.StringIO(issues_csv(self.res))))), len(EXPECTED) + 1)
        self.assertEqual(len(list(csv.reader(io.StringIO(open_csv(self.res))))), len(self.res["open_findings"]) + 1)
        self.assertIn("Summary for senior stakeholders", to_markdown(self.res, "X"))


class TestCli(unittest.TestCase):
    def cli(self, *a):
        return subprocess.run([sys.executable, "-m", "vft", *a], cwd=ROOT, capture_output=True, text=True)

    def test_writes_files(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.cli(str(SAMPLE), "--as-of", "2026-10-23", "--out-dir", d)
            self.assertEqual(r.returncode, 0, r.stderr)
            for f in ("report.md", "report.json", "issues.csv", "open_findings.csv"):
                self.assertTrue((Path(d) / f).is_file(), f)
            self.assertEqual(len(json.loads((Path(d) / "report.json").read_text())["issues"]), len(EXPECTED))

    def test_exit_codes(self):
        self.assertEqual(self.cli(str(SAMPLE), "--as-of", "2026-10-23", "--fail-on", "critical").returncode, 1)
        self.assertEqual(self.cli("nope.json").returncode, 2)
        self.assertEqual(self.cli(str(SAMPLE), "--as-of", "soon").returncode, 2)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "b.json"
            p.write_text(json.dumps({"vendors": [], "findings": [{"id": "F", "vendor": "V", "title": "t", "severity": "urgent", "opened": "2026-01-01"}]}))
            r = self.cli(str(p))
            self.assertEqual(r.returncode, 2)
            self.assertIn("severity", r.stderr)


if __name__ == "__main__":
    unittest.main()
