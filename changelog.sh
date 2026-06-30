#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [output-file] [--no-tag]
# Default output: CHANGELOG.md in current directory

set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"
NO_TAG=false

# Parse arguments
for arg in "$@"; do
  case $arg in
    --no-tag) NO_TAG=true ;;
  esac
done

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

# Check if we're in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "Error: Not a git repository. Run 'git init' first." >&2
  exit 1
fi

# Check if there are any commits
if ! git log --oneline -1 > /dev/null 2>&1; then
  echo "Error: No commits found in repository." >&2
  exit 1
fi

# Auto-categorize commit messages
categorize() {
  local msg="$1"
  if echo "$msg" | grep -qiE "^(feat|add|new|implement|introduce|create)"; then
    echo "Added"
  elif echo "$msg" | grep -qiE "^(fix|bug|hotfix|resolve|patch|correct)"; then
    echo "Fixed"
  elif echo "$msg" | grep -qiE "^(remove|delete|drop|deprecate)"; then
    echo "Removed"
  elif echo "$msg" | grep -qiE "^(security|vulnerability|cve)"; then
    echo "Security"
  elif echo "$msg" | grep -qiE "^(perf|performance|speed|fast|optimi[sz]e)"; then
    echo "Performance"
  elif echo "$msg" | grep -qiE "^(docs|doc|readme|document)"; then
    echo "Documentation"
  elif echo "$msg" | grep -qiE "^(test|spec|testing|coverage)"; then
    echo "Tests"
  elif echo "$msg" | grep -qiE "^(chore|ci|cd|build|deps|dependencies|refactor|style|cleanup)"; then
    echo "Maintenance"
  else
    echo "Changed"
  fi
}

# Generate the changelog
{
echo "# Changelog"
echo ""
echo "All notable changes to this project will be documented in this file."
echo ""
echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),"
echo "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)."
echo ""
} > "$OUTPUT_FILE"

# Get all tags sorted by version
TAGS=$(git tag --sort=-version:refname 2>/dev/null || git tag --sort=-creatordate 2>/dev/null || "")

if [ -z "$TAGS" ] || [ "$NO_TAG" = true ]; then
  # No tags — output all commits
  echo "## Unreleased" >> "$OUTPUT_FILE"
  echo "" >> "$OUTPUT_FILE"
  
  CURRENT=""
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    HASH=$(echo "$line" | awk '{print $1}')
    MSG=$(echo "$line" | awk '{$1=""; print $0}' | sed 's/^ //')
    CATEGORY=$(categorize "$MSG")
    
    if [ "$CATEGORY" != "$CURRENT" ]; then
      if [ -n "$CURRENT" ]; then echo "" >> "$OUTPUT_FILE"; fi
      echo "### $CATEGORY" >> "$OUTPUT_FILE"
      echo "" >> "$OUTPUT_FILE"
      CURRENT="$CATEGORY"
    fi
    
    echo "- ${MSG} (${HASH})" >> "$OUTPUT_FILE"
  done < <(git log --pretty=format:"%h %s" --reverse)
  echo "" >> "$OUTPUT_FILE"
else
  # Generate changelog between tags
  PREV_TAG=""
  FIRST_TAG=""
  
  for TAG in $TAGS; do
    if [ -z "$FIRST_TAG" ]; then
      FIRST_TAG="$TAG"
      continue
    fi
    
    if [ -n "$PREV_TAG" ]; then
      echo "" >> "$OUTPUT_FILE"
      echo "## [$PREV_TAG] → [$TAG]" >> "$OUTPUT_FILE"
      echo "" >> "$OUTPUT_FILE"
    else
      echo "" >> "$OUTPUT_FILE"
      echo "## [$TAG]" >> "$OUTPUT_FILE"
      echo "" >> "$OUTPUT_FILE"
    fi
    
    CURRENT=""
    while IFS= read -r line; do
      [ -z "$line" ] && continue
      HASH=$(echo "$line" | awk '{print $1}')
      MSG=$(echo "$line" | awk '{$1=""; print $0}' | sed 's/^ //')
      CATEGORY=$(categorize "$MSG")
      
      if [ "$CATEGORY" != "$CURRENT" ]; then
        if [ -n "$CURRENT" ]; then echo "" >> "$OUTPUT_FILE"; fi
        echo "### $CATEGORY" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        CURRENT="$CATEGORY"
      fi
      
      echo "- ${MSG} (${HASH})" >> "$OUTPUT_FILE"
    done < <(git log --pretty=format:"%h %s" "$PREV_TAG..$TAG" 2>/dev/null || git log --pretty=format:"%h %s" -20)
    
    PREV_TAG="$TAG"
  done
  
  # Add unreleased section for commits after the last tag
  if [ -n "$FIRST_TAG" ]; then
    UNRELEASED=$(git log --pretty=format:"%h %s" "$FIRST_TAG..HEAD" 2>/dev/null || "")
    if [ -n "$UNRELEASED" ]; then
      echo "" >> "$OUTPUT_FILE"
      echo "## [Unreleased]" >> "$OUTPUT_FILE"
      echo "" >> "$OUTPUT_FILE"
      
      CURRENT=""
      while IFS= read -r line; do
        [ -z "$line" ] && continue
        HASH=$(echo "$line" | awk '{print $1}')
        MSG=$(echo "$line" | awk '{$1=""; print $0}' | sed 's/^ //')
        CATEGORY=$(categorize "$MSG")
        
        if [ "$CATEGORY" != "$CURRENT" ]; then
          if [ -n "$CURRENT" ]; then echo "" >> "$OUTPUT_FILE"; fi
          echo "### $CATEGORY" >> "$OUTPUT_FILE"
          echo "" >> "$OUTPUT_FILE"
          CURRENT="$CATEGORY"
        fi
        
        echo "- ${MSG} (${HASH})" >> "$OUTPUT_FILE"
      done <<< "$UNRELEASED"
    fi
  fi
fi

echo "" >> "$OUTPUT_FILE"
echo "---" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "Generated on $(date -u '+%Y-%m-%d %H:%M:%S UTC') using [changelog.sh](changelog.sh)" >> "$OUTPUT_FILE"

echo "✅ CHANGELOG generated: $OUTPUT_FILE"
