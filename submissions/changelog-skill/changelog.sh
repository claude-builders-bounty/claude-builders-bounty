#!/usr/bin/env bash
# changelog.sh — Generate structured CHANGELOG.md from git history
# Usage: bash changelog.sh [output_file]
set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo '.')"
cd "$REPO_ROOT"

# Colors for terminal output
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

echo -e "${BLUE}🔍 Scanning git history...${NC}"

# Get tags sorted by version (newest first)
mapfile -t TAGS < <(git tag -l --sort=-v:refname 2>/dev/null)

# Build tag date lookup
declare -A TAG_DATES
for tag in "${TAGS[@]}"; do
    tag_date=$(git log -1 --format="%ai" "$tag" 2>/dev/null | cut -d' ' -f1)
    TAG_DATES["$tag"]="$tag_date"
done

# Categorize a commit message
categorize() {
    local msg="$1"
    case "$msg" in
        feat:*|feature:*)    echo "Added" ;;
        fix:*|bugfix:*)      echo "Fixed" ;;
        change:*|refactor:*|perf:*|improve:*) echo "Changed" ;;
        remove:*|delete:*)   echo "Removed" ;;
        docs:*|doc:*)        echo "Documentation" ;;
        test:*|tests:*)      echo "Tests" ;;
        chore:*|ci:*|build:*|deps:*) echo "Maintenance" ;;
        *)                   echo "Other" ;;
    esac
}

# Format a single commit line
format_commit() {
    local hash="$1" msg="$2"
    local short_hash="${hash:0:7}"
    # Strip the prefix for cleaner display
    local clean_msg
    clean_msg=$(echo "$msg" | sed -E 's/^(feat|fix|change|refactor|perf|remove|delete|docs|chore|ci|build|test|tests|improve|bugfix|feature|doc|deps):\s*//')
    echo "- ${clean_msg} (\`${short_hash}\`)"
}

# Collect sections
declare -A SECTIONS
for section in Added Fixed Changed Removed Documentation Tests Maintenance Other; do
    SECTIONS["$section"]=""
done

# Generate content between two refs
generate_section() {
    local from_ref="${1:-}" to_ref="${2:-HEAD}"
    local range
    if [[ -n "$from_ref" ]]; then
        range="${from_ref}..${to_ref}"
    else
        range="$to_ref"
    fi

    # Reset sections
    for section in Added Fixed Changed Removed Documentation Tests Maintenance Other; do
        SECTIONS["$section"]=""
    done

    # Read commits (no merges, reverse order within range)
    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        hash="${line%% *}"
        msg="${line#* }"
        [[ "$msg" == "Merge "* ]] && continue

        cat=$(categorize "$msg")
        formatted=$(format_commit "$hash" "$msg")
        SECTIONS["$cat"]+="${formatted}"$'\n'
    done < <(git log --no-merges --reverse --format="%H %s" "$range" 2>/dev/null)
}

# Write output
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""

    if [[ ${#TAGS[@]} -eq 0 ]]; then
        # No tags — single unreleased section
        generate_section "" "HEAD"
        echo "## [Unreleased]"
        echo ""
        for section in Added Fixed Changed Removed Documentation Tests Maintenance Other; do
            if [[ -n "${SECTIONS[$section]}" ]]; then
                echo "### ${section}"
                echo ""
                echo -n "${SECTIONS[$section]}"
                echo ""
            fi
        done
    else
        # With tags — group by version
        prev_tag=""
        for tag in "${TAGS[@]}"; do
            tag_date="${TAG_DATES[$tag]:-unknown}"
            if [[ -z "$prev_tag" ]]; then
                # Unreleased (HEAD..latest_tag)
                generate_section "$tag" "HEAD"
                has_content=false
                for section in Added Fixed Changed Removed Documentation Tests Maintenance Other; do
                    [[ -n "${SECTIONS[$section]}" ]] && has_content=true
                done
                if $has_content; then
                    echo "## [Unreleased]"
                    echo ""
                    for section in Added Fixed Changed Removed Documentation Tests Maintenance Other; do
                        if [[ -n "${SECTIONS[$section]}" ]]; then
                            echo "### ${section}"
                            echo ""
                            echo -n "${SECTIONS[$section]}"
                            echo ""
                        fi
                    done
                fi
            fi

            # This tag's section
            if [[ -n "$prev_tag" ]]; then
                generate_section "$tag" "$prev_tag"
            else
                generate_section "" "$tag"
            fi

            echo "## [${tag}] - ${tag_date}"
            echo ""
            for section in Added Fixed Changed Removed Documentation Tests Maintenance Other; do
                if [[ -n "${SECTIONS[$section]}" ]]; then
                    echo "### ${section}"
                    echo ""
                    echo -n "${SECTIONS[$section]}"
                    echo ""
                fi
            done

            prev_tag="$tag"
        done
    fi
} > "$OUTPUT"

commit_count=$(git rev-list --count HEAD 2>/dev/null || echo "?")
section_count=$(grep -c '^### ' "$OUTPUT" 2>/dev/null || echo 0)

echo -e "${GREEN}✅ Generated ${OUTPUT}${NC}"
echo -e "   📊 ${commit_count} commits processed"
echo -e "   📂 ${section_count} sections generated"
if [[ ${#TAGS[@]} -gt 0 ]]; then
    echo -e "   🏷️  ${#TAGS[@]} version tags found"
fi
echo -e "   📝 Output: ${REPO_ROOT}/${OUTPUT}"
