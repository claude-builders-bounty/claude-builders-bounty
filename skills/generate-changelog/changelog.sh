#!/usr/bin/env bash
# Generate CHANGELOG.md from git history since the latest tag.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: changelog.sh [options] [REPO_PATH]

Options:
  -o, --output PATH   Write CHANGELOG.md to PATH (default: REPO_PATH/CHANGELOG.md)
  -f, --stdout        Print to stdout instead of writing a file
  -h, --help          Show this help

Environment:
  CHANGELOG_TITLE     Override the top-level heading (default: Changelog)
EOF
}

REPO_PATH=""
OUTPUT=""
STDOUT=0
TITLE="${CHANGELOG_TITLE:-Changelog}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output)
      OUTPUT="${2:?missing argument for $1}"
      shift 2
      ;;
    -f|--stdout)
      STDOUT=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "changelog.sh: unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
    *)
      if [[ -z "$REPO_PATH" ]]; then
        REPO_PATH="$1"
      else
        echo "changelog.sh: unexpected argument: $1" >&2
        exit 1
      fi
      shift
      ;;
  esac
done

REPO_PATH="${REPO_PATH:-.}"
REPO_PATH="$(cd "$REPO_PATH" && pwd)"

if ! git -C "$REPO_PATH" rev-parse --git-dir >/dev/null 2>&1; then
  echo "changelog.sh: not a git repository: $REPO_PATH" >&2
  exit 1
fi

if [[ -z "$OUTPUT" ]]; then
  OUTPUT="${REPO_PATH}/CHANGELOG.md"
fi

# --- categorization ---------------------------------------------------------

conventional_type() {
  local subject="$1"
  local lower type

  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  type="$(printf '%s' "$lower" | sed -E 's/^([a-z]+)(\([^)]*\))?!?:.*$/\1/')"
  if [[ "$type" == "$lower" ]]; then
    printf '\n'
    return
  fi
  printf '%s' "$type"
}

categorize_subject() {
  local subject="$1"
  local lower rest ctype

  ctype="$(conventional_type "$subject")"
  case "$ctype" in
    feat|feature) printf 'Added\n'; return ;;
    fix) printf 'Fixed\n'; return ;;
    remove|removal|delete|drop) printf 'Removed\n'; return ;;
    change|changed|chore|refactor|perf|docs|style|test|build|ci|revert|deprecate)
      printf 'Changed\n'
      return
      ;;
  esac

  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  rest="$lower"
  rest="${rest#feat!:}"
  rest="${rest#feat:}"
  rest="${rest#feature:}"
  rest="${rest#fix:}"
  rest="${rest#remove:}"
  rest="${rest#delete:}"

  case "$rest" in
    fix*|bugfix*|hotfix*|patch*) printf 'Fixed\n'; return ;;
    add*|new*|introduce*|feat*) printf 'Added\n'; return ;;
    remove*|deleted*|delete*|drop*|dropped*) printf 'Removed\n'; return ;;
    change*|changed*|update*|updated*|refactor*|chore*|perf*|docs*|style*|test*|build*|ci*|revert*|deprecate*)
      printf 'Changed\n'
      return
      ;;
  esac

  printf 'Changed\n'
}

format_bullet() {
  local hash="$1"
  local subject="$2"
  local short_hash

  short_hash="${hash:0:7}"
  printf -- '- %s (%s)\n' "$subject" "$short_hash"
}

append_line() {
  local category="$1"
  local line="$2"
  case "$category" in
    Added) ADDED="${ADDED}${line}"$'\n' ;;
    Fixed) FIXED="${FIXED}${line}"$'\n' ;;
    Removed) REMOVED="${REMOVED}${line}"$'\n' ;;
    *) CHANGED="${CHANGED}${line}"$'\n' ;;
  esac
}

# --- collect commits --------------------------------------------------------

latest_tag=""
if latest_tag="$(git -C "$REPO_PATH" describe --tags --abbrev=0 2>/dev/null)"; then
  :
else
  latest_tag=""
fi

if [[ -n "$latest_tag" ]]; then
  rev_range="${latest_tag}..HEAD"
  scope_note="Changes since git tag \`${latest_tag}\`."
else
  rev_range="HEAD"
  scope_note="No git tags found; including all commits on the current branch."
fi

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS='|' read -r hash subject; do
  [[ -z "$hash" ]] && continue
  category="$(categorize_subject "$subject")"
  line="$(format_bullet "$hash" "$subject")"
  append_line "$category" "$line"
done < <(git -C "$REPO_PATH" log "$rev_range" --pretty=format:'%H|%s%n' --reverse 2>/dev/null || true)

generated_at="$(date -u +'%Y-%m-%d %H:%M:%S UTC')"
repo_name="$(basename "$REPO_PATH")"

tmp_file="${OUTPUT}.tmp"
: > "$tmp_file"

{
  printf '# %s\n\n' "$TITLE"
  printf 'Generated for **%s** on %s.\n\n' "$repo_name" "$generated_at"
  printf '%s\n\n' "$scope_note"
  printf '## [Unreleased]\n\n'

  if [[ -n "$ADDED" ]]; then
    printf '### Added\n\n%s\n' "$ADDED"
  fi
  if [[ -n "$FIXED" ]]; then
    printf '### Fixed\n\n%s\n' "$FIXED"
  fi
  if [[ -n "$CHANGED" ]]; then
    printf '### Changed\n\n%s\n' "$CHANGED"
  fi
  if [[ -n "$REMOVED" ]]; then
    printf '### Removed\n\n%s\n' "$REMOVED"
  fi

  if [[ -z "$ADDED$FIXED$CHANGED$REMOVED" ]]; then
    printf '_No commits in range._\n'
  fi
} >> "$tmp_file"

if [[ "$STDOUT" -eq 1 ]]; then
  cat "$tmp_file"
  rm -f "$tmp_file"
else
  mv "$tmp_file" "$OUTPUT"
  echo "Wrote $OUTPUT"
fi
