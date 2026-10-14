#!/usr/bin/env bash
# Test suite for the block-destructive PreToolUse hook.
# Feeds hook payloads on stdin and checks the decision + the log file.
# Exits non-zero if any case fails. Run: bash test/run-tests.sh
set -u

HOOK="$(cd "$(dirname "$0")/.." && pwd)/block-destructive.sh"
TMP="$(mktemp -d)"
export CLAUDE_HOOK_LOG_DIR="$TMP"
LOG="$TMP/blocked.log"
unset CLAUDE_ALLOW_DESTRUCTIVE 2>/dev/null || true

pass=0
fail=0

check() {
  local expected="$1" label="$2" command="$3" tool="${4:-Bash}"
  local payload decision
  payload="$(printf '{"hook_event_name":"PreToolUse","session_id":"test","cwd":"/home/dev/project","tool_name":"%s","tool_input":{"command":%s}}' \
    "$tool" "$(printf '%s' "$command" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))' 2>/dev/null || printf '"%s"' "$command")")"

  out="$(printf '%s' "$payload" | bash "$HOOK" 2>/dev/null)"
  if printf '%s' "$out" | grep -q '"permissionDecision":"deny"'; then decision="deny"; else decision="allow"; fi

  if [ "$decision" = "$expected" ]; then
    printf '  ok    %-6s %s\n' "$expected" "$label"
    pass=$((pass + 1))
  else
    printf '  FAIL  esperaba %s y dio %s -> %s\n' "$expected" "$decision" "$label"
    fail=$((fail + 1))
  fi
}

echo "== casos que deben BLOQUEARSE =="
check deny "rm -rf"                 'rm -rf /tmp/build'
check deny "sudo rm -rf"            'sudo rm -rf /var/data'
check deny "rm -fr"                 'rm -fr ./dist'
check deny "rm -r -f (separados)"   'rm -r -f ./node_modules'
check deny "rm --recursive --force" 'rm --recursive --force ./cache'
check deny "DROP TABLE"             'psql -c "DROP TABLE users"'
check deny "TRUNCATE"               'mysql -e "TRUNCATE TABLE orders"'
check deny "DELETE sin WHERE"       'psql -c "DELETE FROM users"'
check deny "DELETE sin WHERE (2a)"  'echo listo; DELETE FROM logs; SELECT 1;'
check deny "git push --force"       'git push --force origin main'
check deny "git push -f"            'git push -f'

echo "== casos que deben PASAR =="
check allow "ls"                    'ls -la'
check allow "rm de un archivo"      'rm file.txt'
check allow "rm -r sin force"       'rm -r ./build'
check allow "DELETE con WHERE"      'psql -c "DELETE FROM users WHERE id = 1"'
check allow "git push normal"       'git push origin main'
check allow "force-with-lease"      'git push --force-with-lease origin main'
check allow "npm test"              'npm test && npm run build'
check allow "otra tool (no Bash)"   'rm -rf /' 'Edit'

echo
echo "== log de bloqueos =="
if [ -f "$LOG" ]; then
  cat "$LOG"
  lines=$(wc -l < "$LOG" | tr -d ' ')
  echo "lineas en blocked.log: $lines (esperadas 11)"
  if [ "$lines" = "11" ]; then pass=$((pass + 1)); else echo "  FAIL: se esperaban 11 lineas"; fail=$((fail + 1)); fi
  if grep -q '/home/dev/project' "$LOG"; then
    echo "  ok    el log incluye la ruta del proyecto"
    pass=$((pass + 1))
  else
    echo "  FAIL: el log no incluye la ruta del proyecto"; fail=$((fail + 1))
  fi
  if grep -qE '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z \| ' "$LOG"; then
    echo "  ok    el log incluye timestamp ISO"
    pass=$((pass + 1))
  else
    echo "  FAIL: falta el timestamp ISO"; fail=$((fail + 1))
  fi
else
  echo "  FAIL: no se creo blocked.log"
  fail=$((fail + 1))
fi

echo
echo "== escape hatch (CLAUDE_ALLOW_DESTRUCTIVE=1) =="
out="$(printf '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"},"cwd":"/tmp"}' | CLAUDE_ALLOW_DESTRUCTIVE=1 CLAUDE_HOOK_LOG_DIR="$TMP" bash "$HOOK")"
if [ -z "$out" ]; then echo "  ok    con la variable activada no bloquea"; pass=$((pass + 1)); else echo "  FAIL: bloqueo pese a la variable"; fail=$((fail + 1)); fi

rm -rf "$TMP"
echo
echo "RESULTADO: $pass pasaron, $fail fallaron"
[ "$fail" = "0" ]
