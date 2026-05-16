#!/usr/bin/env bash
set -euo pipefail

# changelog.sh — Generate structured CHANGELOG from git history
# Usage: bash changelog.sh [--repo PATH] [--output FILE] [--since TAG]

REPO_PATH="."
OUTPUT_FILE="CHANGELOG.md"
SINCE_TAG=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --repo)
      REPO_PATH="$2"
      shift 2
      ;;
    --output)
      OUTPUT_FILE="$2"
      shift 2
      ;;
    --since)
      SINCE_TAG="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: bash changelog.sh [--repo PATH] [--output FILE] [--since TAG]"
      exit 1
      ;;
  esac
done

cd "$REPO_PATH"

# Get last tag if not specified
if [[ -z "$SINCE_TAG" ]]; then
  SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

# Get commit range
if [[ -n "$SINCE_TAG" ]]; then
  COMMIT_RANGE="${SINCE_TAG}..HEAD"
  echo "Generating changelog since tag: $SINCE_TAG"
else
  COMMIT_RANGE="HEAD"
  echo "No tags found. Generating changelog from all commits."
fi

# Get current date
CURRENT_DATE=$(date +%Y-%m-%d)

# Initialize changelog
cat > "$OUTPUT_FILE" << EOF
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - $CURRENT_DATE

EOF

# Categorize commits
declare -A categories
categories=(
  ["Added"]=""
  ["Fixed"]=""
  ["Changed"]=""
  ["Removed"]=""
  ["Security"]=""
  ["Deprecated"]=""
  ["Documentation"]=""
)

# Parse commits
while IFS= read -r commit; do
  # Extract commit message (first line only)
  msg=$(echo "$commit" | sed 's/^[a-f0-9]* //')
  
  # Categorize based on conventional commit prefix
  if [[ "$msg" =~ ^feat(\(.*\))?:\ (.+) ]]; then
    categories["Added"]+="- ${BASH_REMATCH[2]}\n"
  elif [[ "$msg" =~ ^fix(\(.*\))?:\ (.+) ]]; then
    categories["Fixed"]+="- ${BASH_REMATCH[2]}\n"
  elif [[ "$msg" =~ ^refactor(\(.*\))?:\ (.+) ]]; then
    categories["Changed"]+="- ${BASH_REMATCH[2]}\n"
  elif [[ "$msg" =~ ^perf(\(.*\))?:\ (.+) ]]; then
    categories["Changed"]+="- ${BASH_REMATCH[2]}\n"
  elif [[ "$msg" =~ ^remove(\(.*\))?:\ (.+) ]]; then
    categories["Removed"]+="- ${BASH_REMATCH[2]}\n"
  elif [[ "$msg" =~ ^security(\(.*\))?:\ (.+) ]]; then
    categories["Security"]+="- ${BASH_REMATCH[2]}\n"
  elif [[ "$msg" =~ ^docs(\(.*\))?:\ (.+) ]]; then
    categories["Documentation"]+="- ${BASH_REMATCH[2]}\n"
  elif [[ "$msg" =~ ^deprecate(\(.*\))?:\ (.+) ]]; then
    categories["Deprecated"]+="- ${BASH_REMATCH[2]}\n"
  else
    # Fallback: try to guess from keywords
    if [[ "$msg" =~ [Aa]dd|[Nn]ew|[Ii]mplement ]]; then
      categories["Added"]+="- $msg\n"
    elif [[ "$msg" =~ [Ff]ix|[Bb]ug|[Rr]esolve ]]; then
      categories["Fixed"]+="- $msg\n"
    elif [[ "$msg" =~ [Rr]emove|[Dd]elete ]]; then
      categories["Removed"]+="- $msg\n"
    elif [[ "$msg" =~ [Uu]pdate|[Cc]hange|[Mm]odify ]]; then
      categories["Changed"]+="- $msg\n"
    fi
  fi
done < <(git log "$COMMIT_RANGE" --pretty=format:"%h %s" --no-merges)

# Write categories to changelog
for category in "Added" "Fixed" "Changed" "Removed" "Security" "Deprecated" "Documentation"; do
  if [[ -n "${categories[$category]}" ]]; then
    echo "### $category" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo -e "${categories[$category]}" >> "$OUTPUT_FILE"
  fi
done

echo "✓ Changelog generated: $OUTPUT_FILE"
echo ""
echo "Preview:"
head -30 "$OUTPUT_FILE"
