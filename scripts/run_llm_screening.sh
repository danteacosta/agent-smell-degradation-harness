#!/usr/bin/env bash
# One-shot LLM-consensus screening of the 258 requirement candidates (macOS, local).
# Usage: bash scripts/run_llm_screening.sh [model-1 model-2 tiebreaker]
set -euo pipefail
cd "$(dirname "$0")/.."
M1="${1:-gpt-6-astra}"; M2="${2:-gpt-6-sol}"; TIE="${3:-gpt-6-luna}"
EVIDENCE="${EVIDENCE_ROOT:-$HOME/Documents/GitHub/.private-research-evidence}"
RUN="$EVIDENCE/llm-screening-$(date +%Y%m%d-%H%M%S)"
PY="${PYTHON:-python3}"
[ -x .venv/bin/python ] && PY=.venv/bin/python

echo "== 1/2 freeze controls and blinded prompts (panel: $M1 + $M2, tiebreaker $TIE)"
"$PY" scripts/llm_screening_panel.py prepare --out "$RUN" --model "$M1" --model "$M2" --tiebreaker "$TIE"

echo "== 2/2 controls, then about 530 Codex calls (no retry)"
"$PY" scripts/llm_screening_panel.py run --out "$RUN" | tee "$RUN.summary.json"
echo
echo "Done. Results: $RUN/results.json"
