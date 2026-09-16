#!/usr/bin/env bash
# Generate a structured CHANGELOG.md from git history.
#
# Usage:
#   changelog.sh [--output PATH] [-h|--help]
#
# Categorizes commits since the latest reachable tag (or full history when no
# tag exists) into Added / Fixed / Changed / Removed, following the spirit of
# https://keepachangelog.com. Only Git + Bash are required.
set -euo pipefail

SCRIPT_NAME="$(basename "$0")"

usage() {
  cat <<EOF
Usage: ${SCRIPT_NAME} [--output PATH] [-h|--help]

Generate/update CHANGELOG.md from git history since the latest tag.

Options:
  --output PATH   Write to PATH instead of <repo-root>/CHANGELOG.md
  -h, --help      Show this help text
EOF
}

OUTPUT_PATH=""

while [ $# -gt 0 ]; do
  case "$1" in
    --output)
      [ $# -ge 2 ] || { echo "Error: --output requires a path argument." >&2; exit 1; }
      OUTPUT_PATH="$2"
      shift 2
      ;;
    --output=*)
      OUTPUT_PATH="${1#--output=}"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Error: unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

# --- Step 1: validate we're inside a git work tree ------------------------
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: not inside a git repository. Run this from within a git work tree." >&2
  exit 1
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
if [ -z "$OUTPUT_PATH" ]; then
  OUTPUT_PATH="${REPO_ROOT}/CHANGELOG.md"
fi

# --- Step 2: handle a repository with no commits at all --------------------
if ! git rev-parse --verify -q HEAD >/dev/null 2>&1; then
  echo "No commits found in this repository."
  exit 0
fi

# --- Step 3: determine the commit range ------------------------------------
LATEST_TAG=""
if LATEST_TAG="$(git describe --tags --abbrev=0 2>/dev/null)"; then
  RANGE="${LATEST_TAG}..HEAD"
  echo "Latest tag: ${LATEST_TAG}. Analyzing commits in ${RANGE}."
else
  LATEST_TAG=""
  RANGE="HEAD"
  echo "No tags found. Analyzing full reachable history up to HEAD."
fi

# --- Step 4: collect commits (deterministic, no fragile parsing) -----------
# Field separator is \x1f (unit separator) — practically never appears in a
# commit subject, so no delimiter collision. Merge commits are excluded by
# default. Commit subjects are treated strictly as opaque data from here on:
# they are never eval'd, sourced, or interpolated into a shell command.
WORKDIR="$(mktemp -d "${TMPDIR:-/tmp}/changelog.XXXXXX")"
trap 'rm -rf "$WORKDIR"' EXIT

COMMITS_FILE="${WORKDIR}/commits"
ADDED_FILE="${WORKDIR}/added"
FIXED_FILE="${WORKDIR}/fixed"
CHANGED_FILE="${WORKDIR}/changed"
REMOVED_FILE="${WORKDIR}/removed"
: > "$ADDED_FILE"
: > "$FIXED_FILE"
: > "$CHANGED_FILE"
: > "$REMOVED_FILE"

git log --no-merges --pretty=format:'%H%x1f%s' "$RANGE" > "$COMMITS_FILE" || true

if [ ! -s "$COMMITS_FILE" ]; then
  if [ -n "$LATEST_TAG" ]; then
    echo "No commits found since ${LATEST_TAG}."
  else
    echo "No commits found."
  fi
  exit 0
fi

# --- Step 5: categorize each commit -----------------------------------------
# Recognized conventional-commit-style prefix: "type(scope): description" or
# "type: description" (optional trailing "!" for breaking changes). Anything
# that doesn't match this shape is kept verbatim and bucketed under Changed,
# so no commit is ever discarded for lacking conventional syntax.
classify_one() {
  subject="$1"
  category="Changed"
  desc="$subject"

  if [[ "$subject" =~ ^([A-Za-z]+)(\(([^\)]*)\))?\!?:[[:space:]]*(.*)$ ]]; then
    raw_type="${BASH_REMATCH[1]}"
    raw_desc="${BASH_REMATCH[4]}"
    type_lc="$(printf '%s' "$raw_type" | tr '[:upper:]' '[:lower:]')"

    case "$type_lc" in
      feat|feature|add|added)
        category="Added" ;;
      fix|fixed|bugfix|hotfix)
        category="Fixed" ;;
      remove|removed|delete|deleted)
        category="Removed" ;;
      refactor|perf|docs|doc|style|test|tests|build|ci|chore|change|changed|revert)
        category="Changed" ;;
      *)
        category="Changed" ;;
    esac

    if [ -n "$raw_desc" ]; then
      desc="$raw_desc"
    fi
  fi

  # Trim surrounding whitespace (data flows through stdin only; the sed
  # program itself contains no user-controlled content).
  desc="$(printf '%s' "$desc" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
  [ -n "$desc" ] || desc="$subject"

  # A commit with a genuinely empty/whitespace-only subject (e.g. made with
  # --allow-empty-message) has nothing usable to show; skip it rather than
  # ever emit a bare "- " bullet.
  [ -n "$desc" ] || return 0

  first_char="$(printf '%s' "${desc:0:1}" | tr '[:lower:]' '[:upper:]')"
  desc="${first_char}${desc:1}"

  case "$category" in
    Added)   printf -- '- %s\n' "$desc" >> "$ADDED_FILE" ;;
    Fixed)   printf -- '- %s\n' "$desc" >> "$FIXED_FILE" ;;
    Removed) printf -- '- %s\n' "$desc" >> "$REMOVED_FILE" ;;
    *)       printf -- '- %s\n' "$desc" >> "$CHANGED_FILE" ;;
  esac
}

while IFS=$'\x1f' read -r commit_hash commit_subject || [ -n "${commit_hash:-}" ]; do
  [ -n "$commit_hash" ] || continue
  classify_one "$commit_subject"
done < "$COMMITS_FILE"

# --- Step 6: build the "Unreleased" section ---------------------------------
UNRELEASED_FILE="${WORKDIR}/unreleased"
{
  echo "## Unreleased"
  echo
  for pair in "Added:$ADDED_FILE" "Fixed:$FIXED_FILE" "Changed:$CHANGED_FILE" "Removed:$REMOVED_FILE"; do
    label="${pair%%:*}"
    file="${pair#*:}"
    if [ -s "$file" ]; then
      echo "### ${label}"
      cat "$file"
      echo
    fi
  done
} > "$UNRELEASED_FILE"

# --- Step 7: merge with any existing CHANGELOG.md, preserving history -------
# Strip a prior top-level "# Changelog" title and any prior "## Unreleased"
# section (heading through the next "## " heading); everything else — every
# past release section — is preserved exactly as written, internal blank
# lines included. This keeps repeated runs idempotent instead of
# accumulating duplicate entries.
HISTORY_FILE="${WORKDIR}/history"
if [ -f "$OUTPUT_PATH" ]; then
  awk '
    $0 == "# Changelog" { next }
    /^## Unreleased/ { skip=1; next }
    /^## / && skip==1 { skip=0 }
    skip==1 { next }
    { print }
  ' "$OUTPUT_PATH" > "$HISTORY_FILE"
else
  : > "$HISTORY_FILE"
fi

# Only the freshly generated header + Unreleased section is normalized (it is
# already built with controlled single blank lines via the echo calls above,
# so no further squeezing is applied to it either). Preserved history is
# never blank-line-squeezed, so intentional formatting inside old release
# sections — including multiple consecutive blank lines — survives untouched.
FINAL_FILE="${WORKDIR}/final"
{
  echo "# Changelog"
  echo
  cat "$UNRELEASED_FILE"
  # Drop leading blank lines from preserved history so exactly one blank
  # line separates it from the generated Unreleased section above; this
  # does not touch any blank lines inside the history content itself.
  sed -e '/./,$!d' "$HISTORY_FILE"
} > "$FINAL_FILE"

# Ensure exactly one trailing newline at EOF (does not otherwise alter
# interior content or blank-line structure).
printf '%s\n' "$(cat "$FINAL_FILE")" > "$OUTPUT_PATH"

# --- Step 8: report -----------------------------------------------------
added_count="$(wc -l < "$ADDED_FILE" | tr -d '[:space:]')"
fixed_count="$(wc -l < "$FIXED_FILE" | tr -d '[:space:]')"
changed_count="$(wc -l < "$CHANGED_FILE" | tr -d '[:space:]')"
removed_count="$(wc -l < "$REMOVED_FILE" | tr -d '[:space:]')"

echo "Wrote ${OUTPUT_PATH}"
echo "  Added: ${added_count}  Fixed: ${fixed_count}  Changed: ${changed_count}  Removed: ${removed_count}"
