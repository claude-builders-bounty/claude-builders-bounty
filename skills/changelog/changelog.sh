#!/usr/bin/env bash
#
# changelog.sh - Generate a structured CHANGELOG.md from git history
#
# Usage: bash changelog.sh [options]
#
# Options:
#   -o, --output FILE    Output file (default: CHANGELOG.md)
#   -f, --from TAG       Start from this tag (default: auto-detect last tag)
#   -t, --to REF         End at this ref (default: HEAD)
#   -v, --version VER    Version for this release (default: Unreleased)
#   -a, --append         Append to existing CHANGELOG instead of overwriting
#   -h, --help           Show this help message
#
# Examples:
#   bash changelog.sh                      # Generate from last tag to HEAD
#   bash changelog.sh -v 1.2.0             # Generate with version 1.2.0
#   bash changelog.sh -f v1.0.0 -t v1.1.0  # Generate between two tags
#

set -euo pipefail

# Default values
OUTPUT_FILE="CHANGELOG.md"
FROM_TAG=""
TO_REF="HEAD"
VERSION="Unreleased"
APPEND_MODE=false

# Temp files for categories (bash 3.x compatible)
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Category files
BREAKING_FILE="$TEMP_DIR/breaking"
SECURITY_FILE="$TEMP_DIR/security"
ADDED_FILE="$TEMP_DIR/added"
CHANGED_FILE="$TEMP_DIR/changed"
FIXED_FILE="$TEMP_DIR/fixed"
REMOVED_FILE="$TEMP_DIR/removed"
DOCS_FILE="$TEMP_DIR/docs"
OTHER_FILE="$TEMP_DIR/other"

# Initialize category files
touch "$BREAKING_FILE" "$SECURITY_FILE" "$ADDED_FILE" "$CHANGED_FILE"
touch "$FIXED_FILE" "$REMOVED_FILE" "$DOCS_FILE" "$OTHER_FILE"

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored message
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# Show help
show_help() {
    sed -n '2,/^$/p' "$0" | sed 's/^# //' | sed 's/^#//'
    exit 0
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -o|--output)
                OUTPUT_FILE="$2"
                shift 2
                ;;
            -f|--from)
                FROM_TAG="$2"
                shift 2
                ;;
            -t|--to)
                TO_REF="$2"
                shift 2
                ;;
            -v|--version)
                VERSION="$2"
                shift 2
                ;;
            -a|--append)
                APPEND_MODE=true
                shift
                ;;
            -h|--help)
                show_help
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                ;;
        esac
    done
}

# Check if we're in a git repository
check_git_repo() {
    if ! git rev-parse --is-inside-work-tree &>/dev/null; then
        log_error "Not a git repository. Please run from within a git repo."
        exit 1
    fi
}

# Get the last git tag, or empty if none exist
get_last_tag() {
    git describe --tags --abbrev=0 2>/dev/null || echo ""
}

# Get repository info
get_repo_info() {
    local remote_url
    remote_url=$(git config --get remote.origin.url 2>/dev/null || echo "")

    # Convert SSH to HTTPS format for GitHub links
    if [[ "$remote_url" == git@github.com:* ]]; then
        remote_url="${remote_url/git@github.com:/https://github.com/}"
        remote_url="${remote_url%.git}"
    elif [[ "$remote_url" == *.git ]]; then
        remote_url="${remote_url%.git}"
    fi

    echo "$remote_url"
}

# Convert string to lowercase (bash 3.x compatible)
to_lower() {
    echo "$1" | tr '[:upper:]' '[:lower:]'
}

# Categorize commit based on conventional commit type
categorize_commit() {
    local message="$1"
    local type=""

    # Extract conventional commit type using grep/sed (bash 3.x compatible)
    if echo "$message" | grep -qE '^[a-zA-Z]+(\(.+\))?!?:[[:space:]]'; then
        type=$(echo "$message" | sed -E 's/^([a-zA-Z]+)(\(.+\))?!?:[[:space:]].*/\1/')
        type=$(to_lower "$type")
    else
        type="other"
    fi

    case "$type" in
        feat|feature|add|new)
            echo "Added"
            ;;
        fix|bugfix|hotfix|patch)
            echo "Fixed"
            ;;
        docs|doc|documentation)
            echo "Documentation"
            ;;
        refactor|perf|performance|style|format)
            echo "Changed"
            ;;
        remove|delete|deprecate|deprecated)
            echo "Removed"
            ;;
        test|tests|testing)
            echo "Other"
            ;;
        build|ci|chore|deps|dependency)
            echo "Other"
            ;;
        security|sec)
            echo "Security"
            ;;
        breaking|break)
            echo "Breaking"
            ;;
        *)
            # Try to categorize by keywords in the message
            local msg_lower
            msg_lower=$(to_lower "$message")

            if echo "$msg_lower" | grep -qE '(add|new|create|implement|introduce)'; then
                echo "Added"
            elif echo "$msg_lower" | grep -qE '(fix|bug|repair|resolve|correct)'; then
                echo "Fixed"
            elif echo "$msg_lower" | grep -qE '(remove|delete|deprecate|drop)'; then
                echo "Removed"
            elif echo "$msg_lower" | grep -qE '(update|change|modify|refactor|improve|enhance)'; then
                echo "Changed"
            else
                echo "Other"
            fi
            ;;
    esac
}

# Clean commit message (remove type prefix for cleaner output)
clean_message() {
    local message="$1"

    # Remove conventional commit prefix using sed
    if echo "$message" | grep -qE '^[a-zA-Z]+(\(.+\))?!?:[[:space:]]'; then
        echo "$message" | sed -E 's/^[a-zA-Z]+(\(.+\))?!?:[[:space:]]//'
    else
        echo "$message"
    fi
}

# Main changelog generation
generate_changelog() {
    local from_ref="$FROM_TAG"
    local to_ref="$TO_REF"
    local repo_url
    repo_url=$(get_repo_info)

    # Auto-detect last tag if not specified
    if [[ -z "$from_ref" ]]; then
        from_ref=$(get_last_tag)
        if [[ -n "$from_ref" ]]; then
            log_info "Using last tag: $from_ref"
        else
            log_info "No tags found, using all commits"
        fi
    fi

    # Build git log range
    local range
    if [[ -n "$from_ref" ]]; then
        range="${from_ref}..${to_ref}"
    else
        range="$to_ref"
    fi

    log_info "Analyzing commits: $range"

    local commit_count=0

    # Read commits and categorize them
    while IFS='|' read -r hash author date message; do
        [[ -z "$hash" ]] && continue

        commit_count=$((commit_count + 1))

        local category
        category=$(categorize_commit "$message")
        local clean_msg
        clean_msg=$(clean_message "$message")
        local short_hash="${hash:0:7}"

        # Build commit entry
        local entry
        if [[ -n "$repo_url" ]]; then
            entry="- ${clean_msg} ([\`${short_hash}\`](${repo_url}/commit/${hash}))"
        else
            entry="- ${clean_msg} (\`${short_hash}\`)"
        fi

        # Add to appropriate category file
        case "$category" in
            Added)
                echo "$entry" >> "$ADDED_FILE"
                ;;
            Fixed)
                echo "$entry" >> "$FIXED_FILE"
                ;;
            Changed)
                echo "$entry" >> "$CHANGED_FILE"
                ;;
            Removed)
                echo "$entry" >> "$REMOVED_FILE"
                ;;
            Documentation)
                echo "$entry" >> "$DOCS_FILE"
                ;;
            Security)
                echo "$entry" >> "$SECURITY_FILE"
                ;;
            Breaking)
                echo "$entry" >> "$BREAKING_FILE"
                ;;
            *)
                echo "$entry" >> "$OTHER_FILE"
                ;;
        esac

    done < <(git log "$range" --pretty=format:'%H|%an|%ad|%s' --date=short 2>/dev/null)

    if [[ $commit_count -eq 0 ]]; then
        log_warn "No commits found in range: $range"
        return 1
    fi

    log_info "Found $commit_count commits"

    # Generate output
    local date_str
    date_str=$(date +%Y-%m-%d)

    # Start building output
    {
        # Header (only if not appending)
        if [[ "$APPEND_MODE" == false ]]; then
            echo "# Changelog"
            echo ""
            echo "All notable changes to this project will be documented in this file."
            echo ""
            echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),"
            echo "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)."
            echo ""
        fi

        # Version header
        if [[ "$VERSION" == "Unreleased" ]]; then
            echo "## [Unreleased]"
        else
            if [[ -n "$repo_url" ]] && [[ -n "$from_ref" ]]; then
                echo "## [${VERSION}](${repo_url}/compare/${from_ref}...${VERSION}) - ${date_str}"
            else
                echo "## [${VERSION}] - ${date_str}"
            fi
        fi
        echo ""

        # Breaking changes first (important!)
        if [[ -s "$BREAKING_FILE" ]]; then
            echo "### ⚠️ Breaking Changes"
            echo ""
            cat "$BREAKING_FILE"
            echo ""
        fi

        # Security (important!)
        if [[ -s "$SECURITY_FILE" ]]; then
            echo "### 🔒 Security"
            echo ""
            cat "$SECURITY_FILE"
            echo ""
        fi

        # Added
        if [[ -s "$ADDED_FILE" ]]; then
            echo "### ✨ Added"
            echo ""
            cat "$ADDED_FILE"
            echo ""
        fi

        # Changed
        if [[ -s "$CHANGED_FILE" ]]; then
            echo "### 🔄 Changed"
            echo ""
            cat "$CHANGED_FILE"
            echo ""
        fi

        # Fixed
        if [[ -s "$FIXED_FILE" ]]; then
            echo "### 🐛 Fixed"
            echo ""
            cat "$FIXED_FILE"
            echo ""
        fi

        # Removed
        if [[ -s "$REMOVED_FILE" ]]; then
            echo "### 🗑️ Removed"
            echo ""
            cat "$REMOVED_FILE"
            echo ""
        fi

        # Documentation
        if [[ -s "$DOCS_FILE" ]]; then
            echo "### 📚 Documentation"
            echo ""
            cat "$DOCS_FILE"
            echo ""
        fi

        # Other
        if [[ -s "$OTHER_FILE" ]]; then
            echo "### 📦 Other"
            echo ""
            cat "$OTHER_FILE"
            echo ""
        fi

    } > "$OUTPUT_FILE"

    log_success "Generated $OUTPUT_FILE with $commit_count commits"

    # Print summary
    echo ""
    echo "📊 Summary:"
    [[ -s "$BREAKING_FILE" ]] && echo "   ⚠️  Breaking: $(wc -l < "$BREAKING_FILE" | tr -d ' ')"
    [[ -s "$SECURITY_FILE" ]] && echo "   🔒 Security: $(wc -l < "$SECURITY_FILE" | tr -d ' ')"
    [[ -s "$ADDED_FILE" ]] && echo "   ✨ Added: $(wc -l < "$ADDED_FILE" | tr -d ' ')"
    [[ -s "$CHANGED_FILE" ]] && echo "   🔄 Changed: $(wc -l < "$CHANGED_FILE" | tr -d ' ')"
    [[ -s "$FIXED_FILE" ]] && echo "   🐛 Fixed: $(wc -l < "$FIXED_FILE" | tr -d ' ')"
    [[ -s "$REMOVED_FILE" ]] && echo "   🗑️  Removed: $(wc -l < "$REMOVED_FILE" | tr -d ' ')"
    [[ -s "$DOCS_FILE" ]] && echo "   📚 Docs: $(wc -l < "$DOCS_FILE" | tr -d ' ')"
    [[ -s "$OTHER_FILE" ]] && echo "   📦 Other: $(wc -l < "$OTHER_FILE" | tr -d ' ')"
}

# Main entry point
main() {
    parse_args "$@"
    check_git_repo
    generate_changelog
}

main "$@"
