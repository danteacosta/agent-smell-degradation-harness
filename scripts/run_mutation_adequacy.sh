#!/usr/bin/env bash
# Mutation adequacy study over the 46-case collection (macOS, local Codex CLI and Docker).
# No new implementation is generated: the tester writes suites, which run against the
# frozen A and C pages of the 46-case packets.
# Usage: bash scripts/run_mutation_adequacy.sh [tester-model]
set -euo pipefail
cd "$(dirname "$0")/.."
MODEL="${1:-gpt-6-astra}"
EVIDENCE="${EVIDENCE_ROOT:-$HOME/Documents/GitHub/.private-research-evidence}"
RUN="$EVIDENCE/mutation-adequacy-v1"
PY="${PYTHON:-python3}"
[ -x .venv/bin/python ] && PY=.venv/bin/python
[ -e "$RUN" ] && { echo "$RUN exists: the study runs once; no resume or retry" >&2; exit 1; }
mkdir -p "$RUN"

echo "== 1/6 runner controls (authored pages, must match before any generated suite runs)"
"$PY" scripts/test_anchor_experiment.py controls --out "$RUN/controls"

echo "== 2/6 locate the 25 eligible packets by the hash of their published results"
"$PY" scripts/mutation_adequacy.py locate --evidence-root "$EVIDENCE" > "$RUN/packets.json"

echo "== 3/6 freeze prompts (tester: $MODEL)"
"$PY" scripts/mutation_adequacy.py prepare --out "$RUN/study" --packets "$RUN/packets.json" --model "$MODEL"

echo "== 4/6 generate suites (150 Codex calls, no retry)"
"$PY" scripts/mutation_adequacy.py generate --out "$RUN/study"

echo "== 5/6 execute every suite on every correct, mutant and recovered page (~1,100 runs)"
"$PY" scripts/mutation_adequacy.py execute --out "$RUN/study" > "$RUN/summary.json"

echo "== 6/6 publish results (no private paths, no raw responses)"
mkdir -p data/mutation-adequacy/v1
cp "$RUN/study/results.json" data/mutation-adequacy/v1/results.json
cp "$RUN/controls/controls.json" data/mutation-adequacy/v1/controls.json
"$PY" -c 'import json,sys; m=json.load(open(sys.argv[1])); print(json.dumps({"seed":m["seed"],"model":m["model"],"image":m["image"],"runner_sha256":m["runner_sha256"],"script_sha256":m["script_sha256"],"cases":[{k:c[k] for k in ("case","project_id","reference","results_sha256","roles")} for c in m["cases"]],"schedule":m["schedule"]},indent=2))' "$RUN/study/frozen/manifest.json" > data/mutation-adequacy/v1/frozen-manifest-public.json
cat "$RUN/summary.json"
echo; echo "Done. Commit data/mutation-adequacy/v1/ in a PR; do not merge without review."
