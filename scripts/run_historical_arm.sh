#!/usr/bin/env bash
# Historical arm H (macOS, local Codex CLI). Two stages with a commit in between:
#
#   bash scripts/run_historical_arm.sh panel [model-1 model-2 tiebreaker]
#       blind review of the old documentation (controls first, ~95-115 calls),
#       then builds data/historical-arm/{admission.json,cases/} from the decisions.
#       Commit those files (the H texts are frozen there) before stage 2.
#
#   bash scripts/run_historical_arm.sh collect
#       arms A and H for every admitted case (2 models x 2 repetitions x 2 arms),
#       one packet per case, then copies each results.json to
#       data/historical-arm-results/<date>/<case>/ and prints the H vs A estimate.
set -euo pipefail
cd "$(dirname "$0")/.."
EVIDENCE="${EVIDENCE_ROOT:-$HOME/Documents/GitHub/.private-research-evidence}"
PY="${PYTHON:-python3}"
[ -x .venv/bin/python ] && PY=.venv/bin/python
STAGE="${1:?usage: run_historical_arm.sh panel|collect}"; shift || true

case "$STAGE" in
panel)
  M1="${1:-gpt-6-astra}"; M2="${2:-gpt-6-sol}"; TIE="${3:-gpt-6-luna}"
  if [ -e data/historical-arm/cases ] && [ -n "$(ls -A data/historical-arm/cases 2>/dev/null)" ]; then
    echo "data/historical-arm/cases already built; the H texts are frozen" >&2; exit 1
  fi
  RUN="$EVIDENCE/historical-review-panel-$(date +%Y%m%d-%H%M%S)"
  echo "== 1/3 freeze review prompts (panel: $M1 + $M2, tiebreaker $TIE)"
  "$PY" scripts/historical_arm.py prepare-panel --out "$RUN" --model "$M1" --model "$M2" --tiebreaker "$TIE"
  echo "== 2/3 controls, then the review (no retry)"
  "$PY" scripts/historical_arm.py run-panel --out "$RUN" | tee "$RUN.summary.json"
  if ! grep -q '"status": "complete"' "$RUN/results.json"; then
    echo "Panel stopped (see $RUN/results.json). Nothing was built." >&2; exit 1
  fi
  mkdir -p data/historical-arm/panel
  cp "$RUN/results.json" data/historical-arm/panel/results.json
  echo "== 3/3 admission and H texts"
  "$PY" scripts/historical_arm.py build --panel-results data/historical-arm/panel/results.json
  echo
  echo "Review data/historical-arm/admission.json, then commit data/historical-arm/ before 'collect'."
  ;;
collect)
  [ -n "$(ls -A data/historical-arm/cases 2>/dev/null)" ] || { echo "run the panel stage first" >&2; exit 1; }
  if [ -n "$(git status --porcelain data/historical-arm)" ]; then
    echo "commit data/historical-arm/ first (the H texts must be frozen in git)" >&2; exit 1
  fi
  STAMP="$(date +%Y%m%d)"
  OUT="data/historical-arm-results/$STAMP"
  BASE="$EVIDENCE/historical-arm-$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$OUT"
  for cfg in data/historical-arm/cases/*.json; do
    name="$(basename "$cfg" .json)"
    if [ -e "$OUT/$name/results.json" ]; then echo "skip $name (published)"; continue; fi
    echo "== $name"
    "$PY" scripts/abc_case.py prepare "$cfg" --packet "$BASE/$name"
    "$PY" scripts/abc_case.py run --packet "$BASE/$name" || { echo "stopped at $name" >&2; exit 1; }
    mkdir -p "$OUT/$name"
    cp "$BASE/$name/results.json" "$OUT/$name/results.json"
  done
  "$PY" scripts/historical_arm.py analyse --results "$OUT" | tee "$OUT/h-vs-a.json"
  ;;
*)
  echo "usage: run_historical_arm.sh panel|collect" >&2; exit 2;;
esac
