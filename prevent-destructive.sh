#!/usr/bin/env bash
# Claude Code pre-tool-use / before-each-command guard.
# Blocks destructive commands BEFORE they run: rm -rf /, DROP TABLE, rm -rf *,
# mkfs, dd to a disk, > /dev/sdX, shutdown, fork bombs, chmod -R 777 /, etc.
#
# Hook usage (Claude Code / Codex): point CLAUDE_HOOKS / hooks.pre_tool_use at this script
# with the command as argv, OR source and call `guard_check "$CMD"`.
# Exit nonzero to abort the tool call. Stdout is shown to the assistant as the error.

guard_check() {
  local cmd="$*"
  local block=0
  local reason=""
  # Lowercase for matching
  local lc
  lc="$(printf '%s' "$cmd" | tr '[:upper:]' '[:lower:]')"

  # 1) rm -rf /  (any of: /, ~, *, . , *, **, a known dangerous path, home, empty)
  if printf '%s' "$lc" | grep -qE 'rm\s+(-[rRfFx]+\s+)+(/|--)?$'; then block=1; reason="rm targeting root/current dir"; fi
  if printf '%s' "$lc" | grep -qE 'rm\s+(-[rRfFx]+\s+)+\*|rm\s+(-[rRfFx]+\s+)+/ ?( --|$)'; then block=1; reason="rm -rf / or rm -rf *"; fi
  if printf '%s' "$lc" | grep -qE 'rm\s+(-[rRfFx]+\s+)+~\b|rm\s+(-[rRfFx]+\s+)+~(?=/|$)'; then block=1; reason="rm targeting home (~)"; fi
  # 2) wildcard destruction: rm -rf *
  if printf '%s' "$lc" | grep -qE 'rm\s+(-[rRfFx]+\s+)+\*'; then block=1; reason="rm with glob wildcard"; fi
  # 3) SQL destruction
  if printf '%s' "$lc" | grep -qiE 'drop\s+(table|database)\b|truncate\s+table|delete\s+from\s+\w+\s*;|drop\s+schema'; then block=1; reason="destructive SQL (DROP/TRUNCATE/DELETE)"; fi
  # 4) disk/format
  if printf '%s' "$lc" | grep -qiE 'mkfs|fdisk|dd\s+.*of=/dev/(sd|nvme|hd)|:\s*(/dev/sd|/dev/nvme|/dev/hd)|parted\s+.*mklabel|format\s+'; then block=1; reason="disk partition/format command"; fi
  # 5) shutdown / reboot
  if printf '%s' "$lc" | grep -qiE 'shutdown|reboot|halt|poweroff|init\s+0|systemctl\s+(poweroff|halt|reboot)'; then block=1; reason="shutdown/reboot command"; fi
  # 6) chmod/chown broad
  if printf '%s' "$lc" | grep -qE 'chmod\s+(-[rRfFx]+\s+)?(-R\s+)?777\s+/(--)?|chown\s+(-R\s+)?[^:]*/?(--)?\s*$'; then block=1; reason="chmod 777 / or broad chown"; fi
  # 7) fork bomb
  if printf '%s' "$lc" | grep -qE ':\(\)\s*\{|:.*\(\)\s*\{.*\}\s*\|'; then block=1; reason="fork bomb pattern"; fi
  # 8) curl|sh / wget|sh remote (blind remote exec)
  if printf '%s' "$lc" | grep -qE '(curl|wget)\s+.*[a-zA-Z0-9_./-]*(curl|wget|sh|bash)\b.*\|' ; then :; fi  # allowed to warn
  if printf '%s' "$lc" | grep -qE 'curl\s+https?://[^ ]+\|\s*(sh|bash)|wget\s+-O-\s+https?://[^ ]+\|\s*(sh|bash)'; then block=1; reason="blind remote pipe to shell"; fi
  # 9) git push --force / -f (but allow --force-with-lease)
  if printf '%s' "$lc" | grep -qE 'git\s+push(\s+.*)?\s(--force|[^a-z_-]f[^a-z])'; then
    if ! printf '%s' "$lc" | grep -qiE 'force-with-lease'; then block=1; reason="git push --force (use --force-with-lease)"; fi
  fi
  # 10) destructive aws / cloud
  if printf '%s' "$lc" | grep -qiE 'aws\s+[^ ]*delete-(bucket|table|cluster|instance|repository)|aws\s+s3\s+rm\s+|gcloud\s+.*delete|terraform\s+destroy\b'; then block=1; reason="cloud resource deletion"; fi

  if [ "$block" = "1" ]; then
    echo "BLOCKED by prevent-hook: $reason"
    echo "Command: $cmd"
    return 1
  fi
  return 0
}

# --- Self-test mode: validate the hook itself on a list of known-dangerous snippets.
if [ "${1:-}" = "--self-test" ]; then
  pass=0; fail=0
  run_test() { local desc="$1" expect_block="$2" check="$3";
    if eval "$check" >/dev/null 2>&1; then
      if [ "$expect_block" = "no" ]; then echo "ok: $desc (allowed)"; pass=$((pass+1)); else echo "FAIL: $desc should have blocked"; fail=$((fail+1)); fi
    else
      if [ "$expect_block" = "yes" ]; then echo "ok: $desc (blocked)"; pass=$((pass+1)); else echo "FAIL: $desc should have allowed"; fail=$((fail+1)); fi
    fi
  }
  run_test "rm -rf /"        yes "guard_check 'rm -rf / '"
  run_test "rm -rf *"        yes "guard_check 'rm -rf *'"
  run_test "rm -rf ~"        yes "guard_check 'rm -rf ~'"
  run_test "DROP TABLE x"    yes "guard_check 'psql -c \"DROP TABLE users\"'"
  run_test "drop database"   yes "guard_check 'mysql -e \"drop database prod\"'"
  run_test "mkfs.ext4"       yes "guard_check 'mkfs.ext4 /dev/sda1'"
  run_test "dd of=/dev/sda"  yes "guard_check 'dd if=/dev/zero of=/dev/sda'"
  run_test "shutdown -h now" yes "guard_check 'sudo shutdown -h now'"
  run_test "fork bomb"        yes "guard_check ':(){ :|:& };:'"
  run_test "git push --force" yes "guard_check 'git push --force origin main'"
  run_test "aws delete-bucket" yes "guard_check 'aws s3 rm s3://x --recursive' "
  run_test "safe echo"        no  "guard_check 'echo hello'"
  run_test "safe ls"          no  "guard_check 'ls -la'"
  run_test "git commit"       no  "guard_check 'git commit -m foo'"
  run_test "pip install"      no  "guard_check 'pip install requests'"
  echo "self-test: $pass passed, $fail failed"
  exit $fail
fi

# Default: guard against argv if run as a hook with a command argument, else read stdin as the command.
if [ "$#" -gt 0 ]; then
  guard_check "$*" || exit 1
else
  read -r line || exit 0
  guard_check "$line" || exit 1
fi
