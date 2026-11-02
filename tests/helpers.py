from datetime import date

from vft import analyse, load_config, validate

AS_OF = date(2026, 10, 23)
CFG = load_config()


def finding(**kw):
    d = {"id": "F1", "vendor": "V1", "title": "t", "severity": "high", "opened": "2026-10-01", "due": "2026-11-30", "status": "open"}
    d.update(kw)
    return d


def run(*findings, cfg=None):
    data = {"vendors": [{"id": "V1", "name": "Vendor One"}], "findings": list(findings)}
    return analyse(validate(data), cfg or CFG, AS_OF)


def checks(res):
    return {(i["ref"], i["check"]) for i in res["issues"]}


def names(res):
    return {i["check"] for i in res["issues"]}
