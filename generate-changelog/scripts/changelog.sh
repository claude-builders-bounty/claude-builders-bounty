#!/usr/bin/env bash
# changelog.sh — generate a structured CHANGELOG.md section from git history.
# Usage:
#   bash changelog.sh [since-ref] [--stdout]
#     since-ref  tag/branch/commit to start from (default: latest reachable tag)
#     --stdout   print to stdout instead of writing CHANGELOG.md
# Writes CHANGELOG.md at the repo root by default. Prepend-only: preserves existing content.
set -euo pipefail

since_ref=""
to_stdout=""
for arg in "$@"; do
  case "$arg" in
    --stdout) to_stdout=1 ;;
    *) if [[ -z "$since_ref" ]]; then since_ref="$arg"; else
         echo "error: unexpected argument '$arg'" >&2; exit 2; fi ;;
  esac
done

# contract: write CHANGELOG.md on a TTY, print to stdout when piped; --stdout forces stdout
# CL_FORCE_FILE=1 overrides (for CI/test environments with no TTY)
if [[ -z "$to_stdout" ]]; then
  if [[ -n "${CL_FORCE_FILE:-}" ]] || [[ -t 1 ]]; then to_stdout=0; else to_stdout=1; fi
fi

# --- locate the repo root (works from subdirectories) ---
root="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "error: not inside a git repository" >&2
  exit 1
}
cd "$root"

# --- resolve the starting point ---
if [[ -z "$since_ref" ]]; then
  if since_ref="$(git describe --tags --abbrev=0 2>/dev/null)"; then
    range="$since_ref..HEAD"
  else
    # tagless repo: start from the first commit
    first="$(git rev-list --max-parents=0 HEAD | tail -n1)"
    range="$first..HEAD"
    since_ref=""
    echo "note: no tags found; using entire history since first commit" >&2
  fi
else
  if ! git rev-parse --verify --quiet "$since_ref^{commit}" >/dev/null; then
    echo "error: ref '$since_ref' not found" >&2
    exit 1
  fi
  range="$since_ref..HEAD"
fi

# --- collect commits (skip merge commits) ---
# bash 3.2 compatible (macOS): no mapfile
commits=()
while IFS= read -r c; do commits+=("$c"); done < <(git log "$range" --no-merges --pretty=format:%s 2>/dev/null || true)

if [[ ${#commits[@]} -eq 0 || ( ${#commits[@]} -eq 1 && -z "${commits[0]:-}" ) ]]; then
  echo "no commits since ${since_ref:-first commit}; nothing to add" >&2
  exit 0
fi

# --- categorize ---
added=() fixed=() changed=() removed=()

categorize() {
  local s
  s="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"   # bash 3.2 safe (no ${1,,})
  case "$s" in
    feat:*|feat\(*|add*|"support"*)       added+=("$1") ;;
    fix:*|fix\(*|bugfix*|"hotfix"*)       fixed+=("$1") ;;
    remove*|"drop"*|"delete"*|deprecate*) removed+=("$1") ;;
    refactor*|perf*|chore*|"improve"*|"update"*|"bump"*|"move"*|"rename"*|"split"*) changed+=("$1") ;;
    docs:*|doc:*|test:*|ci:*|build:*|style:*) changed+=("$1") ;;
    *add*|*support*)                      added+=("$1") ;;
    *fix*|*bug*)                          fixed+=("$1") ;;
    *remov*|*delet*|*drop*)               removed+=("$1") ;;
    *)                                    changed+=("$1") ;;
  esac
}

for c in "${commits[@]}"; do
  [[ -n "$c" ]] && categorize "$c"
done

strip_prefix() {
  local item="$1"
  item="${item#feat: }"; item="${item#fix: }"; item="${item#docs: }"; item="${item#doc: }"
  item="${item#chore: }"; item="${item#refactor: }"; item="${item#perf: }"
  item="${item#test: }"; item="${item#ci: }"; item="${item#build: }"; item="${item#style: }"
  printf '%s' "$item"
}

format_section() {
  local title="$1"; shift
  [[ $# -eq 0 ]] && return 0
  printf '### %s\n\n' "$title"
  local seen="" item
  for item in "$@"; do
    item="$(strip_prefix "$item")"
    if [[ ",$seen," == *",$item,"* ]]; then continue; fi
    seen="$seen,$item"
    if (( ${#item} > 100 )); then item="${item:0:97}..."; fi
    printf -- '- %s\n' "$item"
  done
  printf '\n'
}

# build each section, keep only non-empty ones (no namerefs: bash 3.2 safe)
body=""
append_section() {
  local title="$1"; shift
  local sec
  sec="$(format_section "$title" "$@")"
  if [[ -n "$sec" ]]; then
    # $( ) strips trailing newlines; restore the blank line that separates sections
    body+="$sec"$'\n\n'
  fi
}
append_section "Added" "${added[@]+"${added[@]}"}"
append_section "Fixed" "${fixed[@]+"${fixed[@]}"}"
append_section "Changed" "${changed[@]+"${changed[@]}"}"
append_section "Removed" "${removed[@]+"${removed[@]}"}"

if [[ -z "${body// }" ]]; then
  echo "error: nothing to write" >&2
  exit 1
fi

header="## [Unreleased] - $(date +%Y-%m-%d)"
new_block="$header

$body"

out="$root/CHANGELOG.md"

write_file() {
  if [[ -f "$out" ]] && grep -q '^## \[' "$out"; then
    # insert the new section after a leading '# Title' line, before the first '## [' section
    tmp="$(mktemp)"
    awk -v block="$new_block" '
      BEGIN { inserted = 0 }
      NR == 1 && /^# / { print; title_done = 1; next }
      !inserted && title_done && /^## \[/ {
        print block; print ""; inserted = 1
      }
      !inserted && !title_done && /^## \[/ {
        print block; print ""; inserted = 1
      }
      { print }
      END { if (!inserted) { print block; print "" } }
    ' "$out" > "$tmp"
    mv "$tmp" "$out"
  elif [[ -f "$out" ]]; then
    tmp="$(mktemp)"
    { printf '%s\n\n' "$new_block"; cat "$out"; } > "$tmp"
    mv "$tmp" "$out"
  else
    printf '# Changelog\n\n%s\n' "$new_block" > "$out"
  fi
  echo "wrote $out" >&2
}

if (( to_stdout )); then
  printf '%s\n' "$new_block"
else
  write_file
fi