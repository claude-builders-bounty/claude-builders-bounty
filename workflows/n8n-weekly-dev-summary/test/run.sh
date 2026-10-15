#!/usr/bin/env bash
set -euo pipefail

test_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
run_dir=$(mktemp -d /tmp/n8n-weekly-summary-test.XXXXXX)
chmod 755 "$run_dir"
server_pid=''

cleanup() {
  if [[ -n "$server_pid" ]]; then
    kill "$server_pid" 2>/dev/null || true
    wait "$server_pid" 2>/dev/null || true
  fi
  rm -rf "$run_dir"
}
trap cleanup EXIT

node "$test_dir/prepare.js" "$run_dir"
node "$test_dir/mock-server.js" "$run_dir/requests.jsonl" >"$run_dir/server.log" 2>&1 &
server_pid=$!

for _ in $(seq 1 100); do
  if grep -q READY "$run_dir/server.log" 2>/dev/null; then break; fi
  if ! kill -0 "$server_pid" 2>/dev/null; then
    sed -n '1,160p' "$run_dir/server.log"
    exit 1
  fi
  sleep 0.1
done
grep -q READY "$run_dir/server.log"

mkdir "$run_dir/n8n"
chmod 777 "$run_dir/n8n"

docker_run=(
  docker run --rm
  --add-host=host.docker.internal:host-gateway
  -e N8N_ENCRYPTION_KEY=weekly-summary-mock-test-key
  -e N8N_DIAGNOSTICS_ENABLED=false
  -e N8N_VERSION_NOTIFICATIONS_ENABLED=false
  -e N8N_LOG_LEVEL=error
  -e N8N_RUNNERS_ENABLED=false
  -v "$run_dir/n8n:/home/node/.n8n"
  -v "$run_dir:/test-data:ro"
  n8nio/n8n:2.42.1
)

"${docker_run[@]}" import:credentials --input=/test-data/credentials.json
"${docker_run[@]}" import:workflow --input=/test-data/workflows.json

for workflow_id in weekly-test-slack weekly-test-discord weekly-test-quiet-fr; do
  "${docker_run[@]}" execute --id="$workflow_id" --rawOutput >"$run_dir/$workflow_id.log"
done

node "$test_dir/assert.js" "$run_dir/requests.jsonl"
