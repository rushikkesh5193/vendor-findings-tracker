"""Write a synthetic findings register with problems injected on purpose.

    python3 -m tools.gen_sample examples/sample_findings.json
"""
import json
import sys

VENDORS = [("V01", "Northwind Payroll"), ("V02", "Contoso Cloud"), ("V03", "Fabrikam KYC"), ("V04", "Tailspin Messaging"),
           ("V05", "Adatum Analytics"), ("V06", "Litware Support"), ("V07", "Proseware Print"), ("V08", "Wingtip Travel")]


def f(i, vendor, title, sev, opened, due, **kw):
    d = {"id": f"F{i:02d}", "vendor": vendor, "title": title, "severity": sev, "opened": opened, "due": due,
         "status": "open", "owner": "A. Menon", "escalation_level": 0}
    d.update(kw)
    return d


def build():
    F = [
        # --- injected problems (as of 2026-10-23) ---
        f(1, "V01", "No MFA on admin console", "critical", "2026-09-01", "2026-09-16", escalation_level=3),            # 37 days late, leadership recorded
        f(2, "V02", "Backups not encrypted", "high", "2026-08-20", "2026-09-19", escalation_level=1, owner="R. Iyer"), # 34 days late, needs leadership
        f(3, "V03", "Stale access reviews", "medium", "2026-07-20", "2026-10-10", escalation_level=1, owner="R. Iyer"),  # 13 days late, owner level is enough
        f(4, "V04", "Missing log retention", "high", "2026-10-10", None),                                              # no due date
        f(5, "V05", "No pen test in 18 months", "high", "2026-08-01", "2027-01-01"),                                    # due 153 days out, SLA 30
        f(6, "V06", "Weak password policy", "medium", "2026-03-01", None, status="risk_accepted",
          acceptance={"approver": "CISO", "approved_on": "2026-03-20", "expiry": "2026-09-30"}),                        # expired
        f(7, "V07", "Shared admin accounts", "medium", "2026-04-01", None, status="risk_accepted",
          acceptance={"approver": "", "approved_on": "2026-04-10", "expiry": "2027-04-10"}),                            # no approver
        f(8, "V08", "No DR test evidence", "low", "2026-10-01", None, status="risk_accepted",
          acceptance={"approver": "CISO", "approved_on": "2026-10-01", "expiry": "2028-01-01"}),                        # too long
        f(9, "V01", "Outdated TLS configuration", "medium", "2026-05-01", "2026-07-30", status="closed", closed="2026-07-20"),  # closed, no evidence
        f(10, "V99", "Unmapped vendor finding", "low", "2026-10-15", "2027-04-01"),                                      # unknown vendor
        # --- clean findings ---
        f(11, "V02", "Incomplete asset inventory", "medium", "2026-09-15", "2026-12-14"),
        f(12, "V03", "Policy review overdue", "low", "2026-09-01", "2027-02-01"),
        f(13, "V04", "Training records incomplete", "low", "2026-10-01", "2027-03-01"),
        f(14, "V05", "No SIEM alert tuning", "medium", "2026-10-05", "2027-01-03"),
        f(15, "V06", "Vendor DR plan untested", "high", "2026-10-12", "2026-11-11"),
        f(16, "V07", "Patch SLA not defined", "medium", "2026-10-02", "2026-12-31"),
        f(17, "V08", "SOC 2 exceptions", "high", "2026-10-15", "2026-11-14"),
        f(18, "V01", "Old subprocessor list", "low", "2026-08-01", "2027-01-15", status="closed", closed="2026-09-10", closure_evidence="Updated list received 2026-09-10"),
        f(19, "V02", "Weak vendor offboarding", "high", "2026-06-01", "2026-07-01", status="closed", closed="2026-06-25", closure_evidence="Revised procedure and access removal log"),
        f(20, "V03", "Shared service account", "medium", "2026-05-01", None, status="risk_accepted",
          acceptance={"approver": "CISO", "approved_on": "2026-05-15", "expiry": "2027-05-15"}),
    ]
    return {"_note": "Synthetic data for demonstration. Problems are injected on purpose.", "organisation": "ExampleOrg",
            "vendors": [{"id": i, "name": n} for i, n in VENDORS], "findings": F}


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "examples/sample_findings.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(build(), fh, indent=2)
        fh.write("\n")
