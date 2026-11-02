import csv
import io
import json


def _csv(rows, header):
    b = io.StringIO()
    w = csv.writer(b, lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    return b.getvalue()


def issues_csv(res):
    return _csv([[i["severity"], i["ref"], i["vendor"], i["check"], i["detail"], i["action"]] for i in res["issues"]],
                ["severity", "finding", "vendor", "check", "detail", "action"])


def open_csv(res):
    return _csv([[r["id"], r["name"], r["severity"], r["age_days"], r["days_overdue"], r["required_level"], r["recorded_level"], r["owner"]]
                 for r in res["open_findings"]],
                ["finding", "vendor", "severity", "age_days", "days_overdue", "escalation_required", "escalation_recorded", "owner"])


def to_json(res):
    return json.dumps(res, indent=2)


def to_markdown(res, org=""):
    over = [r for r in res["open_findings"] if r["days_overdue"] > 0]
    L = [f"# Vendor findings and escalation report{(' - ' + org) if org else ''}", "",
         f"As of {res['as_of']}. {len(res['open_findings'])} open findings, {len(over)} overdue, {len(res['issues'])} issues. "
         "SLAs and escalation thresholds are configurable defaults.", "", "## Summary for senior stakeholders", ""]
    L += [f"- {r['name']}: {r['id']} ({r['severity']}) is {r['days_overdue']} days overdue; needs {r['required_level']}, recorded {r['recorded_level']}." for r in over[:5]] or ["- No overdue findings."]
    L += ["", "## Issues", ""]
    for sev in ("critical", "high", "medium", "low"):
        rows = [i for i in res["issues"] if i["severity"] == sev]
        if rows:
            L += [f"### {sev.title()} ({len(rows)})", ""]
            L += [f"- **{i['check']}** `{i['ref']}`: {i['detail']} *Action:* {i['action']}" for i in rows] + [""]
    L += ["## Ageing of open findings (days since opened)", "", "| Bucket | Findings |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in res["aging"].items()]
    L += ["", "## By vendor", "", "| Vendor | Open | Overdue | Oldest (days) |", "|---|---|---|---|"]
    L += [f"| {k} | {v['open']} | {v['overdue']} | {v['oldest_days']} |" for k, v in res["by_vendor"].items()]
    L += ["", "## By owner", "", "| Owner | Open | Overdue | Oldest (days) |", "|---|---|---|---|"]
    L += [f"| {k} | {v['open']} | {v['overdue']} | {v['oldest_days']} |" for k, v in res["by_owner"].items()]
    return "\n".join(L) + "\n"
