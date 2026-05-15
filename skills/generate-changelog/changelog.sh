#!/usr/bin/env bash
# =============================================================================
# 📋 Generate CHANGELOG — Conventional Commits → Structured Markdown
# =============================================================================
# Usage:
#   bash changelog.sh                     # Generate full changelog
#   bash changelog.sh --since v0.1.0      # Since a specific tag
#   bash changelog.sh --output FILE.md    # Write to custom file
#   bash changelog.sh --dry-run           # Preview only (stdout)
#   bash changelog.sh --include-merges    # Include merge commits
#
# All notable changes to this project will be documented in this file.
# Format based on Keep a Changelog: https://keepachangelog.com/en/1.1.0/
# Commit parsing based on Conventional Commits: https://www.conventionalcommits.org/
# =============================================================================

set -euo pipefail

# ---- Configuration ----------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Determine repo root: use git root from current directory first
# then fall back to going up 2 levels from script dir
if REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" && [[ -n "$REPO_ROOT" ]]; then
    : # REPO_ROOT already set
elif REPO_ROOT="$(cd "${SCRIPT_DIR}" && cd ../../ 2>/dev/null && pwd)" && [[ -n "$REPO_ROOT" ]]; then
    : # REPO_ROOT from path
else
    REPO_ROOT="$SCRIPT_DIR"
fi
DEFAULT_OUTPUT="${REPO_ROOT}/CHANGELOG.md"
SINCE_REF=""
OUTPUT_FILE=""
DRY_RUN=false
INCLUDE_MERGES=false

# ---- Color helpers (disabled in dry-run to keep output clean) ----------------

RESET=""
BOLD=""
GREEN=""
YELLOW=""
RED=""
BLUE=""
CYAN=""

if [[ -t 1 ]]; then
    RESET="\033[0m"
    BOLD="\033[1m"
    GREEN="\033[0;32m"
    YELLOW="\033[1;33m"
    RED="\033[0;31m"
    BLUE="\033[0;34m"
    CYAN="\033[0;36m"
fi

info()  { echo -e "  ${GREEN}✓${RESET} $1"; }
warn()  { echo -e "  ${YELLOW}⚠${RESET} $1"; }
error() { echo -e "  ${RED}✗${RESET} $1" >&2; }
title() { echo -e "\n${BOLD}${BLUE}$1${RESET}\n"; }

# ---- Help -------------------------------------------------------------------

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Generate a structured CHANGELOG.md from conventional commit git history.

Options:
  --since <ref>        Only include commits after this git ref (tag, commit, date)
  --output <file>      Write to a specific file (default: ${DEFAULT_OUTPUT})
  --dry-run            Print to stdout without writing any files
  --include-merges     Include merge commits in the changelog
  -h, --help           Show this help message

Examples:
  $(basename "$0")                                 # Generate complete changelog
  $(basename "$0") --since v1.0.0                   # Changes since v1.0.0
  $(basename "$0") --since "2025-01-01"             # Changes since Jan 1, 2025
  $(basename "$0") --since HEAD~10                   # Last 10 commits
  $(basename "$0") --output docs/CHANGELOG.md        # Custom output path
  $(basename "$0") --dry-run                        # Preview only
  $(basename "$0") --include-merges                  # Include merges
EOF
    exit 0
}

# ---- Argument Parsing -------------------------------------------------------

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --since)
                if [[ -z "${2:-}" ]]; then
                    error "Missing value for --since"
                    exit 1
                fi
                SINCE_REF="$2"
                shift 2
                ;;
            --output)
                if [[ -z "${2:-}" ]]; then
                    error "Missing value for --output"
                    exit 1
                fi
                OUTPUT_FILE="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --include-merges)
                INCLUDE_MERGES=true
                shift
                ;;
            -h|--help)
                usage
                ;;
            *)
                error "Unknown option: $1"
                echo ""
                usage
                ;;
        esac
    done
}

# ---- Git Operations ---------------------------------------------------------

# Determine git log range based on --since flag
get_log_range() {
    if [[ -n "$SINCE_REF" ]]; then
        # Check if since_ref resolves to something
        if git rev-parse --verify --quiet "${SINCE_REF}" >/dev/null 2>&1; then
            echo "${SINCE_REF}..HEAD"
        else
            # Try as a date
            echo "--after=${SINCE_REF}"
        fi
    else
        # Try last tag, fallback to all commits
        local last_tag
        last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
        if [[ -n "$last_tag" ]]; then
            echo "${last_tag}..HEAD"
        else
            echo ""
        fi
    fi
}

# Fetch commits with proper format
get_commits() {
    local range="$1"
    local git_args=(log --format="%s|||%h|||%an|||%ad" --date=short --reverse)

    if [[ "$INCLUDE_MERGES" == "true" ]]; then
        # Include merges — filter them later
        :
    else
        git_args+=(--no-merges)
    fi

    if [[ -n "$range" ]]; then
        # Range could be "tag..HEAD" or "--after=DATE"
        if [[ "$range" == "--after="* ]]; then
            git_args+=("$range")
        else
            git_args+=("$range")
        fi
    else
        # No range specified, get last 200 commits
        git_args+=(-200)
    fi

    git "${git_args[@]}"
}

# ---- Conventional Commit Parsing --------------------------------------------

# Parse conventional commit prefix from a commit message
# Returns: prefix (e.g., "feat", "fix") or empty string
parse_prefix() {
    local msg="$1"
    # Match conventional commit pattern: type(scope)!: description
    # or type: description
    # Extract prefix before any (, ), or :
    if [[ "$msg" =~ ^([a-zA-Z]+) ]]; then
        local prefix="${BASH_REMATCH[1],,}"
        # Verify it's followed by conventional commit structure
        # Valid patterns: "type:", "type(scope):", "type!:"
        if [[ "$msg" =~ ^[a-zA-Z]+[\(!]?\ *: ]]; then
            echo "$prefix"
        fi
    fi
}

# Map conventional commit type to changelog category
# Based on: https://www.conventionalcommits.org/en/v1.0.0/
map_category() {
    local prefix="$1"

    case "$prefix" in
        feat|feature|add|new)
            echo "Added"
            ;;
        fix|bug|bugfix|hotfix|patch)
            echo "Fixed"
            ;;
        refactor|style|update|change)
            echo "Changed"
            ;;
        remove|delete|rm)
            echo "Removed"
            ;;
        deprecate|deprecated)
            echo "Deprecated"
            ;;
        revert)
            echo "Removed"
            ;;
        perf|performance|speed|optimize)
            echo "Performance"
            ;;
        security|secure)
            echo "Security"
            ;;
        docs|documentation|readme|doc)
            echo "Documentation"
            ;;
        test|tests|testing|spec)
            echo "Tests"
            ;;
        build|ci|cd|infra|deps|dependencies)
            echo "Build System"
            ;;
        chore|chores|config|configs)
            echo "Chores"
            ;;
        *)
            echo ""  # Uncategorized
            ;;
    esac
}

# Clean commit message: remove the conventional commit prefix
# e.g., "feat(auth): add login" → "add login"
clean_message() {
    local msg="$1"
    # Remove type(scope)!: prefix using simpler approach
    # Find the first ": " and take everything after it
    if [[ "$msg" == *": "* ]]; then
        echo "${msg#*: }"
    else
        echo "$msg"
    fi
}

# Check if message has breaking change indicator
has_breaking_change() {
    local msg="$1"
    # Check for ! before : or BREAKING CHANGE footer
    # Use simple string matching for !: pattern
    if [[ "$msg" == *"!"* && "$msg" == *": "* ]] && \
       [[ "${msg%%:*}" == *"!" ]]; then
        return 0
    fi
    if echo "$msg" | grep -qi "BREAKING CHANGE"; then
        return 0
    fi
    return 1
}

# ---- Changelog Generation ---------------------------------------------------

generate_changelog() {
    local range
    range="$(get_log_range)"
    local commits
    commits="$(get_commits "$range")"

    # Check if we got any commits
    if [[ -z "$commits" ]]; then
        warn "No commits found${SINCE_REF:+ since '${SINCE_REF}'}."
        return 1
    fi

    # Initialize category buckets
    declare -A categories
    categories=(
        ["Added"]=""
        ["Fixed"]=""
        ["Changed"]=""
        ["Removed"]=""
        ["Deprecated"]=""
        ["Security"]=""
        ["Performance"]=""
        ["Documentation"]=""
        ["Tests"]=""
        ["Build System"]=""
        ["Chores"]=""
    )

    local total=0
    local categorized=0
    local breaking=0
    local breaking_entries=""

    # Process each commit (format: "msg|||hash|||author|||date")
    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        total=$((total + 1))

        local msg hash author date
        msg="$(echo "$line" | cut -d'|' -f1)"
        hash="$(echo "$line" | cut -d'|' -f2)"
        author="$(echo "$line" | cut -d'|' -f3)"
        date="$(echo "$line" | cut -d'|' -f4)"

        local prefix
        prefix="$(parse_prefix "$msg")"

        if [[ -n "$prefix" ]]; then
            local category
            category="$(map_category "$prefix")"
            local entry_msg
            entry_msg="$(clean_message "$msg")"

            if [[ -n "$category" ]]; then
                # Check for breaking change
                if has_breaking_change "$msg"; then
                    category="Changed"  # Breaking changes go to Changed with a marker
                    entry_msg="**BREAKING**: ${entry_msg}"
                    breaking=$((breaking + 1))
                    breaking_entries="${breaking_entries}  - ${entry_msg} (${hash})\n"
                fi

                local formatted_entry
                if [[ -n "$hash" ]]; then
                    formatted_entry="  - ${entry_msg} ([${hash}]($(get_commit_url "$hash")))"
                else
                    formatted_entry="  - ${entry_msg}"
                fi

                if [[ -z "${categories[$category]}" ]]; then
                    categories[$category]="${formatted_entry}"
                else
                    categories[$category]="${categories[$category]}"$'\n'"${formatted_entry}"
                fi
                categorized=$((categorized + 1))
            else
                # Unknown type — put in Changed
                local entry
                entry="  - $(clean_message "$msg")"
                if [[ -z "${categories['Changed']}" ]]; then
                    categories['Changed']="$entry"
                else
                    categories['Changed']="${categories['Changed']}"$'\n'"$entry"
                fi
            fi
        else
            # No conventional commit prefix — try heuristic
            local entry
            entry="  - ${msg}"
            if [[ -z "${categories['Changed']}" ]]; then
                categories['Changed']="$entry"
            else
                categories['Changed']="${categories['Changed']}"$'\n'"$entry"
            fi
        fi
    done <<< "$commits"

    # ---- Generate Date/Version Header ----
    local version="Unreleased"
    local date_str
    date_str="$(date +%Y-%m-%d)"

    if [[ -n "$SINCE_REF" ]]; then
        version="${SINCE_REF}"
    else
        local last_tag
        last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
        if [[ -n "$last_tag" ]]; then
            version="${last_tag}"
        fi
    fi

    # ---- Assemble Output ----
    local output=""

    # Header
    output+="# Changelog\n\n"
    output+="All notable changes to this project will be documented in this file.\n"
    output+="The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),\n"
    output+="and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n"
    output+="Commits are parsed using the [Conventional Commits](https://www.conventionalcommits.org/) specification.\n"
    output+="\n## [${version}] - ${date_str}\n\n"

    # Breaking changes first (if any)
    if [[ $breaking -gt 0 ]]; then
        output+="### ⚠ Breaking Changes\n\n"
        output+="${breaking_entries}\n"
    fi

    # Categories in order
    local order=("Added" "Fixed" "Changed" "Deprecated" "Removed" "Security" "Performance" "Documentation" "Tests" "Build System" "Chores")
    for cat in "${order[@]}"; do
        local items="${categories[$cat]}"
        if [[ -n "$items" ]]; then
            output+="### ${cat}\n\n${items}\n\n"
        fi
    done

    # Stats summary
    output+="---\n"
    output+="_${categorized} categorized commits out of ${total} total${breaking:+ (${breaking} breaking)}_\n"

    echo -e "$output"
}

# ---- Helper: Commit URL -----------------------------------------------------

get_commit_url() {
    local hash="$1"
    local remote_url
    remote_url="$(git config --get remote.origin.url 2>/dev/null || true)"
    if [[ "$remote_url" =~ github\.com[:/](.+)/(.+)\.git ]]; then
        echo "https://github.com/${BASH_REMATCH[1]}/${BASH_REMATCH[2]}/commit/${hash}"
    elif [[ "$remote_url" =~ github\.com[:/](.+)/(.+) ]]; then
        echo "https://github.com/${BASH_REMATCH[1]}/${BASH_REMATCH[2]}/commit/${hash}"
    else
        echo "${hash}"
    fi
}

# ---- Prepend Existing Changelog ---------------------------------------------

prepend_changelog() {
    local new_content="$1"
    local output_file="$2"

    if [[ -f "$output_file" ]]; then
        local existing
        existing="$(cat "$output_file")"
        # Remove BOM if present
        existing="$(echo -n "$existing" | sed '1s/^\xEF\xBB\xBF//')"

        # Check if the existing file already has a header we should keep
        # We'll insert the new content right after the title line
        echo -e "${new_content}\n\n$(cat "$output_file")"
    else
        echo "$new_content"
    fi
}

# ---- Main -------------------------------------------------------------------

main() {
    parse_args "$@"

    # Verify we're in a git repo
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        error "Not inside a git repository."
        exit 1
    fi

    # Change to repo root for git operations
    cd "$REPO_ROOT"

    # Check for empty repo (no commits yet)
    if ! git rev-list --max-parents=0 HEAD &>/dev/null; then
        warn "This repository has no commits yet."
        echo ""
        info "Nothing to generate — commit something first."
        exit 0
    fi

    # Determine output file
    if [[ -z "$OUTPUT_FILE" ]]; then
        OUTPUT_FILE="$DEFAULT_OUTPUT"
    fi

    title "📋 Generating CHANGELOG"

    # Show configuration
    echo -e "  ${CYAN}•${RESET} Repo root: ${BOLD}$REPO_ROOT${RESET}"
    echo -e "  ${CYAN}•${RESET} Since:     ${BOLD}${SINCE_REF:-last tag / all history}${RESET}"
    echo -e "  ${CYAN}•${RESET} Output:    ${BOLD}${OUTPUT_FILE}${RESET}"
    echo -e "  ${CYAN}•${RESET} Dry run:   ${BOLD}${DRY_RUN}${RESET}"
    echo -e "  ${CYAN}•${RESET} Merges:    ${BOLD}${INCLUDE_MERGES}${RESET}"
    echo ""

    # Generate changelog content
    local changelog_content
    if ! changelog_content="$(generate_changelog)"; then
        error "Failed to generate changelog."
        exit 1
    fi

    if [[ -z "$changelog_content" ]]; then
        error "Generated changelog is empty."
        exit 1
    fi

    # Prepend to existing changelog if it exists
    local final_content
    if [[ -f "$OUTPUT_FILE" ]]; then
        info "Existing CHANGELOG found at ${OUTPUT_FILE} — prepending..."
        final_content="$(prepend_changelog "$changelog_content" "$OUTPUT_FILE")"
    else
        final_content="$changelog_content"
    fi

    # Output
    if [[ "$DRY_RUN" == "true" ]]; then
        # Strip ANSI for clean dry-run output
        echo ""
        echo -e "$final_content"
        echo ""
        info "Dry run complete — no files written."
    else
        # Write to file
        echo "$final_content" > "$OUTPUT_FILE"
        info "CHANGELOG written to ${BOLD}${OUTPUT_FILE}${RESET}"
    fi

    # Stats
    local commit_count
    commit_count="$(echo "$final_content" | grep -c "^- " || true)"
    echo ""
    info "Done — ${commit_count} changes documented."
}

# ---- Entry Point ------------------------------------------------------------

main "$@"
