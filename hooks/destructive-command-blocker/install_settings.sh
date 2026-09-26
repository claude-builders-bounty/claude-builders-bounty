#!/usr/bin/env bash
set -euo pipefail
umask 077

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
hook_src="$script_dir/block_destructive_bash.sh"
hook_dst="$HOME/.claude/hooks/block_destructive_bash.sh"
settings_path="$HOME/.claude/settings.json"
backup_path="$settings_path.bak"
backup_tmp=""
settings_tmp=""

cleanup_temporary_files() {
  [[ -z "$backup_tmp" ]] || rm -f "$backup_tmp" 2>/dev/null || true
  [[ -z "$settings_tmp" ]] || rm -f "$settings_tmp" 2>/dev/null || true
}
trap cleanup_temporary_files EXIT

mkdir -p "$(dirname "$hook_dst")" "$(dirname "$settings_path")"

if [[ -f "$settings_path" ]]; then
  if [[ -L "$backup_path" ]]; then
    printf 'Refusing to overwrite symlink at %s\n' "$backup_path" >&2
    exit 1
  fi
  if [[ -e "$backup_path" && ! -f "$backup_path" ]]; then
    printf 'Refusing to overwrite non-file at %s\n' "$backup_path" >&2
    exit 1
  fi
fi

if [[ -L "$hook_dst" ]]; then
  printf 'Refusing to overwrite symlink at %s\n' "$hook_dst" >&2
  exit 1
fi
if [[ -e "$hook_dst" ]]; then
  if [[ ! -f "$hook_dst" ]]; then
    printf 'Refusing to overwrite non-file at %s\n' "$hook_dst" >&2
    exit 1
  fi
  if ! cmp -s "$hook_src" "$hook_dst"; then
    printf 'Refusing to overwrite different existing hook at %s\n' "$hook_dst" >&2
    exit 1
  fi
fi

if [[ ! -e "$hook_dst" ]]; then
  cp "$hook_src" "$hook_dst"
fi
chmod 700 "$hook_dst"

if [[ -f "$settings_path" ]]; then
  backup_tmp="$(mktemp "${backup_path}.tmp.XXXXXX")"
  cp "$settings_path" "$backup_tmp"
  chmod 600 "$backup_tmp"
  mv -f "$backup_tmp" "$backup_path"
  backup_tmp=""
fi

settings_tmp="$(mktemp "${settings_path}.tmp.XXXXXX")"
chmod 600 "$settings_tmp"

node -e '
  const fs = require("node:fs");
  const path = process.argv[1];
  const temporaryPath = process.argv[2];
  const command = "bash ~/.claude/hooks/block_destructive_bash.sh";
  let settings = {};

  if (fs.existsSync(path)) {
    settings = JSON.parse(fs.readFileSync(path, "utf8"));
  }

  if (!settings.hooks || typeof settings.hooks !== "object" || Array.isArray(settings.hooks)) {
    settings.hooks = {};
  }
  if (!Array.isArray(settings.hooks.PreToolUse)) {
    settings.hooks.PreToolUse = [];
  }

  let bashMatcher = settings.hooks.PreToolUse.find(
    (entry) => entry && entry.matcher === "Bash" && Array.isArray(entry.hooks)
  );
  if (!bashMatcher) {
    bashMatcher = { matcher: "Bash", hooks: [] };
    settings.hooks.PreToolUse.push(bashMatcher);
  }

  if (!bashMatcher.hooks.some((hook) => hook?.type === "command" && hook.command === command)) {
    bashMatcher.hooks.push({ type: "command", command });
  }

  fs.writeFileSync(temporaryPath, JSON.stringify(settings, null, 2) + "\n", "utf8");
  fs.renameSync(temporaryPath, path);
' "$settings_path" "$settings_tmp"
settings_tmp=""

printf 'Installed destructive command blocker at %s and updated %s\n' "$hook_dst" "$settings_path"
