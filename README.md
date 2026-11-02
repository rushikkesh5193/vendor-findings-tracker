# vendor-findings-tracker

A small Python tool for tracking **vendor audit findings through to remediation**. It checks every finding against a severity-based deadline, works out who the finding should have been escalated to (the vendor owner, a manager, or senior leadership), and flags where the escalation has not happened. It also keeps risk acceptances honest: approved by someone, with an expiry date, and not left to lapse.

Python standard library only (tested on Python 3.13).

> **Data note.** `examples/sample_findings.json` is **synthetic** (an invented "ExampleOrg": 8 vendors, 20 findings). Ten findings have problems injected on purpose, giving 11 issues, and the tests check the tool finds exactly those. Nothing here comes from a real organisation.

## Why

Findings rarely go missing; they go quiet. A critical finding sits a month past due and nobody above the vendor owner knows. A "risk accepted" finding expires and nobody renews it. This tool makes the quiet items loud and produces the summary a senior stakeholder needs.

## Quick start

```bash
python3 -m vft examples/sample_findings.json --as-of 2026-10-23 --out-dir out   # report.md, report.json, issues.csv, open_findings.csv
python3 -m vft examples/sample_findings.json --fail-on high                      # exit 1 on any high issue (cron / CI)
python3 -m unittest discover -s tests                                            # 27 tests
bash scripts/run_demo.sh                                                         # regenerate data, report and tests
```

## How it works

**Deadlines.** Each severity has an SLA from the day the finding is opened: critical 15 days, high 30, medium 90, low 180. If a finding has no due date, the SLA date is used so it still gets chased.

**Escalation ladder.** Based on how many days overdue a finding is:

| Severity | Owner (1 day late) | Manager | Senior leadership |
|---|---|---|---|
| Critical | 1+ | 7+ days | 14+ days |
| High | 1+ | 14+ days | 30+ days |
| Medium | 1+ | 30+ days | 60+ days |
| Low | 1+ | 45+ days | 90+ days |

Record the level reached on each finding (`escalation_level`: 0 none, 1 owner, 2 manager, 3 senior leadership).

| Check | Raised when | Severity |
|---|---|---|
| `FINDING_OVERDUE` | An open finding is past its due date | the finding's own severity |
| `ESCALATION_MISSING` | Overdue, and the recorded escalation level is below the level required | high |
| `NO_DUE_DATE` | An open finding has no due date | medium |
| `DUE_BEYOND_SLA` | The due date is later than opened date plus the severity SLA | medium |
| `CLOSED_NO_EVIDENCE` | Closed with no closure evidence recorded | medium |
| `ACCEPTANCE_INVALID` | Risk accepted without an approver, approval date or expiry | high |
| `ACCEPTANCE_EXPIRED` | The acceptance expiry has passed | high |
| `ACCEPTANCE_TOO_LONG` | The acceptance runs longer than 12 months | medium |
| `UNKNOWN_VENDOR` | The finding names a vendor that is not in the list | high |

**Reporting.** The Markdown report opens with a short summary of the worst overdue findings for senior stakeholders, then the issues, the ageing of open findings (0-30, 31-60, 61-90, over 90 days) and tables by vendor and by owner. Open findings are also written to `open_findings.csv`.

## Input format

```json
{"organisation": "ExampleOrg",
 "vendors":  [{"id": "V01", "name": "Northwind Payroll"}],
 "findings": [{"id": "F01", "vendor": "V01", "title": "No MFA on admin console", "severity": "critical",
               "opened": "2026-09-01", "due": "2026-09-16", "status": "open", "owner": "A. Menon", "escalation_level": 3},
              {"id": "F06", "vendor": "V06", "title": "...", "severity": "medium", "opened": "2026-03-01", "status": "risk_accepted",
               "acceptance": {"approver": "CISO", "approved_on": "2026-03-20", "expiry": "2027-03-20"}}]}
```

`status` is `open`, `closed` (with `closure_evidence`) or `risk_accepted`. Duplicate IDs, bad severities, bad dates and a missing opened date are rejected with a clear message (exit code 2).

## Limitations

- **The SLAs and escalation thresholds are illustrative defaults**, not a standard. Set them in `vft/config.json` to match your policy.
- **It trusts the recorded escalation level.** It cannot check that a manager or leadership was actually told; it only checks that someone wrote it down.
- **It does not verify closure.** `CLOSED_NO_EVIDENCE` only tests that evidence is recorded, not that it is adequate. An agreed extension has to be recorded as a new due date.
- **A finding is not a score.** There is no risk rating here beyond the severity you supply.
- No persistence, UI, notifications or authentication. It reads JSON and writes reports.

## Layout

```
vft/       models.py  analyse.py  report.py  config.json  __main__.py
tools/     gen_sample.py     synthetic data generator
tests/     27 tests, including an exact-match end-to-end test
examples/  sample_findings.json  report.md  report.json  issues.csv  open_findings.csv
scripts/   run_demo.sh
```
