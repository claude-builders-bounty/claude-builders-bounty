#!/usr/bin/env bash
# generate-changelog.sh
# Generate a structured CHANGELOG.md from git history.
# Usage: bash changelog.sh [--since <ref>] [--version <ver>] [--output <path>]
#                        [--keep-unreleased] [--allow-dirty] [--help]
#
# Categorizes commits into Added / Fixed / Changed / Removed using conventional
# commit prefixes, with a heuristic fallback for non-conventional messages.
# Writes (or prepends) a Keep-a-Changelog 1.1.0 section to CHANGELOG.md.
#
# Requires: git, awk, sort. No external dependencies.

set -euo pipefail

PROG="${0##*/}"
OUTPUT="CHANGELOG.md"
SINCE=""
VERSION=""
KEEP_UNRELEASED=0
ALLOW_DIRTY=0
LATEST_TAG=""

usage() {
  cat <<EOF
$PROG — generate CHANGELOG.md from git history

Usage: $PROG [options]

Options:
  --since <ref>       Commit range start (tag, branch, sha, or date).
  --version <ver>     Version string for the new section header (default: inferred).
  --output <path>     Output file (default: CHANGELOG.md).
  --keep-unreleased   Do not consume existing [Unreleased] block.
  --allow-dirty       Bypass the clean-working-tree safety check.
  -h, --help          Show this help and exit.

Examples:
  $PROG
  $PROG --since v1.0.0
  $PROG --version 2.0.0 --output CHANGELOG.md
  $PROG --keep-unreleased --allow-dirty
EOF
}

# ---- arg parsing ----
while [[ $# -gt 0 ]]; do
  case "$1" in
    --since) SINCE="${2:-}"; shift 2 ;;
    --version) VERSION="${2:-}"; shift 2 ;;
    --output) OUTPUT="${2:-}"; shift 2 ;;
    --keep-unreleased) KEEP_UNRELEASED=1; shift ;;
    --allow-dirty) ALLOW_DIRTY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "$PROG: unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

# ---- safety: clean working tree ----
if [[ $ALLOW_DIRTY -eq 0 ]]; then
  dirty="$(git status --porcelain 2>/dev/null || true)"
  if [[ -n "$dirty" ]]; then
    echo "$PROG: working tree is dirty. Commit/stash first, or pass --allow-dirty." >&2
    exit 3
  fi
fi

# ---- detect range ----
if [[ -z "$SINCE" ]]; then
  if LATEST_TAG="$(git describe --tags --abbrev=0 2>/dev/null)"; then
    SINCE="$LATEST_TAG"
  else
    SINCE=""
  fi
fi

if [[ -n "$SINCE" ]]; then
  RANGE="$SINCE..HEAD"
else
  RANGE="HEAD"
fi

# Collect commits: sha<TAB>author<TAB>email<TAB>iso-date<TAB>subject
mapfile -t COMMITS < <(git log "$RANGE" --no-merges --pretty=format:'%H%x09%an%x09%ae%x09%aI%x09%s' 2>/dev/null || true)

if [[ ${#COMMITS[@]} -eq 0 ]]; then
  if [[ -n "$SINCE" ]]; then
    echo "$PROG: no new commits since $SINCE."
  else
    echo "$PROG: no commits found."
  fi
  exit 0
fi

# ---- detect version ----
if [[ -z "$VERSION" ]]; then
  if [[ -n "$LATEST_TAG" ]]; then
    base="${LATEST_TAG#v}"
    if [[ "$base" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
      major="${BASH_REMATCH[1]}"
      minor="${BASH_REMATCH[2]}"
      patch="${BASH_REMATCH[3]}"
      VERSION="$major.$minor.$((patch + 1))"
    else
      VERSION="Unreleased"
    fi
  else
    VERSION="Unreleased"
  fi
fi

# Latest commit date in range
LATEST_DATE="$(git log "$RANGE" --no-merges --pretty=format:'%aI' | head -n1 | cut -c1-10)"

# ---- categorize ----
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()
declare -a BREAKING=()

classify() {
  local subject="$1"
  local s
  s="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  local bucket="changed"
  local breaking=0

  # Conventional commit: type(optional-scope)!?: ...
  # Extract leading token up to first ':' or whitespace
  local head rest
  if [[ "$subject" == *:* ]]; then
    head="${subject%%:*}"
    rest="${subject#*:}"
  else
    head=""
    rest="$subject"
  fi

  # Strip leading "Merge" / "Revert" markers
  if [[ "$head" =~ ^([Mm]erge|[Rr]evert) ]]; then
    echo "changed 0"
    return
  fi

  # Detect ! in conventional type token (e.g. "feat(api)!")
  if [[ "$head" == *"!"* ]]; then
    breaking=1
    head="${head%!}"
  fi

  # Strip (scope) if present
  local type="${head%%(*}"
  if [[ "$head" == *"("*")"* ]]; then
    type="${head%%(*}"
    type="${type// /}"
  fi
  type="$(printf '%s' "$type" | tr '[:upper:]' '[:lower:]')"

  case "$type" in
    feat|feature|add|new)     bucket="added"   ;;
    fix|bug|patch|hotfix)     bucket="fixed"   ;;
    refactor|perf|style|docs|chore|build|ci|test) bucket="changed" ;;
    remove|drop|deprecate|delete) bucket="removed" ;;
    "")
      # Heuristic fallback on rest
      if [[ "$s" =~ (^|[^a-z])(add|added|adds|adding)([^a-z]|$) ]]; then bucket="added"
      elif [[ "$s" =~ (^|[^a-z])(fix|fixed|fixes|fixing)([^a-z]|$) ]]; then bucket="fixed"
      elif [[ "$s" =~ (^|[^a-z])(remove|removed|removes|removing|drop|dropped|drops|deprecate)([^a-z]|$) ]]; then bucket="removed"
      fi
      ;;
    *)
      bucket="changed"
      ;;
  esac

  # BREAKING CHANGE marker in rest
  if [[ "$rest" == *"BREAKING CHANGE"* ]] || [[ "$rest" == *"BREAKING-CHANGE"* ]] || [[ "$s" == *"breaking change"* ]]; then
    breaking=1
  fi

  echo "$bucket $breaking"
}

for line in "${COMMITS[@]}"; do
  IFS=$'\t' read -r sha author email date subject <<<"$line"
  short="${sha:0:7}"

  result="$(classify "$subject")"
  bucket="${result%% *}"
  breaking="${result##* }"

  entry="- $subject ($short)"
  case "$bucket" in
    added)   ADDED+=("$entry") ;;
    fixed)   FIXED+=("$entry") ;;
    changed) CHANGED+=("$entry") ;;
    removed) REMOVED+=("$entry") ;;
  esac
  if [[ "$breaking" == "1" ]]; then
    BREAKING+=("$entry")
  fi
done

# ---- build section ----
SECTION="## [$VERSION] - $LATEST_DATE

"
if [[ ${#BREAKING[@]} -gt 0 ]]; then
  SECTION+="### ⚠️ BREAKING CHANGES
$(printf '%s\n' "${BREAKING[@]}" | sort -u)

"
fi

if [[ ${#ADDED[@]}   -gt 0 ]]; then
  SECTION+="### Added
$(printf '%s\n' "${ADDED[@]}" | sort -u)

"
fi
if [[ ${#FIXED[@]}   -gt 0 ]]; then
  SECTION+="### Fixed
$(printf '%s\n' "${FIXED[@]}" | sort -u)

"
fi
if [[ ${#CHANGED[@]} -gt 0 ]]; then
  SECTION+="### Changed
$(printf '%s\n' "${CHANGED[@]}" | sort -u)

"
fi
if [[ ${#REMOVED[@]} -gt 0 ]]; then
  SECTION+="### Removed
$(printf '%s\n' "${REMOVED[@]}" | sort -u)

"
fi

# ---- write output ----
HEADER='# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

'

if [[ -f "$OUTPUT" ]]; then
  if grep -q "^## \[$VERSION\]" "$OUTPUT"; then
    echo "$PROG: section for $VERSION already exists; not modifying $OUTPUT." >&2
    exit 0
  fi
  tmp="$(mktemp)"
  # Find the line after the header (first blank line after non-blank header line).
  awk -v section="$SECTION" '
    BEGIN { printed = 0 }
    {
      print
      if (printed == 0 && /^# Changelog/) {
        # Print the standard header lines that follow, then the section.
        print ""
        print "All notable changes to this project will be documented in this file."
        print ""
        print "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),"
        print "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)."
        print ""
        printf "%s", section
        printed = 1
        in_header = 1
        next
      }
    }
  ' "$OUTPUT" > "$tmp"
  # If we did not insert (file has no standard header), prepend.
  if ! grep -q "^## \[$VERSION\]" "$tmp"; then
    { printf '%s%s' "$HEADER" "$SECTION"; cat "$OUTPUT"; } > "${tmp}.2"
    mv "${tmp}.2" "$tmp"
  fi
  # Skip remaining lines of original (the awk above already printed everything).
  mv "$tmp" "$OUTPUT"
else
  printf '%s%s' "$HEADER" "$SECTION" > "$OUTPUT"
fi

# ---- summary ----
echo "$PROG: wrote $OUTPUT (version $VERSION, ${#COMMITS[@]} commits)"
echo "  Added:    ${#ADDED[@]}"
echo "  Fixed:    ${#FIXED[@]}"
echo "  Changed:  ${#CHANGED[@]}"
echo "  Removed:  ${#REMOVED[@]}"
echo "  Breaking: ${#BREAKING[@]}"
