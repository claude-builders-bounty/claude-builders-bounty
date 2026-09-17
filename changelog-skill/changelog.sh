#!/bin/bash

# Generate structured CHANGELOG from git history
# Usage: bash changelog.sh [--output FILE] [--since TAG]

set -e

OUTPUT="CHANGELOG.md"
SINCE_TAG=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --output|-o)
      OUTPUT="$2"
      shift 2
      ;;
    --since|-s)
      SINCE_TAG="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Get the last tag if not specified
if [ -z "$SINCE_TAG" ]; then
  SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

# Build git log command
if [ -n "$SINCE_TAG" ]; then
  GIT_LOG="git log ${SINCE_TAG}..HEAD --pretty=format:'%h|%s|%an|%ad' --date=short"
else
  GIT_LOG="git log --pretty=format:'%h|%s|%an|%ad' --date=short -100"
fi

# Initialize arrays for categories
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()

# Process commits
while IFS='|' read -r hash subject author date; do
  # Skip empty lines
  [ -z "$hash" ] && continue
  
  # Categorize based on commit message
  subject_lower=$(echo "$subject" | tr '[:upper:]' '[:lower:]')
  
  if [[ "$subject_lower" =~ ^feat ]]; then
    ADDED+=("- $subject ($hash)")
  elif [[ "$subject_lower" =~ ^fix ]]; then
    FIXED+=("- $subject ($hash)")
  elif [[ "$subject_lower" =~ ^(refactor|perf|style|build|ci|test) ]]; then
    CHANGED+=("- $subject ($hash)")
  elif [[ "$subject_lower" =~ ^feat.*remove ]] || [[ "$subject_lower" =~ ^remove ]] || [[ "$subject_lower" =~ ^delete ]]; then
    REMOVED+=("- $subject ($hash)")
  else
    # Default to Changed if no match
    CHANGED+=("- $subject ($hash)")
  fi
done < <(eval "$GIT_LOG")

# Generate CHANGELOG
{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project will be documented in this file."
  echo ""
  echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),"
  echo "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)."
  echo ""
  echo "## [Unreleased]"
  echo ""
  
  if [ ${#ADDED[@]} -gt 0 ]; then
    echo "### Added"
    echo ""
    for item in "${ADDED[@]}"; do
      echo "$item"
    done
    echo ""
  fi
  
  if [ ${#FIXED[@]} -gt 0 ]; then
    echo "### Fixed"
    echo ""
    for item in "${FIXED[@]}"; do
      echo "$item"
    done
    echo ""
  fi
  
  if [ ${#CHANGED[@]} -gt 0 ]; then
    echo "### Changed"
    echo ""
    for item in "${CHANGED[@]}"; do
      echo "$item"
    done
    echo ""
  fi
  
  if [ ${#REMOVED[@]} -gt 0 ]; then
    echo "### Removed"
    echo ""
    for item in "${REMOVED[@]}"; do
      echo "$item"
    done
    echo ""
  fi
  
} > "$OUTPUT"

echo "✅ Changelog generated: $OUTPUT"
echo "   - Added: ${#ADDED[@]} entries"
echo "   - Fixed: ${#FIXED[@]} entries"
echo "   - Changed: ${#CHANGED[@]} entries"
echo "   - Removed: ${#REMOVED[@]} entries"
