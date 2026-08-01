#!/usr/bin/env bash
# guard.sh — Claude Code PreToolUse hook: block destructive bash commands.
# Stdin:  JSON event {"tool_name":"Bash","tool_input":{"command":"..."},"cwd":"...",...}
# Behaviour: exit 2 => BLOCK the call (stderr is reported back to Claude).
#            exit 0 (no stdout) => ALLOW.
# Every blocked attempt is appended to ~/.claude/hooks/blocked.log as:
#   <iso8601 utc>\t<project path>\t<attempted command>
# Install: see README.md (one settings.json entry + chmod +x).
set -euo pipefail

LOG_FILE="${CLAUDE_HOOK_BLOCK_LOG:-$HOME/.claude/hooks/blocked.log}"

# Only inspect Bash tool calls
input="$(cat)"
tool="$(printf '%s' "$input" | grep -o '"tool_name"[^,}]*' | cut -d'"' -f4 || true)"
[ "$tool" = "Bash" ] || exit 0

cmd="$(printf '%s' "$input" | sed -n 's/.*"tool_input"[^}]*"command"[^"]*"\([^"]*\)".*/\1/p' | head -c 4000)"
cwd="$(printf '%s' "$input" | grep -o '"cwd"[^,}]*' | cut -d'"' -f4 || true)"
[ -n "$cwd" ] || cwd="$PWD"
# Unescape JSON basics for pattern matching; harmless if imprecise.
cmd_dec="$(printf '%s' "$cmd" | sed 's/\\\\/\\/g; s/\\n/ /g' | tr 'A-Z' 'a-z' | tr -s ' ')"

block() {
  # Log: timestamp, project path, attempted command (requirement of the hook spec)
  mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true
  printf '%s\t%s\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$cwd" "$cmd" >> "$LOG_FILE" 2>/dev/null || true
  echo "BLOCKED by safety hook: $1" >&2
  exit 2
}

# --- Destructive filesystem ---
grep -qE '(^|sudo[[:space:]]+|[;&|][[:space:]]*)rm[[:space:]]+(-[a-z]*[rf][a-z]*[[:space:]]+)*.*(/$|/\s|/\*|~|\$home|\.\.|/etc|/usr|/var|/bin|/lib|/boot|/opt|/srv|/home)' <<<"$cmd_dec" \
  && block "recursive/forced rm on system or home path"
grep -qE '\brm[[:space:]]+-[a-z]*[rf].*[[:space:]](/|\./)[[:space:]]*$' <<<"$cmd_dec" \
  && block "rm -rf on root or cwd"
grep -qE '\bmkfs\b|\bdd\b[^|]*of=/dev/|:\(\) ?\{ ?:\|:\& ?\};?:' <<<"$cmd_dec" \
  && block "disk/format/forkbomb pattern"
grep -qE '>\s*/dev/sd[a-z]|>\s*/dev/nvme|>\s*/dev/mmcblk' <<<"$cmd_dec" \
  && block "raw write to block device"

# --- Database destruction ---
# Don't fire on text-processing one-liners (grep/sed/awk/echo/...) where the SQL
# keyword only appears inside a quoted literal or pattern argument.
sql_blocked=1
grep -qE '(^|[;&|][[:space:]]*)(grep|egrep|fgrep|rg|sed|awk|echo|printf|cat|head|tail|less|more|vi|vim|nano)[[:space:]]' <<<"$cmd_dec" \
  || sql_blocked=0
if [ "$sql_blocked" -eq 0 ]; then
grep -qE '\bdrop[[:space:]]+table\b' <<<"$cmd_dec" \
  && block "DROP TABLE destroys data irreversibly"
grep -qE '\btruncate([[:space:]]+table)?[[:space:]]+[a-z_]' <<<"$cmd_dec" \
  && block "TRUNCATE wipes an entire table"
grep -qE '\bdelete[[:space:]]+from[[:space:]]+\S+' <<<"$cmd_dec" \
  && ! grep -qiwE 'where' <<<"$cmd_dec" \
  && block "DELETE FROM without a WHERE clause"
fi

# --- Git / repo damage ---
grep -qE 'git[[:space:]]+push[[:space:]].*(--force|-f)([[:space:]]|$).*(main|master)' <<<"$cmd_dec" \
  && block "force push to main/master"
grep -qE 'git[[:space:]]+reset[[:space:]]+--hard[[:space:]]*$' <<<"$cmd_dec" \
  && block "bare git reset --hard (undefended)"
grep -qE 'git[[:space:]]+clean[[:space:]]+-[a-z]*[fx][a-z]*[df]?\b' <<<"$cmd_dec" \
  && grep -qE 'git[[:space:]]+clean[[:space:]]+-[a-z]*[df]' <<<"$cmd_dec" \
  && block "git clean -fd deletes untracked dirs"

# --- System/service damage ---
grep -qE '\b(systemctl|svc|service)\s+(stop|disable|mask)\b|\bservice\s+[a-z0-9._-]+\s+(stop|disable)' <<<"$cmd_dec" \
  && block "stopping/disabling system services from a coding agent"
grep -qE '\bshutdown\b|\breboot\b|\bhalt\b|\bpoweroff\b' <<<"$cmd_dec" \
  && block "host power operation"
grep -qE '\bkill(all)?\s+-9\s+-1\b|\bkillall\b' <<<"$cmd_dec" \
  && block "mass process kill"
grep -qE '\bchmod[[:space:]]+(-[a-z]+[[:space:]]+)?0?777[[:space:]]+(/|\.|\*)([[:space:]]|$)' <<<"$cmd_dec" \
  && block "recursive or broad permissive chmod"

# --- Exfiltration / remote code exec ---
grep -qE '(curl|wget)[^|]*\|\s*(sudo\s+)?(ba|z|d)?sh\b' <<<"$cmd_dec" \
  && block "pipe-to-shell remote execution"
grep -qE '/etc/(passwd|shadow)|\.ssh/id_|\.aws/credentials|\.env[^a-z]' <<<"$cmd_dec" \
  && grep -qE '(curl|wget|nc |ncat |scp |ftp )' <<<"$cmd_dec" \
  && block "possible secret exfiltration"

exit 0
