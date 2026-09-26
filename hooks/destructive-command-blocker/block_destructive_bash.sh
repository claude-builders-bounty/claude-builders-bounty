#!/usr/bin/env bash
set -uo pipefail
umask 077

payload="$(cat)"

json_escape() {
  sed -E 's/\\/\\\\/g; s/"/\\"/g' <<< "$1" | tr -d '\n'
}

parsed_fields=()
while IFS= read -r -d '' parsed_field; do
  parsed_fields+=("$parsed_field")
done < <(
  printf '%s' "$payload" | node -e '
    let input = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => { input += chunk; });
    process.stdin.on("end", () => {
      try {
        const data = JSON.parse(input);
        const values = [
          data?.tool_name ?? "",
          data?.tool_input?.command ?? data?.command ?? "",
          data?.tool_input?.cwd ?? data?.cwd ?? data?.project_path ?? "",
          "ok",
        ];
        for (const value of values) {
          process.stdout.write((typeof value === "string" ? value : "") + "\0");
        }
      } catch {
        for (const value of ["", "", "", "invalid"]) process.stdout.write(value + "\0");
      }
    });
  '
)

parser_status="${parsed_fields[3]:-invalid}"
if [[ "$parser_status" != "ok" ]]; then
  reason="invalid hook payload"
  command="[unparseable hook payload]"
  project_path="${CLAUDE_PROJECT_DIR:-$(pwd)}"
  log_path="${CLAUDE_HOOKS_LOG_PATH:-$HOME/.claude/hooks/blocked.log}"
  mkdir -p "$(dirname "$log_path")"
  chmod 600 "$log_path" 2>/dev/null || true
  timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  printf '{"timestamp":"%s","command":"%s","project_path":"%s","reason":"%s"}\n' \
    "$(json_escape "$timestamp")" "$(json_escape "$command")" \
    "$(json_escape "$project_path")" "$(json_escape "$reason")" >> "$log_path"
  printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Blocked destructive Bash command: invalid hook payload. Refusing to execute an unverified command."}}'
  exit 0
fi

tool_name="${parsed_fields[0]:-}"
if [[ -n "$tool_name" && "$tool_name" != "Bash" ]]; then
  exit 0
fi

command="${parsed_fields[1]:-}"
if [[ -z "$command" ]]; then
  exit 0
fi

project_path="${parsed_fields[2]:-}"
if [[ -z "$project_path" ]]; then
  project_path="${CLAUDE_PROJECT_DIR:-$(pwd)}"
fi

lower_command="$(printf '%s' "$command" | tr '[:upper:]' '[:lower:]')"
reason=""
rm_command_prefix='(^|[[:space:];&|/]|\\)rm'
rm_combined_rf_pattern="${rm_command_prefix}[[:space:]]+-[[:alnum:]_-]*r[[:alnum:]_-]*f[[:alnum:]_-]*($|[[:space:]])"
rm_combined_fr_pattern="${rm_command_prefix}[[:space:]]+-[[:alnum:]_-]*f[[:alnum:]_-]*r[[:alnum:]_-]*($|[[:space:]])"
rm_separate_rf_pattern="${rm_command_prefix}[[:space:]]+-[[:alnum:]_-]*r[[:alnum:]_-]*[[:space:]]+-[[:alnum:]_-]*f[[:alnum:]_-]*($|[[:space:]])"
rm_separate_fr_pattern="${rm_command_prefix}[[:space:]]+-[[:alnum:]_-]*f[[:alnum:]_-]*[[:space:]]+-[[:alnum:]_-]*r[[:alnum:]_-]*($|[[:space:]])"
rm_long_flags_pattern="${rm_command_prefix}[[:space:]][^;&|]*(--recursive|-[[:alnum:]_-]*r)[^;&|]*(--force|-[[:alnum:]_-]*f)"
sql_runner_pattern='(^|[[:space:];&|])(psql|mysql|sqlite3|sqlcmd)[[:space:]]'
bare_sql_pattern='(^|[;&|])[[:space:]]*(drop[[:space:]]+table|delete[[:space:]]+from|truncate[[:space:]]+[^-[:space:]])'
bare_sql_commented_drop_pattern='(^|[;&|])[[:space:]]*drop[^;&|]*(/[*]|--)[^;&|]*table'
sql_comment_pattern='(--|/[*])'
force_config_pattern='git[[:space:]][^;&|]*-c[[:space:]]+push[.]force=[^;&|]*push'
git_push_prefix='(^|[[:space:];&|/])git[[:space:]]+([^[:space:];&|]+[[:space:]]+)*push[[:space:]]+'
force_long_push_pattern="${git_push_prefix}[^;&|]*(--force-with-lease|--force)([^[:alnum:]_-]|$)"
force_short_push_pattern="${git_push_prefix}[^;&|]*[[:space:]]-f($|[[:space:]])"
force_plus_ref_pattern="${git_push_prefix}[^;&|]*[[:space:]][+][^[:space:];&|]+"
reset_hard_pattern='(^|[[:space:];&|])git[[:space:]]+reset[[:space:]]+--hard($|[[:space:];&|])'
dd_device_pattern='(^|[[:space:];&|])dd[[:space:]][^;&|]*of=/dev/'
block_device_pattern='(^|[[:space:];&|])(mkfs|wipefs)([.]|[[:space:]])'
sql_execution_context=false
sql_has_comment=false
# Match a statement at the beginning of a SQL client's quoted command argument,
# not a quoted string literal inside a SELECT expression.
quoted_truncate_pattern="(^|[[:space:];&|])(psql|mysql|sqlcmd)[[:space:]][^\"';&|]*(-c|-e|-q|--command|--execute)([[:space:]]+|=)[\"'][[:space:]]*truncate([[:space:];]|$)"
sqlite_truncate_pattern="(^|[[:space:];&|])sqlite3[[:space:]]+[^[:space:]\"';&|]+[[:space:]]+[\"'][[:space:]]*truncate([[:space:];]|$)"
if [[ "$lower_command" =~ $sql_runner_pattern ]] ||
   [[ "$lower_command" =~ $bare_sql_pattern ]] ||
   [[ "$lower_command" =~ $bare_sql_commented_drop_pattern ]]; then
  sql_execution_context=true
fi
if [[ "$sql_execution_context" == true && "$lower_command" =~ $sql_comment_pattern ]]; then
  sql_has_comment=true
fi

if [[ "$lower_command" =~ $rm_combined_rf_pattern ]] ||
   [[ "$lower_command" =~ $rm_combined_fr_pattern ]] ||
   [[ "$lower_command" =~ $rm_separate_rf_pattern ]] ||
   [[ "$lower_command" =~ $rm_separate_fr_pattern ]] ||
   [[ "$lower_command" =~ $rm_long_flags_pattern ]] ||
   [[ "$lower_command" =~ ${rm_command_prefix}[[:space:]][^\;\&\|]*(--force|-[[:alnum:]_-]*f)[^\;\&\|]*(--recursive|-[[:alnum:]_-]*r) ]]; then
  reason="rm -rf recursive deletion"
elif [[ "$sql_execution_context" == true && "$lower_command" =~ drop[[:space:]]+table ]] ||
     [[ "$sql_execution_context" == true && "$sql_has_comment" == true && "$lower_command" =~ drop && "$lower_command" =~ table ]]; then
  reason="DROP TABLE statement"
elif [[ "$sql_execution_context" == true ]] &&
     { [[ "$lower_command" =~ (^|[[:space:]\;\&\|])truncate($|[[:space:]\;\&\|]) ]] ||
       [[ "$lower_command" =~ $quoted_truncate_pattern ]] ||
       [[ "$lower_command" =~ $sqlite_truncate_pattern ]]; }; then
  reason="TRUNCATE statement"
elif [[ "$lower_command" =~ $force_long_push_pattern ]] ||
     [[ "$lower_command" =~ $force_short_push_pattern ]] ||
     [[ "$lower_command" =~ $force_config_pattern ]] ||
     [[ "$lower_command" =~ $force_plus_ref_pattern ]]; then
  reason="force push"
elif [[ "$sql_execution_context" == true && "$lower_command" =~ delete[[:space:]]+from ]] &&
     { [[ "$sql_has_comment" == true ]] || [[ ! "$lower_command" =~ where ]]; }; then
  reason="DELETE FROM without WHERE clause"
elif [[ "$lower_command" =~ $reset_hard_pattern ]]; then
  reason="git reset --hard"
elif [[ "$lower_command" =~ $dd_device_pattern ]] ||
     [[ "$lower_command" =~ $block_device_pattern ]]; then
  reason="block device destruction"
elif { [[ "$lower_command" == *curl* ]] || [[ "$lower_command" == *wget* ]]; } &&
     [[ "$lower_command" == *"|"* ]] &&
     { [[ "$lower_command" == *bash* ]] || [[ "$lower_command" == *" sh"* ]] || [[ "$lower_command" == *"|sh"* ]]; }; then
  reason="remote script execution"
fi

if [[ -z "$reason" ]]; then
  exit 0
fi

log_path="${CLAUDE_HOOKS_LOG_PATH:-$HOME/.claude/hooks/blocked.log}"
mkdir -p "$(dirname "$log_path")"
chmod 600 "$log_path" 2>/dev/null || true
timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
printf '{"timestamp":"%s","command":"%s","project_path":"%s","reason":"%s"}\n' \
  "$(json_escape "$timestamp")" \
  "$(json_escape "$command")" \
  "$(json_escape "$project_path")" \
  "$(json_escape "$reason")" >> "$log_path"

message="Blocked destructive Bash command: $reason. Review the command and rerun only if this destructive action is intentional and safe."
printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' \
  "$(json_escape "$message")"
exit 0
