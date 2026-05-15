#!/usr/bin/env bash
# changelog.sh — Generate structured CHANGELOG.md from git history
# Reads conventional commits (feat:, fix:, docs:, style:, refactor:, perf:, test:, chore:, build:)
#
# Usage:
#   ./changelog.sh [--since <tag|date>] [--output CHANGELOG.md]
#
# Reads conventional commit message headers and produces a formatted CHANGELOG.md.

set -euo pipefail

OUTPUT=""
SINCE=""
DRY_RUN=false
TARGET_DIR=""

usage() {
    cat <<EOF
Usage: $(basename "$0") [options] [git-directory]

Options:
  --since TAG|DATE   Only include commits since this tag or date
  --output FILE      Write CHANGELOG.md to FILE instead of stdout
  --dry-run          Print what would be generated without writing
  -h | --help        Show this help
EOF
    exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --since)  SINCE="${2:-}"; shift 2 ;;
        --output) OUTPUT="${2:-}"; shift 2 ;;
        --dry-run) DRY_RUN=true; shift ;;
        -h|--help) usage 0 ;;
        *) if [[ -z "$TARGET_DIR" ]]; then TARGET_DIR="$1"; fi; shift ;;
    esac
done

TARGET_DIR="${TARGET_DIR:-$PWD}"
cd "$TARGET_DIR"

declare -A CATEGORIES=([feat]= [fix]= [docs]= [style]= [refactor]= [perf]= [test]= [chore]= [build]=)

GIT_CMD=("git" "log" "--format=%h %s" "--no-color")
if [[ -n "$SINCE" ]]; then
    GIT_CMD+=("${SINCE}..HEAD")
fi

while read -r line; do
    [[ -z "$line" ]] && continue
    commit_hash="${line%% *}"
    msg="${line#* }"
    first_w="${msg%% *}"
    case "$first_w" in
        Revert*|Merge*|Bump*|Release*) continue ;;
    esac
    case "$msg" in
        feat:*)    cat="feat" ;;
        fix:*)     cat="fix" ;;
        docs:*)    cat="docs" ;;
        style:*)   cat="style" ;;
        refactor:*)cat="refactor" ;;
        perf:*)    cat="perf" ;;
        test:*)    cat="test" ;;
        chore:*)   cat="chore" ;;
        build:*)   cat="build" ;;
        *)         continue ;;
    esac
    CATEGORIES[$cat]+="* $msg  ($commit_hash)\n"
done < <("${GIT_CMD[@]}")

TOTAL="$(git rev-list --count HEAD 2>/dev/null || echo 0)"

output="# Changelog\n\n"
output+="All notable changes to this project will be documented in this file.\n"
output+="See [Conventional Commits](https://www.conventionalcommits.org/) for guidelines.\n\n"

for section in feat fix docs style refactor perf test chore build; do
    entries="${CATEGORIES[$section]}"
    [[ -z "$entries" ]] && continue
    output+="## ${section^}\n\n$entries\n"
done

output+="---\n\n*Generated on $TOTAL commits via changelog.sh*\n"

if [[ "$DRY_RUN" == "true" ]]; then
    printf "%b" "$output" | head -50
    exit 0
fi

if [[ -n "$OUTPUT" ]]; then
    printf "%b" "$output" > "$OUTPUT"
    echo "Changelog written to $OUTPUT"
else
    printf "%b" "$output"
fi
