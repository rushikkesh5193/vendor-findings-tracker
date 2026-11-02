#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m tools.gen_sample examples/sample_findings.json
python3 -m vft examples/sample_findings.json --as-of 2026-10-23 --out-dir examples
python3 -m unittest discover -s tests
