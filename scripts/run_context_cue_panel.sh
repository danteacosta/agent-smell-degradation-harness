#!/usr/bin/env bash
# Blind LLM-panel coding of context_cue for the 46 selected cases (macOS, local).
# Usage: bash scripts/run_context_cue_panel.sh [model-1 model-2 tiebreaker]
set -euo pipefail
cd "$(dirname "$0")/.."
M1="${1:-gpt-6-astra}"; M2="${2:-gpt-6-sol}"; TIE="${3:-gpt-6-luna}"
EVIDENCE="${EVIDENCE_ROOT:-$HOME/Documents/GitHub/.private-research-evidence}"
RUN="$EVIDENCE/context-cue-panel-$(date +%Y%m%d-%H%M%S)"
PY="${PYTHON:-python3}"
[ -x .venv/bin/python ] && PY=.venv/bin/python
echo "== 1/2 freeze prompts (panel: $M1 + $M2, tiebreaker $TIE)"
"$PY" scripts/context_cue_panel.py prepare --out "$RUN" --model "$M1" --model "$M2" --tiebreaker "$TIE"
echo "== 2/2 controls, then about 100 Codex calls (no retry)"
"$PY" scripts/context_cue_panel.py run --out "$RUN" | tee "$RUN.summary.json"
echo
echo "Done. Results: $RUN/results.json"
echo "Scoreboard: python3 scripts/selected46_report.py --results <packets> --context-cue $RUN/results.json --markdown placar.md"
