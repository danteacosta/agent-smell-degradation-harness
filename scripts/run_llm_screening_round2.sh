#!/usr/bin/env bash
# Screening round 2: the frame extension (Zulip, Grist), same panel and controls as round 1.
# Usage: bash scripts/run_llm_screening_round2.sh [model-1 model-2 tiebreaker]
set -euo pipefail
cd "$(dirname "$0")/.."
M1="${1:-gpt-6-astra}"; M2="${2:-gpt-6-sol}"; TIE="${3:-gpt-6-luna}"
EVIDENCE="${EVIDENCE_ROOT:-$HOME/Documents/GitHub/.private-research-evidence}"
RUN="$EVIDENCE/llm-screening-round2-$(date +%Y%m%d-%H%M%S)"
PY="${PYTHON:-python3}"
[ -x .venv/bin/python ] && PY=.venv/bin/python

echo "== 1/2 freeze controls and blinded prompts for 60 candidates (panel: $M1 + $M2, tiebreaker $TIE)"
"$PY" scripts/llm_screening_panel.py prepare --out "$RUN" --model "$M1" --model "$M2" --tiebreaker "$TIE" \
  --screening data/requirement-sampling/screening-ext-20261002.json

echo "== 2/2 controls, then about 130 Codex calls (no retry)"
"$PY" scripts/llm_screening_panel.py run --out "$RUN" | tee "$RUN.summary.json"
echo
echo "Done. Results: $RUN/results.json"
