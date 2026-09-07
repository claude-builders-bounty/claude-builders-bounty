#!/usr/bin/env bash
# beamo-changelog — structured CHANGELOG.md from git history since the last tag
# Relates to: claude-builders-bounty#1
# Author: Beamo LLC <beamo@beamosupport.com>
set -euo pipefail

VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_FILE="${CHANGELOG_OUTPUT:-CHANGELOG.md}"
PREPEND="${CHANGELOG_PREPEND:-1}"
REPO_ROOT=""
RANGE_FROM=""
RANGE_TO="HEAD"
UNRELEASED_LABEL="Unreleased"
TODAY=""

usage() {
  cat <<'USAGE'
Usage: bash changelog.sh [options]

Generate a Keep-a-Changelog-style CHANGELOG.md from commits since the last git tag.

Options:
  -o, --output FILE     Output path (default: CHANGELOG.md)
  -r, --repo DIR        Git repository root (default: current directory)
  --from REF            Start ref (default: latest tag, or first commit)
  --to REF              End ref (default: HEAD)
  --replace             Replace entire CHANGELOG.md instead of prepending
  --stdout              Print to stdout only (do not write a file)
  -h, --help            Show this help
  -v, --version         Show version

Environment:
  CHANGELOG_OUTPUT      Same as --output
  CHANGELOG_PREPEND=0   Same as --replace
USAGE
}

die() { echo "error: $*" >&2; exit 1; }

require_git_repo() {
  if ! git -C "$REPO_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    die "not a git repository: $REPO_ROOT"
  fi
}

latest_tag() {
  git -C "$REPO_ROOT" describe --tags --abbrev=0 2>/dev/null || true
}

resolve_range() {
  if [[ -z "$RANGE_FROM" ]]; then
    local tag
    tag="$(latest_tag)"
    if [[ -n "$tag" ]]; then
      RANGE_FROM="$tag"
    else
      # No tags: use empty tree → all commits
      RANGE_FROM="$(git -C "$REPO_ROOT" rev-list --max-parents=0 HEAD | tail -1)"
      # Include the root commit itself by using ^@ trick: start before root
      RANGE_FROM="${RANGE_FROM}^"
      # If ^ fails (orphan), fall back to listing all
      if ! git -C "$REPO_ROOT" rev-parse --verify "$RANGE_FROM" >/dev/null 2>&1; then
        RANGE_FROM=""
      fi
    fi
  fi
}

# Categorize a single subject line into Added|Fixed|Changed|Removed|Other
categorize() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  # Conventional Commits type prefix (feat:, fix!, etc.)
  if [[ "$lower" =~ ^(feat|feature)(\(.*\))?\!?: ]]; then
    echo "Added"; return
  fi
  if [[ "$lower" =~ ^(fix|bugfix)(\(.*\))?\!?: ]]; then
    echo "Fixed"; return
  fi
  if [[ "$lower" =~ ^(remove|removed|rm|delete|deleted|drop)(\(.*\))?\!?: ]]; then
    echo "Removed"; return
  fi
  if [[ "$lower" =~ ^(chore|refactor|perf|style|docs|ci|build|change|changed|update|updated|improve|improved)(\(.*\))?\!?: ]]; then
    echo "Changed"; return
  fi

  # Keyword heuristics on free-form subjects
  if [[ "$lower" =~ (^|[[:space:][:punct:]])(add|adds|added|adding|introduce|introduces|introduced|new|create|creates|created|implement|implements|implemented)([[:space:][:punct:]]|$) ]]; then
    echo "Added"; return
  fi
  if [[ "$lower" =~ (^|[[:space:][:punct:]])(fix|fixes|fixed|fixing|bugfix|hotfix|patch|resolve|resolves|resolved)([[:space:][:punct:]]|$) ]]; then
    echo "Fixed"; return
  fi
  if [[ "$lower" =~ (^|[[:space:][:punct:]])(remove|removes|removed|removing|delete|deletes|deleted|deleting|drop|drops|dropped|deprecate|deprecated)([[:space:][:punct:]]|$) ]]; then
    echo "Removed"; return
  fi
  if [[ "$lower" =~ (^|[[:space:][:punct:]])(change|changes|changed|changing|update|updates|updated|updating|improve|improves|improved|refactor|refactors|refactored|rename|renames|renamed|bump|upgrade|upgrades|upgraded|migrate|migrates|migrated)([[:space:][:punct:]]|$) ]]; then
    echo "Changed"; return
  fi

  echo "Changed"
}

# Strip conventional-commit type prefix for cleaner bullets
clean_subject() {
  local subject="$1"
  # Remove type(scope)!: prefix
  subject="$(printf '%s' "$subject" | sed -E 's/^[A-Za-z]+(\([^)]*\))?\!?:[[:space:]]*//')"
  # Capitalize first letter
  if [[ -n "$subject" ]]; then
    local first rest
    first="$(printf '%s' "${subject:0:1}" | tr '[:lower:]' '[:upper:]')"
    rest="${subject:1}"
    subject="${first}${rest}"
  fi
  printf '%s' "$subject"
}

collect_commits() {
  local range_arg=()
  if [[ -n "$RANGE_FROM" ]]; then
    range_arg=("${RANGE_FROM}..${RANGE_TO}")
  else
    range_arg=("${RANGE_TO}")
  fi

  # Format: hash<TAB>subject  (subject only, no body noise)
  git -C "$REPO_ROOT" log --no-merges --pretty=format:'%h%x09%s' "${range_arg[@]}"
}

render_section() {
  local title="$1"
  shift
  local items=("$@")
  if ((${#items[@]} == 0)); then
    return
  fi
  echo "### ${title}"
  echo
  local item
  for item in "${items[@]}"; do
    echo "- ${item}"
  done
  echo
}

generate_markdown() {
  local tag_label="$1"
  local added=() fixed=() changed=() removed=()
  local line hash subject cat cleaned
  local count=0

  while IFS=$'\t' read -r hash subject || [[ -n "${hash:-}" ]]; do
    [[ -z "${hash:-}" ]] && continue
    ((count++)) || true
    cat="$(categorize "$subject")"
    cleaned="$(clean_subject "$subject")"
    case "$cat" in
      Added)   added+=("${cleaned} (\`${hash}\`)") ;;
      Fixed)   fixed+=("${cleaned} (\`${hash}\`)") ;;
      Removed) removed+=("${cleaned} (\`${hash}\`)") ;;
      *)       changed+=("${cleaned} (\`${hash}\`)") ;;
    esac
  done < <(collect_commits)

  if ((count == 0)); then
    echo "# Changelog"
    echo
    echo "No commits found in range ${RANGE_FROM:-<root>}..${RANGE_TO}."
    return 0
  fi

  local since_label
  if [[ -n "$(latest_tag)" && "$RANGE_FROM" == "$(latest_tag)" ]]; then
    since_label="since tag \`${RANGE_FROM}\`"
  elif [[ -n "$RANGE_FROM" ]]; then
    since_label="since \`${RANGE_FROM}\`"
  else
    since_label="full history"
  fi

  echo "# Changelog"
  echo
  echo "All notable changes to this project are documented in this file."
  echo
  echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)."
  echo
  echo "## [${tag_label}] - ${TODAY}"
  echo
  echo "<!-- generated by beamo-changelog v${VERSION} (${since_label}, ${count} commits) -->"
  echo

  render_section "Added" "${added[@]+"${added[@]}"}"
  render_section "Fixed" "${fixed[@]+"${fixed[@]}"}"
  render_section "Changed" "${changed[@]+"${changed[@]}"}"
  render_section "Removed" "${removed[@]+"${removed[@]}"}"
}

write_output() {
  local content="$1"
  local out_path="$2"

  if [[ "$PREPEND" == "1" && -f "$out_path" ]]; then
    local existing
    existing="$(cat "$out_path")"
    # Drop leading "# Changelog" header from new content if existing already has one
    local new_body
    new_body="$(printf '%s\n' "$content" | sed '1{/^# Changelog$/d;}' | sed '1{/^$/d;}')"
    {
      echo "# Changelog"
      echo
      printf '%s\n' "$new_body"
      echo
      # Strip existing top-level "# Changelog" to avoid duplicate titles
      printf '%s\n' "$existing" | sed '1{/^# Changelog$/d;}' | sed '1{/^$/d;}'
    } > "${out_path}.tmp"
    mv "${out_path}.tmp" "$out_path"
  else
    printf '%s\n' "$content" > "$out_path"
  fi
}

main() {
  local stdout_only=0
  REPO_ROOT="$(pwd)"
  TODAY="$(date -u +%Y-%m-%d)"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -o|--output) OUTPUT_FILE="$2"; shift 2 ;;
      -r|--repo) REPO_ROOT="$2"; shift 2 ;;
      --from) RANGE_FROM="$2"; shift 2 ;;
      --to) RANGE_TO="$2"; shift 2 ;;
      --replace) PREPEND=0; shift ;;
      --stdout) stdout_only=1; shift ;;
      -h|--help) usage; exit 0 ;;
      -v|--version) echo "beamo-changelog $VERSION"; exit 0 ;;
      *) die "unknown option: $1" ;;
    esac
  done

  REPO_ROOT="$(cd "$REPO_ROOT" && pwd)"
  require_git_repo
  resolve_range

  local md
  md="$(generate_markdown "$UNRELEASED_LABEL")"

  if ((stdout_only)); then
    printf '%s\n' "$md"
  else
    # Resolve relative output against repo root
    if [[ "$OUTPUT_FILE" != /* ]]; then
      OUTPUT_FILE="${REPO_ROOT}/${OUTPUT_FILE}"
    fi
    write_output "$md" "$OUTPUT_FILE"
    echo "Wrote ${OUTPUT_FILE}" >&2
    echo "Range: ${RANGE_FROM:-<root>}..${RANGE_TO}" >&2
  fi
}

main "$@"
