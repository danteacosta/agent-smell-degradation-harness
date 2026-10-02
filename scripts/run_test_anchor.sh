#!/usr/bin/env bash
# One-shot runner for the pre-registered test-anchor experiment (macOS, local).
# Usage: bash scripts/run_test_anchor.sh [tester-model]
set -euo pipefail
cd "$(dirname "$0")/.."
MODEL="${1:-gpt-6-astra}"
EVIDENCE="${EVIDENCE_ROOT:-$HOME/Documents/GitHub/.private-research-evidence}"
RUN="$EVIDENCE/test-anchor-$(date +%Y%m%d-%H%M%S)"
PY="${PYTHON:-python3}"
[ -x .venv/bin/python ] && PY=.venv/bin/python

echo "== 1/5 runner controls"
"$PY" scripts/test_anchor_experiment.py controls --out "$RUN/controls"

echo "== 2/5 locate October packets in $EVIDENCE"
PACKETS=$("$PY" scripts/test_anchor_experiment.py locate --evidence-root "$EVIDENCE")
echo "$PACKETS"
ARGS=$("$PY" -c 'import json,sys; print(" ".join(f"--packet {k}={v}" for k,v in json.loads(sys.stdin.read()).items()))' <<<"$PACKETS")

echo "== 3/5 freeze prompts (tester model: $MODEL)"
"$PY" scripts/test_anchor_experiment.py prepare --out "$RUN/study" --model "$MODEL" $ARGS

echo "== 4/5 generate suites (81 Codex calls, no retry)"
"$PY" scripts/test_anchor_experiment.py generate --out "$RUN/study"

echo "== 5/5 execute suites in the qualified image"
"$PY" scripts/test_anchor_experiment.py execute --out "$RUN/study" > "$RUN/summary.json"
cat "$RUN/summary.json"
echo
echo "Done. Results: $RUN/study/results.json"
