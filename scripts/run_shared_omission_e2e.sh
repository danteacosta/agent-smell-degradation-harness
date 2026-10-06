#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"
EVIDENCE="${EVIDENCE_ROOT:-$HOME/Documents/GitHub/.private-research-evidence}"
RUN="$EVIDENCE/shared-omission-e2e-v1"
[ -e "$RUN" ] && { echo 'Study already exists; no resume or retry' >&2; exit 1; }
mkdir -p "$RUN"
"$PY" scripts/test_anchor_experiment.py controls --out "$RUN/controls"
"$PY" scripts/mutation_adequacy.py locate --evidence-root "$EVIDENCE" > "$RUN/packets.json"
"$PY" scripts/shared_omission_e2e.py prepare --out "$RUN/study" --packets "$RUN/packets.json" --model "${1:-gpt-6-astra}"
"$PY" scripts/shared_omission_e2e.py generate --out "$RUN/study"
"$PY" scripts/shared_omission_e2e.py execute --out "$RUN/study"
"$PY" scripts/shared_omission_e2e.py publish --out "$RUN/study" --public data/shared-omission-e2e/v1
cp "$RUN/controls/controls.json" data/shared-omission-e2e/v1/controls.json
