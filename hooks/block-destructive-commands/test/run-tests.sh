#!/usr/bin/env bash
# Regression checks for block_destructive.py
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
HOOK="$ROOT/block_destructive.py"
PASS=0
FAIL=0

run_case() {
  local expect="$1"  # deny | allow
  local label="$2"
  local cmd="$3"
  local out err rc decision
  out="$(mktemp)"; err="$(mktemp)"
  set +e
  python3 - "$HOOK" "$cmd" "$out" "$err" <<'PY'
import json, subprocess, sys
hook, cmd, out_path, err_path = sys.argv[1:5]
payload = json.dumps({
    "tool_name": "Bash",
    "tool_input": {"command": cmd},
    "cwd": "/tmp/test-project",
})
with open(out_path, "w") as out, open(err_path, "w") as err:
    proc = subprocess.run(
        ["python3", hook],
        input=payload,
        text=True,
        stdout=out,
        stderr=err,
    )
sys.exit(proc.returncode)
PY
  rc=$?
  set -e
  decision="$(python3 -c '
import json,sys
raw=open(sys.argv[1]).read().strip()
if not raw:
    print("")
else:
    try:
        d=json.loads(raw)
        print(d.get("hookSpecificOutput",{}).get("permissionDecision",""))
    except Exception:
        print("PARSE_ERROR")
' "$out")"

  if [[ "$expect" == "deny" ]]; then
    if [[ "$decision" == "deny" ]]; then
      echo "  ok    deny   $label"
      PASS=$((PASS + 1))
    else
      echo "  FAIL  deny   $label  (got decision='$decision' rc=$rc)"
      echo "        stdout: $(cat "$out")"
      echo "        stderr: $(cat "$err")"
      FAIL=$((FAIL + 1))
    fi
  else
    if [[ "$rc" -eq 0 && "$decision" != "deny" ]]; then
      echo "  ok    allow  $label"
      PASS=$((PASS + 1))
    else
      echo "  FAIL  allow  $label  (decision='$decision' rc=$rc)"
      echo "        stdout: $(cat "$out")"
      echo "        stderr: $(cat "$err")"
      FAIL=$((FAIL + 1))
    fi
  fi
  rm -f "$out" "$err"
}

echo "== cases that must be BLOCKED =="
run_case deny "rm -rf"                   "rm -rf /tmp/build"
run_case deny "sudo rm -rf"              "sudo rm -rf /var/cache/x"
run_case deny "rm -fr"                   "rm -fr ./dist"
run_case deny "rm -r -f"                 "rm -r -f ./node_modules"
run_case deny "rm --recursive --force"   "rm --recursive --force /tmp/x"
run_case deny "DROP TABLE"               "psql -c 'DROP TABLE users;'"
run_case deny "drop table lower"         "mysql -e \"drop table sessions\""
run_case deny "TRUNCATE"                 "psql -c 'TRUNCATE TABLE logs;'"
run_case deny "TRUNCATE bare"            "sqlite3 db.sqlite 'TRUNCATE events;'"
run_case deny "git push --force"         "git push --force origin main"
run_case deny "git push -f"              "git push -f origin feature"
run_case deny "git push --force-with-lease" "git push --force-with-lease origin main"
run_case deny "DELETE FROM no WHERE"     "psql -c 'DELETE FROM users;'"
run_case deny "DELETE FROM multi-stmt"   "psql -c 'DELETE FROM a; SELECT 1;'"

echo
echo "== cases that must be ALLOWED =="
run_case allow "ls"                      "ls -la"
run_case allow "git status"              "git status"
run_case allow "npm test"                "npm test"
run_case allow "rm file (no -rf)"        "rm ./tmp.txt"
run_case allow "rm -r alone"             "rm -r ./cache"
run_case allow "git push"                "git push origin main"
run_case allow "DELETE with WHERE"       "psql -c \"DELETE FROM users WHERE id = 1;\""
run_case allow "echo hello"              "echo hello world"
run_case allow "pwd"                     "pwd"
run_case allow "SELECT"                  "psql -c 'SELECT * FROM users;'"

echo
echo "== log write check =="
LOG="$HOME/.claude/hooks/blocked.log"
BEFORE=$(wc -l < "$LOG" 2>/dev/null || echo 0)
run_case deny "log sample" "rm -rf /tmp/log-check-$$"
AFTER=$(wc -l < "$LOG" 2>/dev/null || echo 0)
if [[ "$AFTER" -gt "$BEFORE" ]] && tail -n1 "$LOG" | grep -q "rm -rf"; then
  echo "  ok    log    blocked.log grew and contains pattern"
  PASS=$((PASS + 1))
else
  echo "  FAIL  log    blocked.log did not record attempt"
  FAIL=$((FAIL + 1))
fi

echo
echo "== summary =="
echo "passed=$PASS failed=$FAIL"
if [[ "$FAIL" -ne 0 ]]; then
  exit 1
fi
echo "ALL OK"
