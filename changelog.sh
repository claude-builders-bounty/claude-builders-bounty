#!/usr/bin/env bash
# changelog.sh — generate a structured CHANGELOG.md from git history.
# Collects commits from the last git tag (or from the start of history if there
# are no tags), categorizes them by Conventional Commits, and writes a
# Keep a Changelog format file.
#
# Usage:
#   bash changelog.sh                # write CHANGELOG.md
#   bash changelog.sh --stdout       # print to stdout (don't write a file)
#   bash changelog.sh --since v1.2.3 # only commits after a specific tag
#   bash changelog.sh --help

set -euo pipefail

# ---------- Configuration ----------
# Commit keyword -> section heading
declare -A CATEGORY_TITLES=(
  [Added]="Added"
  [Fixed]="Fixed"
  [Changed]="Changed"
  [Removed]="Removed"
  [Security]="Security"
  [Deprecated]="Deprecated"
)
# Conventional Commit type -> category (keys are the lowercase type prefix)
declare -A TYPE_MAP=(
  [feat]=Added
  [feature]=Added
  [fix]=Fixed
  [bugfix]=Fixed
  [hotfix]=Fixed
  [refactor]=Changed
  [perf]=Changed
  [performance]=Changed
  [style]=Changed
  [chore]=Changed
  [build]=Changed
  [ci]=Changed
  [docs]=Changed
  [test]=Changed
  [tests]=Changed
  [revert]=Removed
  [remove]=Removed
  [delete]=Removed
  [security]=Security
  [deprecate]=Deprecated
  [deprecated]=Deprecated
)

# ---------- Helpers ----------
print_help() {
  cat <<'EOF'
changelog.sh — generate a structured CHANGELOG.md from git history

Setup (3 steps):
  1. Copy changelog.sh (and SKILL.md if you use Claude Code) into your project root.
  2. chmod +x changelog.sh
  3. bash changelog.sh   # CHANGELOG.md is created in the current directory

Usage:
  bash changelog.sh                 Generate CHANGELOG.md in the current directory
  bash changelog.sh --stdout        Print the result to stdout (don't touch the file)
  bash changelog.sh --since <tag>   Only commits after the given tag
  bash changelog.sh --help          Show this help

How it works:
  1. Finds the last git tag (git describe --tags --abbrev=0).
     If there are no tags, it uses the whole history.
  2. Collects commits from that tag to HEAD.
  3. Categorizes by Conventional Commits
     (feat:, fix:, refactor:, docs:, test:, chore:, perf:, style:, build:, ci:, security:, revert:).
     Commits without a type prefix go to "Changed".
  4. Builds a Keep a Changelog format CHANGELOG.md:
     - Added / Fixed / Changed / Removed / Security / Deprecated sections
     - a tag-comparison link (if a tag was found)

Examples:
  bash changelog.sh
  bash changelog.sh --stdout --since v1.0.0
EOF
}

# ---------- Parse arguments ----------
OUTPUT_FILE="CHANGELOG.md"
TO_STDOUT=0
SINCE_ARG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --stdout) TO_STDOUT=1 ;;
    --since)
      shift
      SINCE_ARG="${1:-}"
      ;;
    --help|-h)
      print_help
      exit 0
      ;;
    *)
      echo "Unknown argument: $1 (see: bash changelog.sh --help)" >&2
      exit 1
      ;;
  esac
  shift
done

# ---------- Determine the commit range ----------
LAST_TAG=""
RANGE=""

if [[ -n "$SINCE_ARG" ]]; then
  LAST_TAG="$SINCE_ARG"
  RANGE="${LAST_TAG}..HEAD"
elif git describe --tags --abbrev=0 >/dev/null 2>&1; then
  LAST_TAG="$(git describe --tags --abbrev=0)"
  RANGE="${LAST_TAG}..HEAD"
else
  # No tags — use the whole history
  RANGE="HEAD"
fi

# ---------- Collect commits ----------
# Each line: <type>|<subject>
COMMITS=""
if [[ "$RANGE" == "HEAD" ]]; then
  COMMITS="$(git log --pretty=format:'%s' HEAD)"
else
  COMMITS="$(git log --pretty=format:'%s' "$RANGE")"
fi

if [[ -z "$COMMITS" ]]; then
  echo "No commits in range${RANGE:+ ($RANGE)}. Nothing to write." >&2
  exit 0
fi

# ---------- Categorize ----------
# Array of "Category|subject"
declare -a ENTRIES=()

while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  # Skip merge-commits and squash headers
  if [[ "$line" =~ ^(Merge|Revert) ]]; then
    continue
  fi
  # Parse Conventional Commit: "feat(scope): message"
  # Split manually — no regex (compatibility across bash versions)
  prefix="${line%%:*}"
  if [[ "$prefix" != "$line" ]]; then
    # has a colon — it is a conventional commit
    type="${prefix,,}"
    subject="${line#*:}"
    subject="${subject#"${subject%%[![:space:]]*}"}"  # trim leading whitespace
    # extract scope: "feat(api)" -> type=feat, scope=api
    scope=""
    if [[ "$type" == *"("* ]]; then
      scope="${type#*(}"
      scope="${scope%)*}"
      type="${type%%(*}"
    fi
    # Capitalize the first letter of the subject
    subject="$(echo "${subject:0:1}" | tr '[:lower:]' '[:upper:]')${subject:1}"
    cat_key="${TYPE_MAP[$type]:-Changed}"
    if [[ -n "$scope" ]]; then
      subject="${subject} (${scope})"
    fi
  else
    # Plain commit without a type prefix — try to guess from the verb
    subject="${line}"
    subject="$(echo "${subject:0:1}" | tr '[:lower:]' '[:upper:]')${subject:1}"
    lower_line="${line,,}"
    if [[ "$lower_line" =~ ^(fix|fixed|repair|resolve|solves?|correct|hotfix) ]]; then
      cat_key="Fixed"
    elif [[ "$lower_line" =~ ^(add|added|implement|introduce|support|new|create|feature) ]]; then
      cat_key="Added"
    elif [[ "$lower_line" =~ ^(remov|delet|drop|deprecat) ]]; then
      cat_key="Removed"
    else
      cat_key="Changed"
    fi
  fi
  ENTRIES+=("${cat_key}|${subject}")
done <<< "$COMMITS"

# ---------- Build the Markdown ----------
DATE="$(date +%Y-%m-%d)"
VERSION_HEADER="Unreleased"
if [[ -n "$LAST_TAG" ]]; then
  # Try to guess the next version: tag like v1.2.3 -> v1.2.4
  if [[ "$LAST_TAG" =~ ^v?([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
    VERSION_HEADER="v${BASH_REMATCH[1]}.${BASH_REMATCH[2]}.$((BASH_REMATCH[3] + 1))"
  else
    VERSION_HEADER="${LAST_TAG}"
  fi
fi

# Build sections in a fixed order
ORDER=(Added Fixed Changed Removed Security Deprecated)
OUT=""
OUT+="# Changelog\n\n"
OUT+="## [${VERSION_HEADER}] - ${DATE}\n\n"

SECTION_OPENED=0
for cat in "${ORDER[@]}"; do
  # Collect entries of this category in order of appearance
  items=()
  for entry in "${ENTRIES[@]}"; do
    if [[ "${entry%%|*}" == "$cat" ]]; then
      items+=("${entry#*|}")
    fi
  done
  if [[ ${#items[@]} -gt 0 ]]; then
    OUT+="### ${CATEGORY_TITLES[$cat]}\n\n"
    for item in "${items[@]}"; do
      OUT+="- ${item}\n"
    done
    OUT+="\n"
    SECTION_OPENED=1
  fi
done

if [[ $SECTION_OPENED -eq 0 ]]; then
  OUT+="_No changes in this range._\n"
fi

# Tag comparison link (if there is a previous tag)
if [[ -n "$LAST_TAG" && "$LAST_TAG" != "$SINCE_ARG" ]]; then
  REMOTE_URL="$(git config --get remote.origin.url 2>/dev/null || true)"
  if [[ -n "$REMOTE_URL" && "$REMOTE_URL" =~ github\.com[:/]([^/]+)/([^/]+)(\.git)?$ ]]; then
    REPO_OWNER="${BASH_REMATCH[1]}"
    REPO_NAME="${BASH_REMATCH[2]%.git}"
    OUT+="[Compare ${LAST_TAG}](https://github.com/${REPO_OWNER}/${REPO_NAME}/compare/${LAST_TAG}...HEAD)\n"
  fi
fi

# ---------- Output ----------
if [[ $TO_STDOUT -eq 1 ]]; then
  printf "%b" "$OUT"
else
  printf "%b" "$OUT" > "$OUTPUT_FILE"
  echo "Done: ${OUTPUT_FILE} (${#ENTRIES[@]} commits, range: ${RANGE})"
fi
