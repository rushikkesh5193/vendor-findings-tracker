"""Remediation tracking, escalation and risk-acceptance checks for vendor findings."""
import json
from datetime import timedelta
from pathlib import Path

from .models import LEVELS, SEVERITIES, add_months

ORDER = {s: i for i, s in enumerate(SEVERITIES)}


def load_config(path=None):
    p = Path(path) if path else Path(__file__).with_name("config.json")
    return json.loads(p.read_text(encoding="utf-8"))


def _issue(sev, ref, vendor, check, detail, action):
    return {"severity": sev, "ref": ref, "vendor": vendor, "check": check, "detail": detail, "action": action}


def effective_due(f, cfg):
    return f["due"] or f["opened"] + timedelta(days=cfg["sla_days"][f["severity"]])


def required_level(days_overdue, severity, cfg):
    """0 = not overdue; 1 owner; 2 manager; 3 senior leadership."""
    if days_overdue <= 0:
        return 0
    if days_overdue >= cfg["leadership_after_days_overdue"][severity]:
        return 3
    if days_overdue >= cfg["manager_after_days_overdue"][severity]:
        return 2
    return 1


def analyse(data, cfg=None, as_of=None):
    cfg = cfg or load_config()
    vendors = {v["id"]: v for v in data["vendors"]}
    issues, rows = [], []
    for f in data["findings"]:
        v = vendors.get(f["vendor"])
        name = v["name"] if v else f["vendor"]
        ref, sev = f["id"], f["severity"]
        if v is None:
            issues.append(_issue("high", ref, f["vendor"], "UNKNOWN_VENDOR",
                                 f"{f['title']} refers to vendor {f['vendor']}, which is not in the vendor list.", "Correct the reference."))
        if f["status"] == "open":
            due = effective_due(f, cfg)
            late = (as_of - due).days
            if f["due"] is None:
                issues.append(_issue("medium", ref, name, "NO_DUE_DATE",
                                     f"{f['title']} has no due date; the {sev} SLA of {cfg['sla_days'][sev]} days gives {due}.", "Agree a due date with the vendor."))
            elif f["due"] > f["opened"] + timedelta(days=cfg["sla_days"][sev]):
                issues.append(_issue("medium", ref, name, "DUE_BEYOND_SLA",
                                     f"{f['title']}: due {f['due']} is {(f['due'] - f['opened']).days} days after it was opened; the {sev} SLA is {cfg['sla_days'][sev]} days.",
                                     "Record an approved extension or bring the date back inside the SLA."))
            need = required_level(late, sev, cfg)
            if late > 0:
                issues.append(_issue(sev, ref, name, "FINDING_OVERDUE",
                                     f"{f['title']} ({name}) is {late} days overdue; escalation to {LEVELS[need]} is due.",
                                     "Chase the vendor and record the escalation."))
                if f["escalation_level"] < need:
                    issues.append(_issue("high", ref, name, "ESCALATION_MISSING",
                                         f"{f['title']} ({name}) is {late} days overdue and needs escalation to {LEVELS[need]}; recorded level is {LEVELS[f['escalation_level']]}.",
                                         f"Escalate to {LEVELS[need]} now."))
            rows.append({"id": ref, "vendor": f["vendor"], "name": name, "severity": sev, "age_days": (as_of - f["opened"]).days,
                         "days_overdue": max(late, 0), "required_level": LEVELS[need], "recorded_level": LEVELS[f["escalation_level"]],
                         "owner": f.get("owner", "")})
        elif f["status"] == "closed":
            if not f.get("closure_evidence"):
                issues.append(_issue("medium", ref, name, "CLOSED_NO_EVIDENCE",
                                     f"{f['title']} was closed on {f['closed'] or 'an unrecorded date'} with no closure evidence.", "Attach the evidence the vendor provided."))
        else:  # risk_accepted
            a = f["acceptance"]
            if not a or not a.get("approver") or a["expiry"] is None or a["approved_on"] is None:
                issues.append(_issue("high", ref, name, "ACCEPTANCE_INVALID",
                                     f"{f['title']} is marked risk accepted without a complete approval (approver, approval date and expiry).", "Complete the approval or reopen the finding."))
            else:
                if a["expiry"] < as_of:
                    issues.append(_issue("high", ref, name, "ACCEPTANCE_EXPIRED",
                                         f"The risk acceptance for {f['title']} expired on {a['expiry']}.", "Renew with a fresh approval or remediate."))
                elif a["expiry"] > add_months(a["approved_on"], cfg["max_acceptance_months"]):
                    issues.append(_issue("medium", ref, name, "ACCEPTANCE_TOO_LONG",
                                         f"The risk acceptance for {f['title']} runs {a['approved_on']} to {a['expiry']}, longer than {cfg['max_acceptance_months']} months.",
                                         "Shorten the expiry so the risk is reviewed at least annually."))
    issues.sort(key=lambda i: (ORDER[i["severity"]], i["ref"], i["check"]))
    rows.sort(key=lambda r: (-r["days_overdue"], ORDER[r["severity"]], r["id"]))
    return {"as_of": str(as_of), "issues": issues, "open_findings": rows, "aging": _aging(rows, cfg), "by_vendor": _by(rows, "name"),
            "by_owner": _by(rows, "owner")}


def _aging(rows, cfg):
    b = cfg["aging_buckets_days"]
    labels = [f"0-{b[0]}"] + [f"{b[i] + 1}-{b[i + 1]}" for i in range(len(b) - 1)] + [f">{b[-1]}"]
    out = dict.fromkeys(labels, 0)
    for r in rows:
        k = next((i for i, lim in enumerate(b) if r["age_days"] <= lim), len(b))
        out[labels[k]] += 1
    return out


def _by(rows, key):
    out = {}
    for r in rows:
        d = out.setdefault(r[key] or "(unassigned)", {"open": 0, "overdue": 0, "oldest_days": 0})
        d["open"] += 1
        d["overdue"] += r["days_overdue"] > 0
        d["oldest_days"] = max(d["oldest_days"], r["age_days"])
    return dict(sorted(out.items(), key=lambda kv: (-kv[1]["overdue"], -kv[1]["open"], kv[0])))
