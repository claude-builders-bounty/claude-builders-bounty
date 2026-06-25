#!/usr/bin/env bash
# generate-changelog.sh - ?git???????CHANGELOG
# ??: /generate-changelog ? bash generate-changelog.sh
# ???: Claude Code SKILL

set -euo pipefail

# ????tag??????????commit??
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)

echo "# Changelog"
echo ""
echo "## [Unreleased]"
echo ""

# ?????tag???commit
git log "$LAST_TAG..HEAD" --pretty=format:"%s" --no-merges 2>/dev/null | while read -r line; do
    case "$line" in
        feat:*|feature:*|add:*|implement*)
            echo "### Added"
            echo "- $line"
            ;;
        fix:*|bugfix:*|hotfix:*|patch*)
            echo "### Fixed"
            echo "- $line"
            ;;
        break*|breaking*|major*)
            echo "### Changed"
            echo "- $line (BREAKING)"
            ;;
        deprecat*)
            echo "### Deprecated"
            echo "- $line"
            ;;
        remov*|delete*)
            echo "### Removed"
            echo "- $line"
            ;;
        sec*|security*)
            echo "### Security"
            echo "- $line"
            ;;
        doc*)
            echo "### Documentation"
            echo "- $line"
            ;;
        perf*)
            echo "### Performance"
            echo "- $line"
            ;;
        test*)
            echo "### Tests"
            echo "- $line"
            ;;
        ci*|chore*|build*|refactor*)
            echo "### Maintenance"
            echo "- $line"
            ;;
        *)
            echo "- $line"
            ;;
    esac
done 2>/dev/null | while read -r line; do
    # ??????
    echo "$line"
done | awk '!seen[$0]++'
