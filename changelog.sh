#!/usr/bin/env bash
set -euo pipefail

# Generate CHANGELOG.md from git history since the last tag.
# Usage:
#   bash changelog.sh
#   bash changelog.sh --output path/to/CHANGELOG.md

output="CHANGELOG.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)
      if [[ $# -lt 2 ]] || [[ -z "${2:-}" ]]; then
        echo "error: --output requires a value" >&2
        echo "Usage: bash changelog.sh [--output CHANGELOG.md]" >&2
        exit 2
      fi
      output="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: bash changelog.sh [--output CHANGELOG.md]"
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 2
      ;;
  esac
done

if ! command -v git >/dev/null 2>&1; then
  echo "error: git is required" >&2
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: must run inside a git repository" >&2
  exit 1
fi

last_tag=""
if last_tag="$(git describe --tags --abbrev=0 2>/dev/null)"; then
  :
else
  last_tag=""
fi

range="HEAD"
since_line="(all commits)"
if [[ -n "$last_tag" ]]; then
  range="${last_tag}..HEAD"
  since_line="since tag ${last_tag}"
fi

today="$(date +%F)"

added=()
fixed=()
changed=()
removed=()

while IFS= read -r subject; do
  [[ -z "$subject" ]] && continue
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  # Conventional commits friendly categorization.
  if [[ "$lower" =~ ^(feat|add)(\(|:|!| ) ]]; then
    added+=("$subject")
  elif [[ "$lower" =~ ^fix(\(|:|!| ) ]]; then
    fixed+=("$subject")
  elif [[ "$lower" =~ ^(remove|delete)(\(|:|!| ) ]]; then
    removed+=("$subject")
  else
    changed+=("$subject")
  fi
done < <(git log --no-merges --pretty=format:%s "$range")

{
  echo "# Changelog"
  echo
  echo "## [Unreleased] - $today"
  echo
  echo "_Generated from git history $since_line._"
  echo

  echo "### Added"
  if [[ ${#added[@]} -eq 0 ]]; then
    echo "- (none)"
  else
    for s in "${added[@]}"; do echo "- $s"; done
  fi
  echo

  echo "### Fixed"
  if [[ ${#fixed[@]} -eq 0 ]]; then
    echo "- (none)"
  else
    for s in "${fixed[@]}"; do echo "- $s"; done
  fi
  echo

  echo "### Changed"
  if [[ ${#changed[@]} -eq 0 ]]; then
    echo "- (none)"
  else
    for s in "${changed[@]}"; do echo "- $s"; done
  fi
  echo

  echo "### Removed"
  if [[ ${#removed[@]} -eq 0 ]]; then
    echo "- (none)"
  else
    for s in "${removed[@]}"; do echo "- $s"; done
  fi
  echo
} >"$output"

echo "Wrote $output ($today)."

