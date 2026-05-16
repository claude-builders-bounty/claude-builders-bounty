#!/usr/bin/env bash
# =============================================================================
# 📋 Generate CHANGELOG — Conventional Commits → Structured Output
# =============================================================================
# Usage:
#   bash changelog.sh                     # Generate full changelog
#   bash changelog.sh --since v0.1.0      # Since a specific tag
#   bash changelog.sh --output FILE.md    # Write to custom file
#   bash changelog.sh --repo /path        # Run against a different repo
#   bash changelog.sh --dry-run           # Preview only (stdout)
#   bash changelog.sh --format json       # JSON output
#   bash changelog.sh --include-merges    # Include merge commits
#
# All notable changes to this project will be documented in this file.
# Format based on Keep a Changelog: https://keepachangelog.com/en/1.1.0/
# Commit parsing based on Conventional Commits: https://www.conventionalcommits.org/
# =============================================================================

set -euo pipefail

# ---- Emoji Map --------------------------------------------------------------

declare -A EMOJI_MAP
EMOJI_MAP=(
    [Added]="✨"
    [Fixed]="🐛"
    [Changed]="🔄"
    [Removed]="🗑️"
    [Deprecated]="⚠️"
    [Security]="🔒"
    [Performance]="⚡"
    [Documentation]="📚"
    [Tests]="🧪"
    [Build System]="🏗️"
    [Chores]="🔧"
)

# ---- Configuration ----------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" && [[ -n "$REPO_ROOT" ]]; then
    :
elif REPO_ROOT="$(cd "${SCRIPT_DIR}" && cd ../../ 2>/dev/null && pwd)" && [[ -n "$REPO_ROOT" ]]; then
    :
else
    REPO_ROOT="$SCRIPT_DIR"
fi
DEFAULT_OUTPUT="${REPO_ROOT}/CHANGELOG.md"
SINCE_REF=""
OUTPUT_FILE=""
REPO_PATH=""
DRY_RUN=false
INCLUDE_MERGES=false
OUTPUT_FORMAT="markdown"

# ---- Color helpers ----------------------------------------------------------

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

Generate a structured CHANGELOG from conventional commit git history.

Options:
  --since <ref>        Only include commits after this git ref (tag, commit, date)
  --output <file>      Write to a specific file (default: ${DEFAULT_OUTPUT})
  --repo <path>        Path to git repository (default: auto-detect from cwd)
  --format <format>    Output format: markdown (default) or json
  --dry-run            Print to stdout without writing any files
  --include-merges     Include merge commits in the changelog
  -h, --help           Show this help message

Examples:
  $(basename "$0")                                 # Generate complete changelog
  $(basename "$0") --since v1.0.0                   # Changes since v1.0.0
  $(basename "$0") --since "2025-01-01"             # Changes since Jan 1, 2025
  $(basename "$0") --since HEAD~10                   # Last 10 commits
  $(basename "$0") --output docs/CHANGELOG.md        # Custom output path
  $(basename "$0") --repo /path/to/project           # Run in another repo
  $(basename "$0") --format json                     # JSON output
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
                if [[ -z "${2:-}" ]]; then error "Missing value for --since"; exit 1; fi
                SINCE_REF="$2"; shift 2
                ;;
            --output)
                if [[ -z "${2:-}" ]]; then error "Missing value for --output"; exit 1; fi
                OUTPUT_FILE="$2"; shift 2
                ;;
            --repo)
                if [[ -z "${2:-}" ]]; then error "Missing value for --repo"; exit 1; fi
                REPO_PATH="$2"; shift 2
                ;;
            --format)
                if [[ -z "${2:-}" ]]; then error "Missing value for --format"; exit 1; fi
                if [[ "$2" == "json" ]] || [[ "$2" == "markdown" ]]; then
                    OUTPUT_FORMAT="$2"
                else
                    error "Invalid format: $2 (use 'markdown' or 'json')"
                    exit 1
                fi
                shift 2
                ;;
            --dry-run)    DRY_RUN=true; shift ;;
            --include-merges) INCLUDE_MERGES=true; shift ;;
            -h|--help)    usage ;;
            *)
                error "Unknown option: $1"
                echo ""
                usage
                ;;
        esac
    done
}

# ---- Git Operations ---------------------------------------------------------

# Wrapper that uses --repo path if set
git_cmd() {
    if [[ -n "$REPO_PATH" ]]; then
        command git -C "$REPO_PATH" "$@"
    else
        command git "$@"
    fi
}

get_log_range() {
    if [[ -n "$SINCE_REF" ]]; then
        if git_cmd rev-parse --verify --quiet "${SINCE_REF}" >/dev/null 2>&1; then
            echo "${SINCE_REF}..HEAD"
        else
            echo "--after=${SINCE_REF}"
        fi
    else
        local last_tag
        last_tag="$(git_cmd describe --tags --abbrev=0 2>/dev/null || true)"
        if [[ -n "$last_tag" ]]; then
            echo "${last_tag}..HEAD"
        else
            echo ""
        fi
    fi
}

get_commits() {
    local range="$1"
    local git_args=(log --format="%s|||%h|||%an|||%ad" --date=short --reverse)
    if [[ "$INCLUDE_MERGES" == "true" ]]; then :; else git_args+=(--no-merges); fi
    if [[ -n "$range" ]]; then
        if [[ "$range" == "--after="* ]]; then git_args+=("$range"); else git_args+=("$range"); fi
    else
        git_args+=(-200)
    fi
    git_cmd "${git_args[@]}"
}

# ---- Conventional Commit Parsing --------------------------------------------

parse_prefix() {
    local msg="$1"
    if [[ "$msg" =~ ^([a-zA-Z]+) ]]; then
        local prefix="${BASH_REMATCH[1],,}"
        if [[ "$msg" =~ ^[a-zA-Z]+[\(!]?\ *: ]]; then echo "$prefix"; fi
    fi
}

map_category() {
    local prefix="$1"
    case "$prefix" in
        feat|feature|add|new)          echo "Added" ;;
        fix|bug|bugfix|hotfix|patch)   echo "Fixed" ;;
        refactor|style|update|change)  echo "Changed" ;;
        remove|delete|rm)              echo "Removed" ;;
        deprecate|deprecated)          echo "Deprecated" ;;
        revert)                        echo "Removed" ;;
        perf|performance|speed|optimize) echo "Performance" ;;
        security|secure)               echo "Security" ;;
        docs|documentation|readme|doc) echo "Documentation" ;;
        test|tests|testing|spec)       echo "Tests" ;;
        build|ci|cd|infra|deps|dependencies) echo "Build System" ;;
        chore|chores|config|configs)   echo "Chores" ;;
        *)                             echo "" ;;
    esac
}

clean_message() {
    local msg="$1"
    if [[ "$msg" == *": "* ]]; then echo "${msg#*: }"; else echo "$msg"; fi
}

has_breaking_change() {
    local msg="$1"
    if [[ "$msg" == *"!"* && "$msg" == *": "* ]] && [[ "${msg%%:*}" == *"!" ]]; then
        return 0
    fi
    if echo "$msg" | grep -qi "BREAKING CHANGE"; then return 0; fi
    return 1
}

get_commit_url() {
    local hash="$1"
    local remote_url
    remote_url="$(git_cmd config --get remote.origin.url 2>/dev/null || true)"
    if [[ "$remote_url" =~ github\.com[:/](.+)/(.+)\..* ]]; then
        echo "https://github.com/${BASH_REMATCH[1]}/${BASH_REMATCH[2]}/commit/${hash}"
    elif [[ "$remote_url" =~ github\.com[:/](.+)/(.+) ]]; then
        echo "https://github.com/${BASH_REMATCH[1]}/${BASH_REMATCH[2]}/commit/${hash}"
    else
        echo "${hash}"
    fi
}

get_emoji() {
    local cat="$1"
    echo "${EMOJI_MAP[$cat]:-}"
}

# ---- JSON Escape Helper -----------------------------------------------------

json_escape() {
    local s="$1"
    s="${s//\\/\\\\}"
    s="${s//\"/\\\"}"
    s="${s//$'\n'/\\n}"
    s="${s//$'\r'/\\r}"
    s="${s//$'\t'/\\t}"
    echo "$s"
}

# ---- Changelog Generation ---------------------------------------------------

generate_output() {
    local range
    range="$(get_log_range)"
    local commits
    commits="$(get_commits "$range")"

    if [[ -z "$commits" ]]; then
        warn "No commits found${SINCE_REF:+ since '${SINCE_REF}'}."
        return 1
    fi

    # Initialize strings for each category (store entries as JSON lines)
    local md_Added="" md_Fixed="" md_Changed="" md_Removed="" md_Deprecated=""
    local md_Security="" md_Performance="" md_Documentation="" md_Tests=""
    local md_Build_System="" md_Chores=""

    local json_Added="" json_Fixed="" json_Changed="" json_Removed="" json_Deprecated=""
    local json_Security="" json_Performance="" json_Documentation="" json_Tests=""
    local json_Build_System="" json_Chores=""

    local total=0 categorized=0 breaking=0
    local breaking_entries_md=""
    local breaking_entries_json=""

    local CATEGORY_ORDER=("Added" "Fixed" "Changed" "Deprecated" "Removed"
                          "Security" "Performance" "Documentation" "Tests"
                          "Build System" "Chores")

    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        total=$((total + 1))

        # Parse the triple-pipe-delimited line
        local msg hash author date
        # Use field splitting: the format is "msg|||hash|||author|||date"
        # With triple pipes, cut on single | gives fields at positions 1, 4, 7, 10
        local IFS_backup="$IFS"
        IFS='|' read -r msg _ _ hash _ _ author _ _ date <<< "$line"
        IFS="$IFS_backup"

        local prefix
        prefix="$(parse_prefix "$msg")"
        local is_breaking=false

        if [[ -n "$prefix" ]]; then
            local category
            category="$(map_category "$prefix")"
            local entry_msg
            entry_msg="$(clean_message "$msg")"

            if [[ -n "$category" ]]; then
                if has_breaking_change "$msg"; then
                    is_breaking=true
                    entry_msg="BREAKING: ${entry_msg}"
                    breaking=$((breaking + 1))
                    local url
                    url="$(get_commit_url "$hash")"
                    breaking_entries_md="${breaking_entries_md}  - **${entry_msg}** ([${hash}](${url}))\n"
                    breaking_entries_json="${breaking_entries_json}{\"message\":\"$(json_escape "$entry_msg")\",\"hash\":\"${hash}\"},"
                fi

                if [[ "$is_breaking" == false ]]; then
                    local escaped_msg
                    escaped_msg="$(json_escape "$entry_msg")"
                    local md_entry="  - ${entry_msg} ([${hash}]($(get_commit_url "$hash")))"
                    local json_entry="{\"message\":\"${escaped_msg}\",\"hash\":\"${hash}\"}"

                    # Append to the right category
                    local md_varname="md_${category// /_}"
                    local json_varname="json_${category// /_}"
                    local current_md="${!md_varname:-}"
                    local current_json="${!json_varname:-}"
                    if [[ -z "$current_md" ]]; then
                        printf -v "$md_varname" "%s" "$md_entry"
                        printf -v "$json_varname" "%s" "$json_entry"
                    else
                        printf -v "$md_varname" "%s\n%s" "$current_md" "$md_entry"
                        printf -v "$json_varname" "%s,%s" "$current_json" "$json_entry"
                    fi
                fi
                categorized=$((categorized + 1))
            else
                # Unknown type → Changed
                local escaped_msg
                escaped_msg="$(json_escape "$(clean_message "$msg")")"
                if [[ -z "$md_Changed" ]]; then
                    md_Changed="  - $(clean_message "$msg")"
                    json_Changed="{\"message\":\"${escaped_msg}\",\"hash\":\"\"}"
                else
                    md_Changed="${md_Changed}\n  - $(clean_message "$msg")"
                    json_Changed="${json_Changed},{\"message\":\"${escaped_msg}\",\"hash\":\"\"}"
                fi
            fi
        else
            # No conventional prefix → Changed
            local escaped_msg
            escaped_msg="$(json_escape "$msg")"
            if [[ -z "$md_Changed" ]]; then
                md_Changed="  - ${msg}"
                json_Changed="{\"message\":\"${escaped_msg}\",\"hash\":\"\"}"
            else
                md_Changed="${md_Changed}\n  - ${msg}"
                json_Changed="${json_Changed},{\"message\":\"${escaped_msg}\",\"hash\":\"\"}"
            fi
        fi
    done <<< "$commits"

    # ---- Version Header ----
    local version="Unreleased"
    local date_str
    date_str="$(date +%Y-%m-%d)"
    if [[ -n "$SINCE_REF" ]]; then
        version="${SINCE_REF}"
    else
        local last_tag
        last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
        if [[ -n "$last_tag" ]]; then version="${last_tag}"; fi
    fi

    # ---- Output: JSON or Markdown ------------------------------------------

    if [[ "$OUTPUT_FORMAT" == "json" ]]; then
        echo "{"
        echo "  \"version\": \"$(json_escape "$version")\","
        echo "  \"date\": \"${date_str}\","
        echo "  \"categories\": {"
        local first_cat=true
        for cat in "${CATEGORY_ORDER[@]}"; do
            local json_varname="json_${cat// /_}"
            local val="${!json_varname:-}"
            if [[ -n "$val" ]]; then
                if [[ "$first_cat" == false ]]; then echo ","; fi
                first_cat=false
                echo "    \"${cat}\": [${val}]"
            fi
        done
        echo ""
        echo "  },"
        echo "  \"stats\": {"
        echo "    \"total\": ${total},"
        echo "    \"categorized\": ${categorized},"
        echo "    \"breaking\": ${breaking}"
        echo "  }"
        echo "}"
    else
        # Markdown output
        local output=""
        output+="# Changelog\n\n"
        output+="All notable changes to this project will be documented in this file.\n"
        output+="The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),\n"
        output+="and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n"
        output+="Commits are parsed using the [Conventional Commits](https://www.conventionalcommits.org/) specification.\n"
        output+="\n## [${version}] - ${date_str}\n\n"

        if [[ $breaking -gt 0 ]]; then
            output+="### 💥 Breaking Changes\n\n${breaking_entries_md}\n"
        fi

        for cat in "${CATEGORY_ORDER[@]}"; do
            local md_varname="md_${cat// /_}"
            local val="${!md_varname:-}"
            if [[ -n "$val" ]]; then
                local emoji
                emoji="$(get_emoji "$cat")"
                if [[ -n "$emoji" ]]; then
                    output+="### ${emoji} ${cat}\n\n"
                else
                    output+="### ${cat}\n\n"
                fi
                output+="${val}\n\n"
            fi
        done

        output+="---\n"
        output+="_${categorized} categorized commits out of ${total} total${breaking:+ (${breaking} breaking)}_\n"

        echo -e "$output"
    fi
}

# ---- Prepend Existing Changelog (markdown only) -----------------------------

prepend_changelog() {
    local new_content="$1"
    local output_file="$2"
    if [[ -f "$output_file" ]]; then
        local existing
        existing="$(cat "$output_file")"
        existing="$(echo -n "$existing" | sed '1s/^\xEF\xBB\xBF//')"
        echo -e "${new_content}\n\n$(cat "$output_file")"
    else
        echo "$new_content"
    fi
}

# ---- Main -------------------------------------------------------------------

main() {
    parse_args "$@"

    # If --repo was specified, use it; otherwise detect from cwd
    if [[ -n "$REPO_PATH" ]]; then
        REPO_ROOT="$REPO_PATH"
        if ! git_cmd rev-parse --git-dir >/dev/null 2>&1; then
            error "Not inside a git repository: $REPO_PATH"
            exit 1
        fi
    elif ! git_cmd rev-parse --git-dir >/dev/null 2>&1; then
        error "Not inside a git repository."
        exit 1
    fi

    cd "$REPO_ROOT"

    if ! git_cmd rev-list --max-parents=0 HEAD &>/dev/null; then
        warn "This repository has no commits yet."
        echo ""
        info "Nothing to generate — commit something first."
        exit 0
    fi

    if [[ -z "$OUTPUT_FILE" ]]; then
        OUTPUT_FILE="$DEFAULT_OUTPUT"
    fi

    title "📋 Generating CHANGELOG"

    echo -e "  ${CYAN}•${RESET} Repo root: ${BOLD}$REPO_ROOT${RESET}"
    echo -e "  ${CYAN}•${RESET} Since:     ${BOLD}${SINCE_REF:-last tag / all history}${RESET}"
    echo -e "  ${CYAN}•${RESET} Output:    ${BOLD}${OUTPUT_FILE}${RESET}"
    echo -e "  ${CYAN}•${RESET} Format:    ${BOLD}${OUTPUT_FORMAT}${RESET}"
    echo -e "  ${CYAN}•${RESET} Dry run:   ${BOLD}${DRY_RUN}${RESET}"
    echo -e "  ${CYAN}•${RESET} Merges:    ${BOLD}${INCLUDE_MERGES}${RESET}"
    echo ""

    local changelog_content
    if ! changelog_content="$(generate_output)"; then
        error "Failed to generate changelog."
        exit 1
    fi

    if [[ -z "$changelog_content" ]]; then
        error "Generated changelog is empty."
        exit 1
    fi

    local final_content
    if [[ -f "$OUTPUT_FILE" ]] && [[ "$OUTPUT_FORMAT" != "json" ]]; then
        info "Existing CHANGELOG found at ${OUTPUT_FILE} — prepending..."
        final_content="$(prepend_changelog "$changelog_content" "$OUTPUT_FILE")"
    else
        final_content="$changelog_content"
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        echo ""
        echo -e "$final_content"
        echo ""
        info "Dry run complete — no files written."
    else
        echo "$final_content" > "$OUTPUT_FILE"
        info "CHANGELOG written to ${BOLD}${OUTPUT_FILE}${RESET}"
    fi

    local commit_count
    commit_count="$(echo "$final_content" | grep -c "^- " || true)"
    echo ""
    info "Done — ${commit_count} changes documented."
}

# ---- Entry Point ------------------------------------------------------------

main "$@"
