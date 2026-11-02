import calendar
import json
from datetime import date

SEVERITIES = ("critical", "high", "medium", "low")
STATUSES = ("open", "closed", "risk_accepted")
LEVELS = {0: "none", 1: "owner", 2: "manager", 3: "senior leadership"}


def parse_date(s, field="date"):
    if s in (None, ""):
        return None
    try:
        y, m, d = (int(x) for x in str(s).split("-"))
        return date(y, m, d)
    except (ValueError, TypeError):
        raise ValueError(f"{field}: expected YYYY-MM-DD, got {s!r}")


def add_months(d, n):
    m = d.month - 1 + n
    y, m = d.year + m // 12, m % 12 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def load(path):
    with open(path, encoding="utf-8") as f:
        return validate(json.load(f))


def validate(data):
    if not isinstance(data, dict):
        raise ValueError("input must be a JSON object")
    out = {"organisation": data.get("organisation", ""), "vendors": [], "findings": []}
    for kind in ("vendors", "findings"):
        seen = set()
        for r in data.get(kind, []):
            if "id" not in r:
                raise ValueError(f"{kind}: record without id")
            if r["id"] in seen:
                raise ValueError(f"{kind}: duplicate id {r['id']}")
            seen.add(r["id"])
    out["vendors"] = [dict(v) for v in data.get("vendors", [])]
    for f in data.get("findings", []):
        if f.get("severity") not in SEVERITIES:
            raise ValueError(f"finding {f['id']}: severity must be one of {SEVERITIES}, got {f.get('severity')!r}")
        if f.get("status", "open") not in STATUSES:
            raise ValueError(f"finding {f['id']}: status must be one of {STATUSES}, got {f.get('status')!r}")
        lvl = f.get("escalation_level", 0)
        if lvl not in LEVELS:
            raise ValueError(f"finding {f['id']}: escalation_level must be 0..3, got {lvl!r}")
        q = dict(f)
        q["status"] = f.get("status", "open")
        q["escalation_level"] = lvl
        for k in ("opened", "due", "closed"):
            q[k] = parse_date(f.get(k), f"finding {f['id']}.{k}")
        if q["opened"] is None:
            raise ValueError(f"finding {f['id']}: opened date is required")
        a = f.get("acceptance")
        if a is not None:
            a = dict(a)
            a["approved_on"] = parse_date(a.get("approved_on"), f"finding {f['id']}.acceptance.approved_on")
            a["expiry"] = parse_date(a.get("expiry"), f"finding {f['id']}.acceptance.expiry")
        q["acceptance"] = a
        out["findings"].append(q)
    return out
