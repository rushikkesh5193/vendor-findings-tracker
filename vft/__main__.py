import argparse
import sys
from datetime import date
from pathlib import Path

from . import analyse, load, load_config, parse_date
from .models import SEVERITIES
from .report import issues_csv, open_csv, to_json, to_markdown


def main(argv=None):
    ap = argparse.ArgumentParser(prog="vft", description="Vendor findings and escalation tracker.")
    ap.add_argument("input")
    ap.add_argument("--as-of", help="YYYY-MM-DD (default: today)")
    ap.add_argument("--out-dir")
    ap.add_argument("--config")
    ap.add_argument("--fail-on", choices=SEVERITIES)
    a = ap.parse_args(argv)
    try:
        as_of = parse_date(a.as_of, "--as-of") if a.as_of else date.today()
        data = load(a.input)
        res = analyse(data, load_config(a.config), as_of)
    except (OSError, ValueError, KeyError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if a.out_dir:
        d = Path(a.out_dir)
        d.mkdir(parents=True, exist_ok=True)
        (d / "report.md").write_text(to_markdown(res, data["organisation"]), encoding="utf-8")
        (d / "report.json").write_text(to_json(res), encoding="utf-8")
        (d / "issues.csv").write_text(issues_csv(res), encoding="utf-8")
        (d / "open_findings.csv").write_text(open_csv(res), encoding="utf-8")
        print(f"{len(res['issues'])} issues -> {d}/")
    else:
        print(to_markdown(res, data["organisation"]))
    if a.fail_on and any(SEVERITIES.index(i["severity"]) <= SEVERITIES.index(a.fail_on) for i in res["issues"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
