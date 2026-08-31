#!/usr/bin/env bash
# Deploy workspace assets and run the full medallion pipeline on Databricks.
set -euo pipefail

PROFILE="${DATABRICKS_PROFILE:-community}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== Step 1: Deploy workspace assets ==="
bash "${ROOT}/scripts/deploy_workspace.sh"

echo "=== Step 2: Submit medallion pipeline (bronze -> silver -> gold -> dashboard) ==="
databricks jobs submit --json @"${ROOT}/conf/medallion_pipeline_run.json" \
  --profile "${PROFILE}" --timeout 60m -o json | tee /tmp/medallion_pipeline_run.json

RUN_ID="$(python3 - <<'PY'
import json
print(json.load(open('/tmp/medallion_pipeline_run.json'))['run_id'])
PY
)"

echo "=== Step 3: Wait for pipeline completion (run_id=${RUN_ID}) ==="
databricks runs get --run-id "${RUN_ID}" --profile "${PROFILE}" -o json > /tmp/medallion_run_status.json
while true; do
  STATE="$(python3 - <<'PY'
import json
print(json.load(open('/tmp/medallion_run_status.json'))['state']['life_cycle_state'])
PY
)"
  RESULT="$(python3 - <<'PY'
import json
state = json.load(open('/tmp/medallion_run_status.json'))['state']
print(state.get('result_state') or '')
PY
)"
  echo "  state=${STATE} result=${RESULT}"
  if [[ "${STATE}" == "TERMINATED" ]]; then
    break
  fi
  sleep 20
  databricks runs get --run-id "${RUN_ID}" --profile "${PROFILE}" -o json > /tmp/medallion_run_status.json
done

if [[ "${RESULT}" != "SUCCESS" ]]; then
  echo "Pipeline failed. Fetching run output..."
  databricks runs get-output --run-id "${RUN_ID}" --profile "${PROFILE}" || true
  exit 1
fi

echo "=== Pipeline SUCCESS ==="
python3 - <<'PY'
import json
run = json.load(open('/tmp/medallion_run_status.json'))
print(f"Run page: {run.get('run_page_url', 'N/A')}")
PY
