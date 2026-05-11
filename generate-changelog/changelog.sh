#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Generate a structured CHANGELOG.md from git history.

Usage:
  bash changelog.sh [options]

Options:
  --dry-run            Print generated changelog to stdout instead of writing a file.
  --output PATH        Changelog output path. Default: CHANGELOG.md.
  --since REF          Git ref to start after. Default: latest reachable tag.
  --version VERSION    Release version heading. Default: current date.
  --help               Show this help message.
USAGE
}

output_file="CHANGELOG.md"
dry_run=0
since_ref=""
version=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --dry-run)
      dry_run=1
      ;;
    --output)
      if [ "$#" -lt 2 ]; then
        echo "error: --output requires a path" >&2
        exit 2
      fi
      output_file="$2"
      shift
      ;;
    --since)
      if [ "$#" -lt 2 ]; then
        echo "error: --since requires a git ref" >&2
        exit 2
      fi
      since_ref="$2"
      shift
      ;;
    --version)
      if [ "$#" -lt 2 ]; then
        echo "error: --version requires a value" >&2
        exit 2
      fi
      version="$2"
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

if [ -z "$version" ]; then
  version="$(date +%Y-%m-%d)"
fi

range_label="all history"
range_spec=""
if [ -n "$since_ref" ]; then
  if ! git rev-parse --verify --quiet "$since_ref^{commit}" >/dev/null; then
    echo "error: --since ref not found: $since_ref" >&2
    exit 1
  fi
  range_spec="${since_ref}..HEAD"
  range_label="since ${since_ref}"
else
  latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
  if [ -n "$latest_tag" ]; then
    range_spec="${latest_tag}..HEAD"
    range_label="since ${latest_tag}"
  fi
fi

if [ -n "$range_spec" ]; then
  commit_lines="$(git log "$range_spec" --reverse --pretty=format:'%h%x09%s' 2>/dev/null || true)"
else
  commit_lines="$(git log --reverse --pretty=format:'%h%x09%s' 2>/dev/null || true)"
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

added="$tmp_dir/added"
fixed="$tmp_dir/fixed"
changed="$tmp_dir/changed"
removed="$tmp_dir/removed"
touch "$added" "$fixed" "$changed" "$removed"

append_entry() {
  local target="$1"
  local sha="$2"
  local subject="$3"
  printf -- '- %s (`%s`)\n' "$subject" "$sha" >> "$target"
}

normalize_subject() {
  local subject="$1"
  subject="${subject//$'\r'/}"
  subject="${subject#"${subject%%[![:space:]]*}"}"
  subject="${subject%"${subject##*[![:space:]]}"}"
  printf '%s' "$subject"
}

if [ -n "$commit_lines" ]; then
  while IFS=$'\t' read -r sha subject; do
    [ -n "$sha" ] || continue
    subject="$(normalize_subject "$subject")"
    [ -n "$subject" ] || continue

    lower_subject="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
    case "$lower_subject" in
      remove:*|removed:*|delete:*|deleted:*|drop:*|dropped:*|deprecate:*|deprecated:*|revert:*|\
      remove\ *|removed\ *|delete\ *|deleted\ *|drop\ *|dropped\ *|deprecate\ *|deprecated\ *|revert\ *)
        append_entry "$removed" "$sha" "$subject"
        ;;
      fix:*|fixed:*|bugfix:*|patch:*|repair:*|resolve:*|resolved:*|\
      fix\ *|fixed\ *|bugfix\ *|patch\ *|repair\ *|resolve\ *|resolved\ *)
        append_entry "$fixed" "$sha" "$subject"
        ;;
      feat:*|feature:*|add:*|added:*|create:*|created:*|implement:*|implemented:*|introduce:*|introduced:*|\
      feat\(*|fix\(*|chore\(*|docs\(*|style\(*|refactor\(*|perf\(*|test\(*|ci\(*|build\(*)
        if [[ "$lower_subject" == feat* || "$lower_subject" == feature* || "$lower_subject" == add* || "$lower_subject" == create* || "$lower_subject" == implement* || "$lower_subject" == introduce* ]]; then
          append_entry "$added" "$sha" "$subject"
        elif [[ "$lower_subject" == fix* ]]; then
          append_entry "$fixed" "$sha" "$subject"
        else
          append_entry "$changed" "$sha" "$subject"
        fi
        ;;
      add\ *|added\ *|create\ *|created\ *|implement\ *|implemented\ *|introduce\ *|introduced\ *)
        append_entry "$added" "$sha" "$subject"
        ;;
      *)
        append_entry "$changed" "$sha" "$subject"
        ;;
    esac
  done <<< "$commit_lines"
fi

new_section="$tmp_dir/new-section"
{
  echo "## ${version}"
  echo
  echo "_Generated from git commits ${range_label}._"
  echo
  for section in "Added:$added" "Fixed:$fixed" "Changed:$changed" "Removed:$removed"; do
    title="${section%%:*}"
    file="${section#*:}"
    echo "### ${title}"
    echo
    if [ -s "$file" ]; then
      cat "$file"
    else
      echo "- No changes."
    fi
    echo
  done
} > "$new_section"

if [ "$dry_run" -eq 1 ]; then
  cat "$new_section"
  exit 0
fi

existing_content=""
if [ -f "$output_file" ]; then
  existing_content="$(cat "$output_file")"
fi

{
  echo "# Changelog"
  echo
  cat "$new_section"
  if [ -n "$existing_content" ]; then
    stripped_existing="$(printf '%s\n' "$existing_content" | sed '1{/^# Changelog$/d;}')"
    if [ -n "$(printf '%s' "$stripped_existing" | tr -d '[:space:]')" ]; then
      echo
      printf '%s\n' "$stripped_existing" | sed '/./,$!d'
    fi
  fi
} > "$output_file"

echo "Wrote ${output_file} (${range_label})"
