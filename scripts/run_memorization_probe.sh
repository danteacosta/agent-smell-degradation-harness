#!/usr/bin/env bash
# Memorization probe for the rules the screening panel admitted (macOS, local).
# Usage: bash scripts/run_memorization_probe.sh [path/to/llm-screening-run]
set -euo pipefail
cd "$(dirname "$0")/.."
EVIDENCE="${EVIDENCE_ROOT:-$HOME/Documents/GitHub/.private-research-evidence}"
PANEL="${1:-$(ls -d "$EVIDENCE"/llm-screening-* 2>/dev/null | grep -v summary | sort | tail -1)}"
[ -f "$PANEL/results.json" ] || { echo "no screening panel results found; run scripts/run_llm_screening.sh first"; exit 1; }
RUN="$EVIDENCE/memorization-probe-$(date +%Y%m%d-%H%M%S)"
PY="${PYTHON:-python3}"
[ -x .venv/bin/python ] && PY=.venv/bin/python
echo "== panel results: $PANEL"
"$PY" scripts/memorization_probe.py prepare --out "$RUN" --panel-results "$PANEL/results.json" \
  --coder gpt-5.6-luna --coder gpt-5.6-sol --judge gpt-6-astra --judge gpt-6-sol
"$PY" scripts/memorization_probe.py run --out "$RUN" | tee "$RUN.summary.json"
echo; echo "Done. Results: $RUN/results.json"
