#!/bin/bash

# Generate a structured CHANGELOG.md from git history since last tag

# Get latest tag
latest_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

# Determine commit range
if [ -z "$latest_tag" ]; then
  range="HEAD"
else
  range="${latest_tag}..HEAD"
fi

# Initialize arrays
declare -a added fixed changed removed

# Process commits
while IFS= read -r commit; do
  subject=$(echo "$commit" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
  if [[ $subject =~ ^feat: ]]; then
    added+=("$subject")
  elif [[ $subject =~ ^fix: ]]; then
    fixed+=("$subject")
  elif [[ $subject =~ ^(perf|refactor|style|docs|test|chore): ]]; then
    changed+=("$subject")
  elif [[ $subject =~ (?i)(remove|delete|drop) ]]; then
    removed+=("$subject")
  else
    changed+=("$subject")
  fi
done < <(git log --pretty=format:"%s" "$range")

# Generate changelog content
{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project will be documented in this file."
  echo ""
  echo "## [Unreleased]"
  echo ""
  
  if [ ${#added[@]} -gt 0 ]; then
    echo "### Added"
    for commit in "${added[@]}"; do
      echo "- $commit"
    done
    echo ""
  fi
  
  if [ ${#fixed[@]} -gt 0 ]; then
    echo "### Fixed"
    for commit in "${fixed[@]}"; do
      echo "- $commit"
    done
    echo ""
  fi
  
  if [ ${#changed[@]} -gt 0 ]; then
    echo "### Changed"
    for commit in "${changed[@]}"; do
      echo "- $commit"
    done
    echo ""
  fi
  
  if [ ${#removed[@]} -gt 0 ]; then
    echo "### Removed"
    for commit in "${removed[@]}"; do
      echo "- $commit"
    done
    echo ""
  fi
} > CHANGELOG.md

echo "CHANGELOG.md generated successfully!"