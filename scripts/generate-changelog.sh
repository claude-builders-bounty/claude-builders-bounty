#!/bin/bash

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
LOG_FILE="CHANGELOG.md"

echo "# Changelog" > $LOG_FILE
echo "" >> $LOG_FILE
echo "## [Unreleased]" >> $LOG_FILE

COMMITS=$(git log ${LAST_TAG}..HEAD --pretty=format:"%s")

parse_commits() {
    local type=$1
    local title=$2
    echo "#### $title" >> $LOG_FILE
    echo "$COMMITS" | grep -i "^$type" | sed 's/^.*: /- /' >> $LOG_FILE
    echo "" >> $LOG_FILE
}

parse_commits "feat" "Added"
parse_commits "fix" "Fixed"
parse_commits "refactor" "Changed"
parse_commits "chore" "Removed"

echo "Changelog generated in $LOG_FILE"