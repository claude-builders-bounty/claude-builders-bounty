#!/usr/bin/env bash
#
# changelog.sh - Generate a structured CHANGELOG.md from git history
#
# Usage:
#   ./changelog.sh [options]
#
# Options:
#   --since DATE     Start date (YYYY-MM-DD) - default: last tag
#   --to DATE        End date (YYYY-MM-DD) - default: HEAD
#   --output FILE    Output file path - default: CHANGELOG.md
#   --append         Append to existing file instead of overwriting
#   --version VER    Version string for header - default: auto-detected
#   --unreleased     Mark as "[Unreleased]" section
#   --dry-run        Print to stdout only, don't write file
#   --help           Show this help message
#
# Examples:
#   ./changelog.sh                                    # Basic usage
#   ./changelog.sh --dry-run                          # Preview output
#   ./changelog.sh --since 2026-01-01                 # From specific date
#   ./changelog.sh --version 2.0.0 --output CHANGES.md # Custom version & file

set -euo pipefail

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_FILE="CHANGELOG.md"
SINCE_DATE=""
TO_DATE=""
VERSION=""
APPEND=false
DRY_RUN=false
UNRELEASED=false

# ---------------------------------------------------------------------------
# COLOR OUTPUT
# ---------------------------------------------------------------------------

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }
log_debug() { echo -e "${BLUE}[DEBUG]${NC} $1"; }

# ---------------------------------------------------------------------------
# UTILITY FUNCTIONS
# ---------------------------------------------------------------------------

show_help() {
    sed -n '/^# Usage:/,/^# /p' "$0" | sed 's/^# //' | head -n -1
    exit 0
}

# Check if we're in a git repository
check_git_repo() {
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "Not a git repository. Please run this script from a git project."
        exit 1
    fi
}

# Get the most recent tag
get_last_tag() {
    local last_tag
    last_tag=$(git describe --tags --abbrev=0 2>/dev/null || true)
    echo "$last_tag"
}

# Get version from latest tag or auto-detect
get_version() {
    local version=""

    if [[ -n "$VERSION" ]]; then
        echo "$VERSION"
        return
    fi

    # Try to get version from package.json
    if [[ -f "package.json" ]]; then
        version=$(grep -m1 '"version"' package.json | sed 's/.*"version".*"\([^"]*\)".*/\1/' 2>/dev/null || true)
    fi

    # Try to get version from latest tag
    if [[ -z "$version" ]]; then
        version=$(get_last_tag)
        # Strip 'v' prefix if present
        version="${version#v}"
    fi

    # Fallback
    if [[ -z "$version" ]]; then
        version="$(date +%Y.%m.%d)"
    fi

    echo "$version"
}

# ---------------------------------------------------------------------------
# COMMIT FETCHING
# ---------------------------------------------------------------------------

# Get commits in the specified range
get_commits() {
    local since="$1"
    local to="${2:-HEAD}"
    local range=""

    if [[ -n "$since" ]]; then
        if git rev-parse "$since" >/dev/null 2>&1; then
            range="${since}..${to}"
        else
            range="HEAD"
        fi
    else
        local last_tag
        last_tag=$(get_last_tag)
        if [[ -n "$last_tag" ]]; then
            range="${last_tag}..${to}"
        else
            range="HEAD"
        fi
    fi

    if [[ -n "$since" ]] && ! git rev-parse "$since" >/dev/null 2>&1; then
        git log "${to}" --since="${since}" --format="%H|%ci|%s|%b%x00" 2>/dev/null || true
    else
        git log "$range" --format="%H|%ci|%s|%b%x00" 2>/dev/null || true
    fi
}

# ---------------------------------------------------------------------------
# COMMIT CATEGORIZATION
# ---------------------------------------------------------------------------

categorize_commit() {
    local subject="$1"
    local lower_subject
    lower_subject=$(echo "$subject" | tr '[:upper:]' '[:lower:]')

    # Check conventional commit prefixes
    if [[ "$lower_subject" =~ ^(feat|feature|add|new|implement|introduce)[(:] ]]; then
        echo "added"; return
    fi
    if [[ "$lower_subject" =~ ^(fix|bugfix|hotfix|patch|resolve)[(:] ]]; then
        echo "fixed"; return
    fi
    if [[ "$lower_subject" =~ ^(chore|update|upgrade|refactor|perf|optimize|improve|change|modify|enhance)[(:] ]]; then
        echo "changed"; return
    fi
    if [[ "$lower_subject" =~ ^(remove|delete|deprecat|drop|clean)[(:] ]]; then
        echo "removed"; return
    fi

    # Keyword-based fallback
    if [[ "$lower_subject" =~ (add|adds|added|adding|new|implement|introduce|feature) ]]; then
        echo "added"; return
    fi
    if [[ "$lower_subject" =~ (fix|fixes|fixed|fixing|bug|repair|correct|resolve|resolves|patch) ]]; then
        echo "fixed"; return
    fi
    if [[ "$lower_subject" =~ (update|updates|updated|updating|upgrade|upgrades|refactor|refactored|change|changes|changed|modify|modified|improve|improved|optimize|optimized|enhance|enhanced|perf) ]]; then
        echo "changed"; return
    fi
    if [[ "$lower_subject" =~ (remove|removes|removed|removing|delete|deletes|deleted|deleting|drop|drops|dropped|deprecate|deprecated|clean|cleanup) ]]; then
        echo "removed"; return
    fi

    echo "other"
}

# Format a single commit line
format_commit_line() {
    local subject="$1"
    local cleaned
    cleaned=$(echo "$subject" | sed -E 's/^[a-z]+(\([^)]*\))?!?: *//i')
    cleaned="$(echo "${cleaned:0:1}" | tr '[:lower:]' '[:upper:]')${cleaned:1}"
    cleaned="${cleaned%.}"
    echo "$cleaned"
}

# ---------------------------------------------------------------------------
# CHANGELOG GENERATION
# ---------------------------------------------------------------------------

generate_changelog() {
    local version="$1"
    local date_str="$2"
    local commits_raw="$3"

    local added_entries=()
    local fixed_entries=()
    local changed_entries=()
    local removed_entries=()
    local other_entries=()

    local IFS=$'\0'
    local record
    for record in $commits_raw; do
        [[ -z "$record" ]] && continue

        local hash date_part subject body
        hash=$(echo "$record" | cut -d'|' -f1)
        subject=$(echo "$record" | cut -d'|' -f3)
        body=$(echo "$record" | cut -d'|' -f4-)

        [[ -z "$subject" ]] && continue
        [[ "$subject" =~ ^Merge ]] && continue

        local category formatted
        category=$(categorize_commit "$subject" "$body")
        formatted=$(format_commit_line "$subject")

        local dup=false
        case "$category" in
            added)
                for e in "${added_entries[@]}"; do [[ "$e" == "- $formatted" ]] && dup=true && break; done
                [[ "$dup" == false ]] && added_entries+=("- $formatted")
                ;;
            fixed)
                for e in "${fixed_entries[@]}"; do [[ "$e" == "- $formatted" ]] && dup=true && break; done
                [[ "$dup" == false ]] && fixed_entries+=("- $formatted")
                ;;
            changed)
                for e in "${changed_entries[@]}"; do [[ "$e" == "- $formatted" ]] && dup=true && break; done
                [[ "$dup" == false ]] && changed_entries+=("- $formatted")
                ;;
            removed)
                for e in "${removed_entries[@]}"; do [[ "$e" == "- $formatted" ]] && dup=true && break; done
                [[ "$dup" == false ]] && removed_entries+=("- $formatted")
                ;;
            other)
                for e in "${other_entries[@]}"; do [[ "$e" == "- $formatted" ]] && dup=true && break; done
                [[ "$dup" == false ]] && other_entries+=("- $formatted")
                ;;
        esac
    done

    local output=""
    if [[ "$UNRELEASED" == true ]]; then
        output+="## [Unreleased]"
    else
        output+="## [${version}] - ${date_str}"
    fi
    output+=$'\n\n'

    if [[ ${#added_entries[@]} -gt 0 ]]; then
        output+="### Added"$'\n'
        printf '%s\n' "${added_entries[@]}" >> /dev/tty 2>/dev/null || true
        for entry in "${added_entries[@]}"; do output+="${entry}"$'\n'; done
        output+=$'\n'
    fi
    if [[ ${#fixed_entries[@]} -gt 0 ]]; then
        output+="### Fixed"$'\n'
        for entry in "${fixed_entries[@]}"; do output+="${entry}"$'\n'; done
        output+=$'\n'
    fi
    if [[ ${#changed_entries[@]} -gt 0 ]]; then
        output+="### Changed"$'\n'
        for entry in "${changed_entries[@]}"; do output+="${entry}"$'\n'; done
        output+=$'\n'
    fi
    if [[ ${#removed_entries[@]} -gt 0 ]]; then
        output+="### Removed"$'\n'
        for entry in "${removed_entries[@]}"; do output+="${entry}"$'\n'; done
        output+=$'\n'
    fi
    if [[ ${#other_entries[@]} -gt 0 ]]; then
        output+="### Other"$'\n'
        for entry in "${other_entries[@]}"; do output+="${entry}"$'\n'; done
        output+=$'\n'
    fi

    echo "$output"
}

# ---------------------------------------------------------------------------
# FILE OPERATIONS
# ---------------------------------------------------------------------------

write_or_print() {
    local content="$1"

    if [[ "$DRY_RUN" == true ]]; then
        echo "$content"
        return
    fi

    if [[ "$APPEND" == true ]] && [[ -f "$OUTPUT_FILE" ]]; then
        local tmp_file title_line
        tmp_file=$(mktemp)
        title_line=$(head -n 1 "$OUTPUT_FILE")
        echo "$title_line" > "$tmp_file"
        echo "" >> "$tmp_file"
        echo "$content" >> "$tmp_file"
        tail -n +3 "$OUTPUT_FILE" >> "$tmp_file"
        mv "$tmp_file" "$OUTPUT_FILE"
        log_info "Changelog section appended to $OUTPUT_FILE"
    else
        {
            echo "# Changelog"
            echo ""
            echo "$content"
        } > "$OUTPUT_FILE"
        log_info "Changelog written to $OUTPUT_FILE"
    fi
}

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

main() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --since)     SINCE_DATE="$2"; shift 2 ;;
            --to)        TO_DATE="$2"; shift 2 ;;
            --output)    OUTPUT_FILE="$2"; shift 2 ;;
            --version)   VERSION="$2"; shift 2 ;;
            --append)    APPEND=true; shift ;;
            --unreleased) UNRELEASED=true; shift ;;
            --dry-run)   DRY_RUN=true; shift ;;
            --help)      show_help ;;
            *)           log_error "Unknown option: $1"; show_help ;;
        esac
    done

    log_info "CHANGELOG Generator v1.0.0"
    check_git_repo

    local last_tag
    last_tag=$(get_last_tag)
    [[ -n "$last_tag" ]] && log_info "Last tag: $last_tag" || log_warn "No tags found. Using all commits."

    local since="$SINCE_DATE"
    if [[ -z "$since" ]]; then
        if [[ -n "$last_tag" ]]; then
            since="$last_tag"
            log_info "Fetching commits since tag: $since"
        else
            log_info "Fetching all commits"
        fi
    else
        log_info "Fetching commits since: $since"
    fi

    log_info "Fetching commit history..."
    local commits
    commits=$(get_commits "$since" "${TO_DATE:-HEAD}")

    if [[ -z "$commits" ]]; then
        log_warn "No commits found in the specified range."
        exit 0
    fi

    local commit_count
    commit_count=$(echo "$commits" | grep -c '^' || echo "0")
    log_info "Found $commit_count commits to process"

    local version date_str
    version=$(get_version)
    date_str=$(date +%Y-%m-%d)

    [[ "$UNRELEASED" == true ]] && log_info "Generating unreleased section..." || log_info "Generating changelog for version $version..."

    local changelog
    changelog=$(generate_changelog "$version" "$date_str" "$commits")

    write_or_print "$changelog"

    if [[ "$DRY_RUN" != true ]]; then
        log_info "Done! Output: $OUTPUT_FILE"
        log_info "Preview (first 20 lines):"
        head -n 20 "$OUTPUT_FILE" 2>/dev/null | while IFS= read -r line; do echo "  $line"; done
    fi
}

main "$@"
