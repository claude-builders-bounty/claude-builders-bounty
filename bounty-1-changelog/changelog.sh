#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history.
#
# Usage:
#   bash changelog.sh                        # commits since last tag
#   bash changelog.sh --all                  # full history across all tags
#   bash changelog.sh --since v1.0.0         # commits since a specific tag
#   bash changelog.sh --output RELEASES.md   # custom output file
#
# Requirements: Git, Bash 4.0+
# License: MIT

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OUTPUT_FILE="CHANGELOG.md"
SINCE_REF=""
ALL_TAGS=false
DRY_RUN=false

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --since)   SINCE_REF="$2"; shift 2 ;;
        --output)  OUTPUT_FILE="$2"; shift 2 ;;
        --all)     ALL_TAGS=true; shift ;;
        --dry-run) DRY_RUN=true; shift ;;
        --help|-h)
            sed -n '2,11p' "$0" | sed 's/^# \?//'
            exit 0
            ;;
        *) echo "Error: unknown argument '$1'. Use --help for usage." >&2; exit 1 ;;
    esac
done

# ---------------------------------------------------------------------------
# Verify we are inside a git repository
# ---------------------------------------------------------------------------
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: not a git repository." >&2
    exit 1
fi

REPO_NAME=$(basename "$(git rev-parse --show-toplevel)")

# ---------------------------------------------------------------------------
# categorize_commit — Determine the changelog section for a commit message.
#
# Strategy:
#   1. Conventional Commit prefix  (feat:, fix:, etc.)
#   2. Keyword fallback            (add, remove, delete, etc.)
#   3. Default to "Changed"
# ---------------------------------------------------------------------------
categorize_commit() {
    local msg="$1"
    local lower
    lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

    # --- Conventional Commit prefixes ---
    # Matches: feat:, feat(scope):, feat!:
    local cc_suffix='([(:!])'
    if [[ "$lower" =~ ^feat$cc_suffix   ]]; then echo "Added";   return; fi
    if [[ "$lower" =~ ^fix$cc_suffix    ]]; then echo "Fixed";   return; fi
    if [[ "$lower" =~ ^remove$cc_suffix ]]; then echo "Removed"; return; fi
    if [[ "$lower" =~ ^deprecate$cc_suffix ]]; then echo "Removed"; return; fi
    if [[ "$lower" =~ ^refactor$cc_suffix  ]]; then echo "Changed"; return; fi
    if [[ "$lower" =~ ^perf$cc_suffix   ]]; then echo "Changed"; return; fi
    if [[ "$lower" =~ ^style$cc_suffix  ]]; then echo "Changed"; return; fi
    if [[ "$lower" =~ ^docs$cc_suffix   ]]; then echo "Changed"; return; fi
    if [[ "$lower" =~ ^build$cc_suffix  ]]; then echo "Changed"; return; fi
    if [[ "$lower" =~ ^ci$cc_suffix     ]]; then echo "Changed"; return; fi
    if [[ "$lower" =~ ^chore$cc_suffix  ]]; then echo "Changed"; return; fi
    if [[ "$lower" =~ ^test$cc_suffix   ]]; then echo "Changed"; return; fi

    # --- Keyword fallback (for non-conventional commits) ---
    case "$lower" in
        add\ *|added\ *|create\ *|created\ *|new\ *|implement\ *|implemented\ *|introduce\ *)
            echo "Added"; return ;;
        fix\ *|fixed\ *|bug\ *|bugfix\ *|patch\ *|resolve\ *|resolved\ *|repair\ *|hotfix\ *)
            echo "Fixed"; return ;;
        remove\ *|removed\ *|delete\ *|deleted\ *|drop\ *|dropped\ *|deprecate\ *|deprecated\ *)
            echo "Removed"; return ;;
        update\ *|updated\ *|change\ *|changed\ *|modify\ *|modified\ *|refactor\ *|improve\ *|improved\ *|upgrade\ *|upgraded\ *|rename\ *|renamed\ *|move\ *|moved\ *|migrate\ *)
            echo "Changed"; return ;;
    esac

    # Default
    echo "Changed"
}

# ---------------------------------------------------------------------------
# clean_message — Strip conventional commit prefix and normalize.
# "feat(api): add user endpoint" -> "Add user endpoint"
# ---------------------------------------------------------------------------
clean_message() {
    local msg="$1"
    # Strip prefix like feat(scope)!: or fix:
    local cleaned
    cleaned=$(echo "$msg" | sed -E 's/^[a-zA-Z]+(\([^)]*\))?[!]?:[[:space:]]*//')
    # Capitalize first letter
    echo "$(echo "${cleaned:0:1}" | tr '[:lower:]' '[:upper:]')${cleaned:1}"
}

# ---------------------------------------------------------------------------
# generate_section — Build one version section of the changelog.
# Args: $1 = title, $2 = date, $3 = git range
# ---------------------------------------------------------------------------
generate_section() {
    local title="$1"
    local date="$2"
    local range="$3"

    # Collect commits (skip merges)
    local commits
    commits=$(git log "$range" --pretty=format:"%H %s" --no-merges 2>/dev/null || true)

    if [[ -z "$commits" ]]; then
        return
    fi

    # Categorize every commit
    declare -A BUCKETS
    BUCKETS[Added]=""
    BUCKETS[Fixed]=""
    BUCKETS[Changed]=""
    BUCKETS[Removed]=""

    while IFS= read -r line; do
        local hash="${line%% *}"
        local msg="${line#* }"
        local short_hash="${hash:0:7}"

        local category
        category=$(categorize_commit "$msg")

        local clean
        clean=$(clean_message "$msg")

        local entry="- ${clean} (\`${short_hash}\`)"

        if [[ -n "${BUCKETS[$category]}" ]]; then
            BUCKETS[$category]="${BUCKETS[$category]}"$'\n'"${entry}"
        else
            BUCKETS[$category]="${entry}"
        fi
    done <<< "$commits"

    # Print section header
    echo "## ${title} - ${date}"
    echo ""

    # Print categories in Keep a Changelog order
    local has_content=false
    for cat in "Added" "Changed" "Fixed" "Removed"; do
        if [[ -n "${BUCKETS[$cat]}" ]]; then
            echo "### ${cat}"
            echo "${BUCKETS[$cat]}"
            echo ""
            has_content=true
        fi
    done

    if [[ "$has_content" == false ]]; then
        return
    fi
}

# ---------------------------------------------------------------------------
# get_sorted_tags — Return tags sorted by commit date (newest first).
# ---------------------------------------------------------------------------
get_sorted_tags() {
    # Sort by the commit date each tag points to (newest first).
    # Falls back to version-sort if creatordate is unavailable.
    git tag --sort=-version:refname 2>/dev/null
}

# ---------------------------------------------------------------------------
# tag_date — Get the date a tag points to.
# ---------------------------------------------------------------------------
tag_date() {
    local tag="$1"
    git log -1 --format="%as" "$tag" 2>/dev/null || date +%Y-%m-%d
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    local changelog=""
    local header
    header="# Changelog"$'\n'$'\n'"All notable changes to **${REPO_NAME}** are documented in this file."$'\n'$'\n'"Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)."$'\n'

    # Gather all tags
    local tags
    tags=$(get_sorted_tags)
    local tag_array=()
    if [[ -n "$tags" ]]; then
        while IFS= read -r t; do
            tag_array+=("$t")
        done <<< "$tags"
    fi

    local tag_count=${#tag_array[@]}

    # -----------------------------------------------------------------------
    # Case 1: --since <ref> (single range)
    # -----------------------------------------------------------------------
    if [[ -n "$SINCE_REF" ]]; then
        local section
        section=$(generate_section "Unreleased" "$(date +%Y-%m-%d)" "${SINCE_REF}..HEAD")
        changelog="${section}"

    # -----------------------------------------------------------------------
    # Case 2: --all (full history across every tag)
    # -----------------------------------------------------------------------
    elif [[ "$ALL_TAGS" == true ]]; then
        # Unreleased: from newest tag to HEAD
        if [[ $tag_count -gt 0 ]]; then
            local unreleased
            unreleased=$(generate_section "Unreleased" "$(date +%Y-%m-%d)" "${tag_array[0]}..HEAD")
            if [[ -n "$unreleased" ]]; then
                changelog="${unreleased}"$'\n'
            fi
        fi

        # Each tag: tag[i]..tag[i-1] (from newest to oldest)
        for (( i=0; i<tag_count; i++ )); do
            local tag="${tag_array[$i]}"
            local tdate
            tdate=$(tag_date "$tag")

            local range
            if (( i + 1 < tag_count )); then
                range="${tag_array[$((i+1))]}..${tag}"
            else
                # Oldest tag: all commits up to that tag
                range="${tag}"
            fi

            local section
            section=$(generate_section "${tag}" "${tdate}" "${range}")
            if [[ -n "$section" ]]; then
                if [[ -n "$changelog" ]]; then
                    changelog="${changelog}"$'\n'"${section}"$'\n'
                else
                    changelog="${section}"$'\n'
                fi
            fi
        done

        # No tags at all: just dump everything
        if [[ $tag_count -eq 0 ]]; then
            local section
            section=$(generate_section "Unreleased" "$(date +%Y-%m-%d)" "HEAD")
            changelog="${section}"
        fi

    # -----------------------------------------------------------------------
    # Case 3: Default — commits since last tag (or all if no tags)
    # -----------------------------------------------------------------------
    else
        if [[ $tag_count -gt 0 ]]; then
            local latest="${tag_array[0]}"
            local section
            section=$(generate_section "Unreleased" "$(date +%Y-%m-%d)" "${latest}..HEAD")
            changelog="${section}"
        else
            local section
            section=$(generate_section "Unreleased" "$(date +%Y-%m-%d)" "HEAD")
            changelog="${section}"
        fi
    fi

    # -----------------------------------------------------------------------
    # Output
    # -----------------------------------------------------------------------
    if [[ -z "$changelog" ]]; then
        echo "No commits found to generate a changelog."
        exit 0
    fi

    local final_output="${header}"$'\n'"${changelog}"

    if [[ "$DRY_RUN" == true ]]; then
        echo "$final_output"
    else
        echo "$final_output" > "$OUTPUT_FILE"
        echo "Changelog written to ${OUTPUT_FILE} ($(echo "$changelog" | grep -c '^\-' || true) entries)"
    fi
}

main
