#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════╗
# ║  Test suite for Destructive Command Guard hook           ║
# ║  Tests: blocked patterns, allowed patterns, log output   ║
# ╚══════════════════════════════════════════════════════════╝

set -uo pipefail

HOOK="$(dirname "$0")/../guard.sh"
PASS="\033[32m✓\033[0m"
FAIL="\033[31m✗\033[0m"
PASSED=0
FAILED=0

# Use temp log to avoid polluting real log
export HOME=$(mktemp -d)
mkdir -p "$HOME/.claude/hooks"

test_blocked() {
  local name="$1"
  local command="$2"
  local input="{\"tool_input\":{\"command\":\"$command\"},\"cwd\":\"/tmp/test\"}"
  local output
  output=$(echo "$input" | bash "$HOOK" 2>/dev/null)
  if echo "$output" | grep -q '"deny"'; then
    echo -e "  $PASS BLOCKED: $name"
    ((PASSED++))
  else
    echo -e "  $FAIL SHOULD BLOCK: $name (got: $output)"
    ((FAILED++))
  fi
}

test_allowed() {
  local name="$1"
  local command="$2"
  local input="{\"tool_input\":{\"command\":\"$command\"},\"cwd\":\"/tmp/test\"}"
  local output
  output=$(echo "$input" | bash "$HOOK" 2>/dev/null)
  if [ -z "$output" ] || ! echo "$output" | grep -q '"deny"'; then
    echo -e "  $PASS ALLOWED: $name"
    ((PASSED++))
  else
    echo -e "  $FAIL SHOULD ALLOW: $name (got: $output)"
    ((FAILED++))
  fi
}

echo ""
echo "🛡️ Destructive Command Guard — Test Suite"
echo ""

# ─── Blocked Commands ────────────────────────────────────────
echo "🔴 Should BLOCK:"
test_blocked "rm -rf /"           "rm -rf /"
test_blocked "rm -rf /home"       "rm -rf /home/user/important"
test_blocked "rm -fr ."           "rm -fr ."
test_blocked "sudo rm -rf"        "sudo rm -rf /var/log"
test_blocked "DROP TABLE"         "psql -c 'DROP TABLE users'"
test_blocked "DROP DATABASE"      "mysql -e 'DROP DATABASE prod'"
test_blocked "TRUNCATE TABLE"     "psql -c 'TRUNCATE TABLE orders'"
test_blocked "DELETE without WHERE" "psql -c 'DELETE FROM users'"
test_blocked "git push --force"   "git push --force origin main"
test_blocked "git push -f"        "git push -f origin main"
test_blocked "mkfs"               "mkfs.ext4 /dev/sda1"
test_blocked "dd of=/dev"         "dd if=/dev/zero of=/dev/sda bs=1M"
test_blocked "chmod 777"          "chmod 777 /etc/passwd"
test_blocked "fork bomb"          ':(){ :|:& };:'

echo ""

# ─── Allowed Commands ────────────────────────────────────────
echo "🟢 Should ALLOW:"
test_allowed "rm single file"     "rm file.txt"
test_allowed "rm -r (no -f)"     "rm -r temp_dir"
test_allowed "git push"          "git push origin main"
test_allowed "git push --force-with-lease" "git push --force-with-lease origin main"
test_allowed "npm install"       "npm install express"
test_allowed "pip install"       "pip install requests"
test_allowed "ls -la"            "ls -la /home"
test_allowed "cat file"          "cat README.md"
test_allowed "DELETE with WHERE" "psql -c 'DELETE FROM users WHERE id = 5'"
test_allowed "SELECT"            "psql -c 'SELECT * FROM users'"
test_allowed "echo"              "echo hello world"
test_allowed "mkdir"             "mkdir -p /tmp/test"
test_allowed "chmod 644"         "chmod 644 file.txt"
test_allowed "git commit"        "git commit -m 'fix: stuff'"

echo ""

# ─── Log Output Test ─────────────────────────────────────────
echo "📝 Log output:"
LOG="$HOME/.claude/hooks/blocked.log"
if [ -f "$LOG" ]; then
  LINES=$(wc -l < "$LOG")
  echo -e "  $PASS blocked.log has $LINES entries"
  ((PASSED++))
  echo "  Sample entry: $(head -1 "$LOG")"
else
  echo -e "  $FAIL blocked.log not created"
  ((FAILED++))
fi

echo ""

# ─── Results ──────────────────────────────────────────────────
echo "────────────────────────────────────────"
echo "Results: $PASSED passed, $FAILED failed"

# Cleanup
rm -rf "$HOME"

exit $FAILED
