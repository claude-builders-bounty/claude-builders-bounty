#!/bin/bash
# changelog.sh - Generate CHANGELOG.md from git history
# Usage: ./changelog.sh

set -e

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LAST_TAG" ]; then
    COMMITS=$(git log --all --pretty=format:"%h|%s|%an" -n 100)
else
    COMMITS=$(git log $LAST_TAG..HEAD --pretty=format:"%h|%s|%an" -n 100)
fi

cat > CHANGELOG.md << 'HEADER'
# Changelog

## [Unreleased]

HEADER

echo "$COMMITS" | while IFS='|' read hash msg author; do
    case "$msg" in
        feat*|Feature*|新增*)
            echo "### Added" >> CHANGELOG.md
            echo "- $hash $msg" >> CHANGELOG.md
            ;;
        fix*|Fix*|修复*)
            echo "### Fixed" >> CHANGELOG.md
            echo "- $hash $msg" >> CHANGELOG.md
            ;;
        docs*|Docs*|文档*)
            echo "### Documentation" >> CHANGELOG.md
            echo "- $hash $msg" >> CHANGELOG.md
            ;;
        *)
            echo "### Other" >> CHANGELOG.md
            echo "- $hash $msg" >> CHANGELOG.md
            ;;
    esac
done

echo "CHANGELOG.md generated!"
