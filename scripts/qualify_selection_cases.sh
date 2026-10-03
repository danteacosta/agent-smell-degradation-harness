#!/usr/bin/env bash
# Binding qualification of the selection-case oracles in the pinned Docker image (macOS, local).
# Usage: bash scripts/qualify_selection_cases.sh
set -euo pipefail
cd "$(dirname "$0")/.."
IMAGE="sha256:00d1265095773b7f8a12aa73e81d0bab75563cbd672dd0b5d91783ea1b6d4400"
EVIDENCE="${EVIDENCE_ROOT:-$HOME/Documents/GitHub/.private-research-evidence}"
RUN="$EVIDENCE/selection-case-qualification-$(date +%Y%m%d-%H%M%S)"
PY="${PYTHON:-python3}"
[ -x .venv/bin/python ] && PY=.venv/bin/python
mkdir -p "$RUN"
for config in data/abc-cases/*.json; do
  case_name=$("$PY" -c 'import json,sys;c=json.load(open(sys.argv[1]));print(c["case"] if c.get("candidate_id") else "")' "$config")
  [ -n "$case_name" ] || continue
  echo "== $case_name"
  "$PY" "eval/fixtures/$case_name/qualify.py" --image "$IMAGE" --output "$RUN/$case_name" \
    | "$PY" -c 'import json,sys;d=json.load(sys.stdin);print("  qualified:",d["qualified"],"controls:",d["controls"])'
done
echo "Done. Evidence: $RUN"
