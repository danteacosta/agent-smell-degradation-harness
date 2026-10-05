#!/usr/bin/env bash
# Screening of the confirmatory frame options (macOS, local Codex CLI). Same panel,
# controls and rules as rounds 1 and 2. No generation and no A/B/C run happens here.
# Usage: bash scripts/run_confirmatory_screening.sh reserve|w2024|both [model-1 model-2 tiebreaker]
set -euo pipefail
cd "$(dirname "$0")/.."
WHICH="${1:?usage: run_confirmatory_screening.sh reserve|w2024|both}"; shift || true
M1="${1:-gpt-6-astra}"; M2="${2:-gpt-6-sol}"; TIE="${3:-gpt-6-luna}"
EVIDENCE="${EVIDENCE_ROOT:-$HOME/Documents/GitHub/.private-research-evidence}"
PY="${PYTHON:-python3}"
[ -x .venv/bin/python ] && PY=.venv/bin/python
case "$WHICH" in reserve|w2024) OPTIONS="$WHICH";; both) OPTIONS="reserve w2024";; *) echo "unknown option $WHICH" >&2; exit 2;; esac
for option in $OPTIONS; do
  SAMPLE="data/requirement-sampling/screening-confirmatory-$option-20261005.json"
  RUN="$EVIDENCE/llm-screening-confirmatory-$option-$(date +%Y%m%d-%H%M%S)"
  echo "== $option: freeze controls and blinded prompts ($SAMPLE; panel $M1 + $M2, tiebreaker $TIE)"
  "$PY" scripts/llm_screening_panel.py prepare --out "$RUN" --model "$M1" --model "$M2" --tiebreaker "$TIE" \
    --screening "$SAMPLE"
  echo "== $option: controls, then the panel (no retry)"
  "$PY" scripts/llm_screening_panel.py run --out "$RUN" | tee "$RUN.summary.json"
  "$PY" - "$RUN/results.json" <<'PY'
import json
from pathlib import Path
import sys

path = Path(sys.argv[1])
status = json.loads(path.read_text()).get("status")
if status != "complete":
    sys.exit(f"Screening stopped: {status!r}; preserve {path} and do not retry.")
PY
  echo "Done: $RUN/results.json"
done
