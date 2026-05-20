#!/usr/bin/env bash
#
# test.sh -- exercise the safe-bash hook against block/allow fixtures.
#
# All 28 cases pass against pre_tool_use.py at commit time. Re-run anytime
# you change the block patterns to make sure nothing regressed.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="${SCRIPT_DIR}/pre_tool_use.py"

if [[ ! -x "$HOOK" ]]; then
    chmod +x "$HOOK"
fi

PASS=0
FAIL=0
FAILED_CASES=()

run_case() {
    local label="$1"
    local cmd="$2"
    local expected="$3"

    local payload
    payload=$(python3 -c "import json,sys; print(json.dumps({'tool_name':'Bash','tool_input':{'command':sys.argv[1]},'cwd':'/tmp/test'}))" "$cmd")

    local got_out
    got_out=$(echo "$payload" | python3 "$HOOK" 2>/dev/null)
    local got=$?

    if [[ "$got" == "$expected" ]]; then
        PASS=$((PASS + 1))
        echo "  PASS  [$label]"
    else
        FAIL=$((FAIL + 1))
        FAILED_CASES+=("$label (exit=$got expected=$expected, cmd=$cmd)")
        echo "  FAIL  [$label]  exit=$got expected=$expected"
    fi
}

echo "== BLOCK cases (expect exit 2) =="
run_case "rm -rf /"                       "rm -rf /"                                  2
run_case "rm -rf path"                    "rm -rf /tmp/foo"                           2
run_case "rm -fr"                         "rm -fr /tmp/foo"                           2
run_case "rm -rfv"                        "rm -rfv /tmp/foo"                          2
run_case "rm -Rf"                         "rm -Rf /tmp/foo"                           2
run_case "rm -r -f"                       "rm -r -f /tmp/foo"                         2
run_case "rm --recursive --force"         "rm --recursive --force /tmp/foo"           2
run_case "DROP TABLE"                     "psql -c 'DROP TABLE users'"                2
run_case "drop table (lowercase)"         "mysql -e 'drop table users'"               2
run_case "TRUNCATE TABLE"                 "psql -c 'TRUNCATE TABLE logs'"             2
run_case "DELETE FROM no WHERE"           "psql -c 'DELETE FROM users'"               2
run_case "delete from (lowercase)"        "mysql -e 'delete from users'"              2
run_case "git push --force"               "git push --force origin main"              2
run_case "git push -f"                    "git push -f origin main"                   2
run_case "git push +ref"                  "git push origin +main"                     2

echo
echo "== ALLOW cases (expect exit 0) =="
run_case "rm single file"                 "rm /tmp/foo.txt"                           0
run_case "rm -i"                          "rm -i /tmp/foo.txt"                        0
run_case "rm -r alone"                    "rm -r /tmp/foo"                            0
run_case "rm -f alone"                    "rm -f /tmp/foo"                            0
run_case "DELETE with WHERE"              "psql -c 'DELETE FROM users WHERE id=1'"    0
run_case "SELECT"                         "psql -c 'SELECT * FROM users'"             0
run_case "git push normal"                "git push origin main"                      0
run_case "git push --force-with-lease"    "git push --force-with-lease origin main"   0
run_case "ls"                             "ls -la /"                                  0
run_case "rfm typo (not rm)"              "rfm -x /tmp/foo"                           0
run_case "git rm a file"                  "git rm CHANGELOG.md"                       0

echo
echo "== Edge cases =="
echo '{"tool_name":"Read","tool_input":{"file_path":"/tmp/foo"}}' | python3 "$HOOK" >/dev/null 2>&1
if [[ $? -eq 0 ]]; then
    PASS=$((PASS + 1)); echo "  PASS  [non-Bash tool payload allowed]"
else
    FAIL=$((FAIL + 1)); echo "  FAIL  [non-Bash tool payload]"
fi

echo "" | python3 "$HOOK" >/dev/null 2>&1
if [[ $? -eq 0 ]]; then
    PASS=$((PASS + 1)); echo "  PASS  [empty stdin allowed]"
else
    FAIL=$((FAIL + 1)); echo "  FAIL  [empty stdin]"
fi

echo
echo "================================"
echo "  PASS: $PASS"
echo "  FAIL: $FAIL"
echo "================================"

if [[ $FAIL -gt 0 ]]; then
    echo
    echo "Failed cases:"
    for c in "${FAILED_CASES[@]}"; do
        echo "  - $c"
    done
    exit 1
fi
