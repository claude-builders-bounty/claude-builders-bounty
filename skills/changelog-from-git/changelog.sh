#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history since the
# last tag. Auto-categorizes commits into Added / Fixed / Changed / Removed
# using conventional-commit prefixes.
#
# Usage:
#   bash changelog.sh                  # uses [Unreleased] as version
#   bash changelog.sh 1.4.0            # uses [1.4.0] as version
#   bash changelog.sh --stdout         # print to stdout instead of writing
#
# Submission for claude-builders-bounty/claude-builders-bounty issue #1.

set -euo pipefail

VERSION=""
TO_STDOUT=0
for arg in "$@"; do
  case "$arg" in
    --stdout) TO_STDOUT=1 ;;
    -h|--help)
      sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) VERSION="$arg" ;;
  esac
done

# 1. Range
if last_tag=$(git describe --tags --abbrev=0 2>/dev/null); then
  range="${last_tag}..HEAD"
else
  last_tag=""
  range="HEAD"
fi

today=$(date +%Y-%m-%d)
header_version="${VERSION:-Unreleased}"

# 2. Read commits — abort cleanly if nothing in range
mapfile -t commits < <(git log "$range" --no-merges --pretty=format:"%h%x09%s")
if [ ${#commits[@]} -eq 0 ]; then
  if [ -n "$last_tag" ]; then
    echo "No commits since tag '${last_tag}'. Nothing to write." >&2
  else
    echo "No commits in repository." >&2
  fi
  exit 0
fi

# 3. Categorize
added=()
fixed=()
changed=()
removed=()

categorize() {
  local subject="$1"
  local sha="$2"
  local breaking=0
  # Detect bang form: feat!: or fix(scope)!:
  if printf '%s' "$subject" | grep -qE '^[A-Za-z]+(\([^)]+\))?!:'; then
    breaking=1
  fi
  # Extract the leading alphabetic prefix (everything before scope or colon).
  local prefix
  prefix=$(printf '%s' "$subject" | grep -oE '^[A-Za-z]+' | tr '[:upper:]' '[:lower:]')
  if [ -z "$prefix" ]; then
    prefix="_unknown_"
  fi

  local entry="${subject} (\`${sha}\`)"
  if [ "$breaking" -eq 1 ]; then
    entry="**BREAKING:** ${entry}"
  fi

  case "$prefix" in
    feat|feature)               added+=("$entry") ;;
    fix|bugfix|hotfix)          fixed+=("$entry") ;;
    perf|refactor|style|docs|ci|build|chore|test) changed+=("$entry") ;;
    revert|remove|delete|deprecate) removed+=("$entry") ;;
    *)
      # No recognizable prefix → Changed.
      changed+=("$entry")
      ;;
  esac
}

for line in "${commits[@]}"; do
  sha="${line%%$'\t'*}"
  subject="${line#*$'\t'}"
  categorize "$subject" "$sha"
done

# 4. Render
render() {
  printf '## [%s] — %s\n\n' "$header_version" "$today"
  if [ ${#added[@]} -gt 0 ]; then
    printf '### Added\n'
    for e in "${added[@]}"; do printf -- '- %s\n' "$e"; done
    printf '\n'
  fi
  if [ ${#fixed[@]} -gt 0 ]; then
    printf '### Fixed\n'
    for e in "${fixed[@]}"; do printf -- '- %s\n' "$e"; done
    printf '\n'
  fi
  if [ ${#changed[@]} -gt 0 ]; then
    printf '### Changed\n'
    for e in "${changed[@]}"; do printf -- '- %s\n' "$e"; done
    printf '\n'
  fi
  if [ ${#removed[@]} -gt 0 ]; then
    printf '### Removed\n'
    for e in "${removed[@]}"; do printf -- '- %s\n' "$e"; done
    printf '\n'
  fi
}

new_section=$(render)

# 5. Counts to stderr so users see what happened
printf 'Range: %s\nAdded: %d | Fixed: %d | Changed: %d | Removed: %d\n' \
  "$range" "${#added[@]}" "${#fixed[@]}" "${#changed[@]}" "${#removed[@]}" >&2

# 6. Output
if [ "$TO_STDOUT" -eq 1 ]; then
  printf '%s\n' "$new_section"
  exit 0
fi

CHANGELOG_FILE="CHANGELOG.md"
if [ -f "$CHANGELOG_FILE" ]; then
  # Prepend new section above existing content, preserving the file header.
  existing=$(cat "$CHANGELOG_FILE")
  # Detect a leading "# Changelog" block; if present, insert after it.
  if printf '%s' "$existing" | head -n 1 | grep -q '^# Changelog'; then
    head_block=$(printf '%s' "$existing" | awk 'NR==1{print; flag=1; next} flag && /^## /{flag=0} flag{print}')
    rest=$(printf '%s' "$existing" | awk 'started{print} /^## /{started=1; print}')
    {
      printf '%s\n\n' "$head_block"
      printf '%s\n' "$new_section"
      printf '%s\n' "$rest"
    } > "$CHANGELOG_FILE"
  else
    {
      printf '%s\n' "$new_section"
      printf '%s\n' "$existing"
    } > "$CHANGELOG_FILE"
  fi
else
  cat > "$CHANGELOG_FILE" <<'HEADER'
# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/) and this
project adheres to [Semantic Versioning](https://semver.org/).

HEADER
  printf '%s\n' "$new_section" >> "$CHANGELOG_FILE"
fi

printf 'Wrote %s\n' "$CHANGELOG_FILE" >&2
