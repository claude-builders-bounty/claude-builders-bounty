#!/bin/bash
# generate-changelog.sh — Structured CHANGELOG from git history
# Usage: ./generate-changelog.sh [v1.0.0..v2.0.0]

set -euo pipefail

VERSION_RANGE="${1:-HEAD}"
OUTPUT_FILE="CHANGELOG.md"
TEMP_FILE=$(mktemp)

# Header
cat > "$TEMP_FILE" << 'HEADER'
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

HEADER

# Categorize commits
declare -A CATEGORIES
CATEGORIES["feat"]="### Added"
CATEGORIES["fix"]="### Fixed"
CATEGORIES["docs"]="### Documentation"
CATEGORIES["style"]="### Changed"
CATEGORIES["refactor"]="### Changed"
CATEGORIES["perf"]="### Changed"
CATEGORIES["test"]="### Changed"
CATEGORIES["chore"]="### Changed"
CATEGORIES["build"]="### Changed"
CATEGORIES["ci"]="### Changed"

# Parse git log
git log --pretty=format:"%H|%s|%b|%ad" --date=short --no-merges "$VERSION_RANGE" | while IFS='|' read -r hash subject body date; do
    # Extract conventional commit type
    type=$(echo "$subject" | sed -n 's/^\([a-zA-Z]*\)[(:].*/\1/p')
    [[ -z "$type" ]] && type="chore"
    
    # Extract scope
    scope=$(echo "$subject" | sed -n 's/^[a-zA-Z]*(\([^)]*\)).*/\1/p')
    
    # Clean subject line
    clean_subject=$(echo "$subject" | sed 's/^[a-zA-Z]*[(:][^)]*[):] *//')
    
    # Build entry
    entry="- ${clean_subject} ([${hash:0:7}](https://github.com/${GITHUB_REPOSITORY:-owner/repo}/commit/${hash}))"
    [[ -n "$scope" ]] && entry="- **${scope}:** ${clean_subject} ([${hash:0:7}](https://github.com/${GITHUB_REPOSITORY:-owner/repo}/commit/${hash}))"
    
    # Categorize
    category="${CATEGORIES[$type]:-"### Changed"}"
    echo "${date}|${category}|${entry}" >> "$TEMP_FILE.entries"
done

# Group by date and category
if [[ -f "$TEMP_FILE.entries" ]]; then
    sort -t'|' -k1,1r -k2,2 "$TEMP_FILE.entries" | awk -F'|' '
    {
        date=$1
        cat=$2
        entry=$3
        
        if (date != last_date) {
            if (last_date != "") print ""
            print "## [" date "]"
            last_date=date
            last_cat=""
        }
        
        if (cat != last_cat) {
            print ""
            print cat
            last_cat=cat
        }
        
        print entry
    }' >> "$TEMP_FILE"
    
    rm -f "$TEMP_FILE.entries"
fi

mv "$TEMP_FILE" "$OUTPUT_FILE"
echo "[+] CHANGELOG generated: $OUTPUT_FILE"
