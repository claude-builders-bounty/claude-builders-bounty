#!/usr/bin/env bash
#
# block-destructive.sh — Claude Code PreToolUse hook for the Bash tool.
#
# Reads the hook JSON on stdin:
#   {"session_id":"...","tool_name":"Bash","tool_input":{"command":"..."},"cwd":"..."}
#
# Blocks these destructive patterns (case-insensitive where noted):
#   * rm -rf in any flag form: rm -rf, rm -fr, rm -r -f, rm --recursive --force
#   * DROP TABLE ...
#   * git push --force / git push -f / git push --force-with-lease
#   * TRUNCATE <table>
#   * DELETE FROM <table> WITHOUT a WHERE clause
#
# Quoted strings are stripped before matching, so mentions such as
#   echo "TRUNCATE is a word"
# do not trigger the hook.
#
# Blocking contract (https://code.claude.com/docs/en/hooks, PreToolUse):
#   allow -> exit 0, no stdout
#   block -> JSON decision on stdout AND reason on stderr AND exit code 2
#     (stdout JSON carries both the documented PreToolUse
#      hookSpecificOutput/permissionDecision form and a top-level
#      decision/reason form for older clients)
#
# Every blocked attempt is appended to $HOME/.claude/hooks/blocked.log:
#   <ISO timestamp> | command=<attempted command> | cwd=<project path>
#
# Dependencies: bash + coreutils (sed, grep, head, tr, date, mkdir, cat).
# No jq, no python.

set -u

# ---------------------------------------------------------------------------
# Log location (created on demand)
# ---------------------------------------------------------------------------
home_dir="${HOME:-}"
[ -n "$home_dir" ] || home_dir="/tmp"
LOG_DIR="$home_dir/.claude/hooks"
LOG_FILE="$LOG_DIR/blocked.log"

# ---------------------------------------------------------------------------
# 1. Read input. Never crash: empty or invalid input => allow silently.
# ---------------------------------------------------------------------------
input="$(cat 2>/dev/null || true)"
[ -n "$input" ] || exit 0

# Extract the value of a JSON string field (first occurrence) from $input,
# then undo basic JSON escapes (\" \\ \n \t \r).
json_field() {
  local name=$1 raw out="" i c n
  raw="$(printf '%s' "$input" \
    | sed -n 's/.*"'"$name"'"[[:space:]]*:[[:space:]]*"\(\(\\.\|[^"\\]\)*\)".*/\1/p' \
    | head -n 1)"
  n=${#raw}
  for ((i = 0; i < n; i++)); do
    c="${raw:i:1}"
    if [ "$c" = '\' ] && [ "$i" -lt $((n - 1)) ]; then
      i=$((i + 1))
      case "${raw:i:1}" in
        n) out+=$'\n' ;;
        t) out+=$'\t' ;;
        r) out+=$'\r' ;;
        *) out+="${raw:i:1}" ;;
      esac
    else
      out+="$c"
    fi
  done
  printf '%s' "$out"
}

command="$(json_field command)"
cwd="$(json_field cwd)"
[ -n "$command" ] || exit 0

# ---------------------------------------------------------------------------
# 2. Strip single- and double-quoted strings so quoted mentions of
#    dangerous words do not trigger. Newlines become spaces (token scans
#    are line-based).
# ---------------------------------------------------------------------------
strip_quotes() {
  local s=$1 out="" in_d=0 in_s=0 esc=0 i c
  for ((i = 0; i < ${#s}; i++)); do
    c="${s:i:1}"
    if [ "$in_d" -eq 1 ]; then
      if [ "$esc" -eq 1 ]; then esc=0
      elif [ "$c" = '\' ]; then esc=1
      elif [ "$c" = '"' ]; then in_d=0
      fi
      continue
    fi
    if [ "$in_s" -eq 1 ]; then
      [ "$c" = "'" ] && in_s=0
      continue
    fi
    case "$c" in
      '"') in_d=1 ;;
      "'") in_s=1 ;;
      *)   out+="$c" ;;
    esac
  done
  printf '%s' "$out"
}

cmd="$(strip_quotes "$command")"
cmd="$(printf '%s' "$cmd" | tr '\n' ' ')"

# ---------------------------------------------------------------------------
# 3. Rules. Each rule appends to $reasons when it fires.
# ---------------------------------------------------------------------------
reasons=""
add_reason() {
  if [ -n "$reasons" ]; then reasons="$reasons; $1"; else reasons=$1; fi
}

# Rule A: rm with BOTH recursive and force flags (combined or separate).
rule_rm_force() {
  local toks t n i j r f
  read -r -a toks <<< "$cmd"
  n=${#toks[@]}
  for ((i = 0; i < n; i++)); do
    case "${toks[i]}" in
      rm|*/rm) ;;
      *) continue ;;
    esac
    j=$((i + 1)); r=0; f=0
    while [ "$j" -lt "$n" ]; do
      t="${toks[j]}"
      case "$t" in
        --recursive*) r=1 ;;
        --force*)     f=1 ;;
        -?*)
          case "${t#-}" in *r*|*R*) r=1 ;; esac
          case "${t#-}" in *f*)     f=1 ;; esac
          ;;
        *) break ;;
      esac
      j=$((j + 1))
    done
    [ "$r" -eq 1 ] && [ "$f" -eq 1 ] && return 0
  done
  return 1
}

# Rule C: git push with a force flag after the push subcommand.
rule_git_force_push() {
  local toks t n i j in_push
  read -r -a toks <<< "$cmd"
  n=${#toks[@]}
  for ((i = 0; i < n; i++)); do
    case "${toks[i]}" in
      git|*/git) ;;
      *) continue ;;
    esac
    in_push=0
    j=$((i + 1))
    while [ "$j" -lt "$n" ]; do
      t="${toks[j]}"
      if [ "$in_push" -eq 1 ]; then
        case "$t" in
          -f)         return 0 ;;
          --force*)   return 0 ;;
          -*)         j=$((j + 1)); continue ;;
          *)          break ;;
        esac
      else
        case "$t" in
          push)        in_push=1; j=$((j + 1)); continue ;;
          -c|--config) j=$((j + 2)); continue ;;
          -*)          j=$((j + 1)); continue ;;
          *)           break ;;
        esac
      fi
    done
  done
  return 1
}

rule_rm_force && add_reason "rm -rf (recursive forced deletion)"
printf '%s' "$cmd" | grep -qiE '\bDROP[[:space:]]+TABLE\b' \
  && add_reason "DROP TABLE (irreversible schema destruction)"
rule_git_force_push && add_reason "git push force-push (rewrites remote history)"
printf '%s' "$cmd" | grep -qiE '\bTRUNCATE[[:space:]]+[A-Za-z_0-9(]' \
  && add_reason "TRUNCATE (irreversible table deletion)"
if printf '%s' "$cmd" | grep -qiE '\bDELETE[[:space:]]+FROM\b'; then
  if ! printf '%s' "$cmd" | grep -qiE '\bWHERE\b'; then
    add_reason "DELETE FROM without WHERE clause (deletes the entire table)"
  fi
fi

# ---------------------------------------------------------------------------
# 4. Verdict.
# ---------------------------------------------------------------------------
if [ -n "$reasons" ]; then
  ts="$(date '+%Y-%m-%dT%H:%M:%S%z' 2>/dev/null || echo unknown)"
  mkdir -p "$LOG_DIR" 2>/dev/null || true
  printf '%s | command=%s | cwd=%s\n' "$ts" "$command" "${cwd:-?}" >> "$LOG_FILE" 2>/dev/null || true

  msg="Blocked by destructive-command hook: $reasons."
  printf '{"decision":"block","reason":"%s","hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$msg" "$msg"
  printf '%s\n' "$msg" >&2
  exit 2
fi

exit 0
