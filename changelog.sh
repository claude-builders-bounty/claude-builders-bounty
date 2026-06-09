#!/usr/bin/env bash
#
# changelog.sh — Generate a structured CHANGELOG.md from git history.
#
# Usage:
#   bash changelog.sh              # writes CHANGELOG.md
#   bash changelog.sh --stdout     # prints to stdout
#   bash changelog.sh --tag v1.0   # changes since a specific tag
#

set -euo pipefail

OUTPUT_FILE="CHANGELOG.md"
STDOUT_MODE=false
TAG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --stdout)  STDOUT_MODE=true; shift ;;
    --tag)     TAG="$2"; shift 2 ;;
    --output)  OUTPUT_FILE="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: bash changelog.sh [--stdout] [--tag TAG] [--output FILE]"
      exit 0 ;;
    *)         echo "Unknown option: $1"; exit 1 ;;
  esac
done

# Find range
if [[ -n "$TAG" ]]; then
  RANGE="${TAG}..HEAD"
  DESC="since ${TAG}"
elif LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null); then
  RANGE="${LAST_TAG}..HEAD"
  DESC="since ${LAST_TAG}"
else
  RANGE=""
  DESC="(all commits)"
fi

# Collect commits
declare -a ADDED=() FIXED=() CHANGED=() REMOVED=()

log_args=(--pretty=format:"%s")
if [[ -n "$RANGE" ]]; then
  log_args+=("$RANGE")
fi

while IFS= read -r msg; do
  [[ -z "$msg" ]] && continue
  lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

  if [[ "$lower" =~ ^(feat|feature)(\(.+\))?!?: ]]; then
    ADDED+=("$msg")
  elif [[ "$lower" =~ ^fix(\(.+\))?!?: ]]; then
    FIXED+=("$msg")
  elif [[ "$lower" =~ ^(revert|remove|delete|drop|breaking)(\(.+\))?!?: ]]; then
    REMOVED+=("$msg")
  elif [[ "$lower" =~ ^(refactor|perf|style|docs|test|build|ci|chore)(\(.+\))?!?: ]]; then
    CHANGED+=("$msg")
  else
    CHANGED+=("$msg")
  fi
done < <(git log "${log_args[@]}" 2>/dev/null)

# Render
{
  echo "# Changelog"
  echo ""
  echo "All notable changes ${DESC} will be documented in this file."
  echo ""
  echo "Format based on [Keep a Changelog](https://keepachangelog.com/) and"
  echo "[Conventional Commits](https://www.conventionalcommits.org/)."
  echo ""

  render() {
    local title="$1"; shift
    if [[ $# -gt 0 ]]; then
      echo "### ${title}"
      echo ""
      for item in "$@"; do
        echo "- ${item}"
      done
      echo ""
    fi
  }

  render "Added"    "${ADDED[@]+"${ADDED[@]}"}"
  render "Fixed"    "${FIXED[@]+"${FIXED[@]}"}"
  render "Changed"  "${CHANGED[@]+"${CHANGED[@]}"}"
  render "Removed"  "${REMOVED[@]+"${REMOVED[@]}"}"

  total=0
  [[ ${#ADDED[@]} -gt 0 ]] && total=$((total + ${#ADDED[@]}))
  [[ ${#FIXED[@]} -gt 0 ]] && total=$((total + ${#FIXED[@]}))
  [[ ${#CHANGED[@]} -gt 0 ]] && total=$((total + ${#CHANGED[@]}))
  [[ ${#REMOVED[@]} -gt 0 ]] && total=$((total + ${#REMOVED[@]}))

  if [[ $total -eq 0 ]]; then
    echo "_No changes found ${DESC}._"
    echo ""
  fi
} > /tmp/_changelog_render.txt

if $STDOUT_MODE; then
  cat /tmp/_changelog_render.txt
else
  mv /tmp/_changelog_render.txt "$OUTPUT_FILE"
  echo "✅ Changelog written to ${OUTPUT_FILE}"
fi