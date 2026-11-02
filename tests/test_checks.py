import unittest
from datetime import date

from vft import validate
from vft.analyse import effective_due, required_level
from helpers import CFG, AS_OF, finding, names, run


class TestEscalationLadder(unittest.TestCase):
    def test_required_level_boundaries_for_high(self):
        # high: manager at 14 days overdue, leadership at 30.
        for late, want in [(0, 0), (-5, 0), (1, 1), (13, 1), (14, 2), (29, 2), (30, 3), (90, 3)]:
            self.assertEqual(required_level(late, "high", CFG), want, late)

    def test_critical_escalates_faster_than_low(self):
        self.assertEqual(required_level(14, "critical", CFG), 3)
        self.assertEqual(required_level(14, "low", CFG), 1)

    def test_overdue_boundary_is_the_day_after_due(self):
        self.assertNotIn("FINDING_OVERDUE", names(run(finding(due="2026-10-23"))))
        self.assertIn("FINDING_OVERDUE", names(run(finding(due="2026-10-22", opened="2026-10-01"))))

    def test_missing_escalation_flagged_when_level_too_low(self):
        f = finding(due="2026-09-20", opened="2026-09-01", escalation_level=1)          # 33 days late: needs leadership
        self.assertIn("ESCALATION_MISSING", names(run(f)))
        self.assertNotIn("ESCALATION_MISSING", names(run(dict(f, escalation_level=3))))

    def test_higher_recorded_level_is_fine(self):
        f = finding(due="2026-10-20", opened="2026-10-01", escalation_level=3)           # 3 days late: owner enough
        self.assertNotIn("ESCALATION_MISSING", names(run(f)))

    def test_overdue_issue_carries_finding_severity(self):
        for sev in ("critical", "high", "medium", "low"):
            res = run(finding(severity=sev, due="2026-10-22", opened="2026-10-01", escalation_level=1))
            self.assertEqual([i["severity"] for i in res["issues"] if i["check"] == "FINDING_OVERDUE"], [sev])


class TestDueDates(unittest.TestCase):
    def test_no_due_date_flagged_and_sla_used_for_overdue(self):
        res = run(finding(due=None, opened="2026-10-01"))                                 # high SLA 30 -> due 10-31
        self.assertIn("NO_DUE_DATE", names(res))
        self.assertNotIn("FINDING_OVERDUE", names(res))
        res = run(finding(due=None, opened="2026-09-01", escalation_level=3))             # SLA due 10-01 -> 22 days late
        self.assertIn("FINDING_OVERDUE", names(res))

    def test_due_beyond_sla_boundary(self):
        # high SLA is 30 days: opened 10-01, 10-31 is exactly 30.
        self.assertNotIn("DUE_BEYOND_SLA", names(run(finding(opened="2026-10-01", due="2026-10-31"))))
        self.assertIn("DUE_BEYOND_SLA", names(run(finding(opened="2026-10-01", due="2026-11-01"))))

    def test_effective_due(self):
        f = validate({"vendors": [], "findings": [finding(due=None, opened="2026-10-01", severity="critical")]})["findings"][0]
        self.assertEqual(effective_due(f, CFG), date(2026, 10, 16))


class TestClosedAndAccepted(unittest.TestCase):
    def test_closed_needs_evidence(self):
        self.assertIn("CLOSED_NO_EVIDENCE", names(run(finding(status="closed", closed="2026-10-10"))))
        self.assertNotIn("CLOSED_NO_EVIDENCE", names(run(finding(status="closed", closed="2026-10-10", closure_evidence="ticket 4471"))))

    def test_closed_findings_are_never_overdue(self):
        self.assertEqual(names(run(finding(status="closed", due="2026-01-01", opened="2025-12-01", closure_evidence="x"))), set())

    def acc(self, **kw):
        a = {"approver": "CISO", "approved_on": "2026-10-01", "expiry": "2027-03-01"}
        a.update(kw)
        return finding(status="risk_accepted", acceptance=a)

    def test_valid_acceptance_is_quiet(self):
        self.assertEqual(names(run(self.acc())), set())

    def test_incomplete_acceptance(self):
        self.assertIn("ACCEPTANCE_INVALID", names(run(self.acc(approver=""))))
        self.assertIn("ACCEPTANCE_INVALID", names(run(self.acc(expiry=None))))
        self.assertIn("ACCEPTANCE_INVALID", names(run(finding(status="risk_accepted"))))

    def test_expiry_boundary(self):
        self.assertNotIn("ACCEPTANCE_EXPIRED", names(run(self.acc(expiry="2026-10-23", approved_on="2026-10-01"))))
        self.assertIn("ACCEPTANCE_EXPIRED", names(run(self.acc(expiry="2026-10-22", approved_on="2026-10-01"))))

    def test_max_length_boundary(self):
        self.assertNotIn("ACCEPTANCE_TOO_LONG", names(run(self.acc(approved_on="2026-10-01", expiry="2027-10-01"))))
        self.assertIn("ACCEPTANCE_TOO_LONG", names(run(self.acc(approved_on="2026-10-01", expiry="2027-10-02"))))

    def test_accepted_findings_are_not_chased_as_open(self):
        self.assertEqual(run(self.acc(due="2026-01-01"))["open_findings"], [])


class TestReferences(unittest.TestCase):
    def test_unknown_vendor(self):
        self.assertIn("UNKNOWN_VENDOR", names(run(finding(vendor="NOPE"))))


class TestAgeing(unittest.TestCase):
    def test_buckets_and_grouping(self):
        fs = [finding(id="A", opened="2026-10-13"), finding(id="B", opened="2026-09-23"), finding(id="C", opened="2026-09-22"),
              finding(id="D", opened="2026-07-01", due="2027-01-01", owner="X"), finding(id="E", opened="2026-08-01", due="2027-01-01")]
        res = run(*fs)
        self.assertEqual(res["aging"], {"0-30": 2, "31-60": 1, "61-90": 1, ">90": 1})        # ages 10, 30, 31, 114, 83
        self.assertEqual(res["by_vendor"]["Vendor One"]["open"], 5)

    def test_open_findings_sorted_by_days_overdue(self):
        res = run(finding(id="A", due="2026-10-10", opened="2026-10-01", escalation_level=1),
                  finding(id="B", due="2026-09-01", opened="2026-08-15", escalation_level=3))
        self.assertEqual([r["id"] for r in res["open_findings"]], ["B", "A"])


class TestValidation(unittest.TestCase):
    def test_bad_input_rejected(self):
        bad = [finding(severity="urgent"), finding(status="done"), finding(escalation_level=4), finding(due="31/12/2026"), finding(opened=None)]
        for b in bad:
            with self.assertRaises(ValueError, msg=str(b)):
                validate({"vendors": [], "findings": [b]})
        with self.assertRaises(ValueError):
            validate({"vendors": [], "findings": [finding(), finding()]})


if __name__ == "__main__":
    unittest.main()
