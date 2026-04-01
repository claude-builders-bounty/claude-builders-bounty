#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# changelog.sh — Generate CHANGELOG from git history
#
# Fetches commits since the last git tag and auto-categorizes them into
# Added / Fixed / Changed / Removed sections using conventional commits
# prefixes with keyword fallback.
#
# Usage:
#   bash changelog.sh [options]
#   /generate-changelog              (as a Claude Code skill)
#
# Options:
#   --from <ref>       Start ref (default: latest tag, or first commit)
#   --to <ref>         End ref (default: HEAD)
#   --output <file>    Output file (default: stdout)
#   --version <ver>    Version label (default: Unreleased)
#   --help             Show this help
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
FROM_REF=""
TO_REF="HEAD"
OUTPUT=""
VERSION="Unreleased"

# ---------------------------------------------------------------------------
# Arg parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --from)    FROM_REF="$2"; shift 2 ;;
        --to)      TO_REF="$2"; shift 2 ;;
        --output)  OUTPUT="$2"; shift 2 ;;
        --version) VERSION="$2"; shift 2 ;;
        --help)
            sed -n '3,16p' "$0" | sed 's/^# \?//'
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Resolve start ref
# ---------------------------------------------------------------------------
resolve_from_ref() {
    if [[ -n "$FROM_REF" ]]; then
        echo "$FROM_REF"
        return
    fi

    local latest_tag
    latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"

    if [[ -n "$latest_tag" ]]; then
        echo "$latest_tag"
    else
        # No tags — use the root commit
        git rev-list --max-parents=0 HEAD | head -1
    fi
}

# ---------------------------------------------------------------------------
# Categorize a single commit message
#
# Strategy:
#   1. Conventional commit prefix (feat:, fix:, etc.)
#   2. Keyword fallback (add, remove, fix, change, etc.)
#   3. Default to "Changed"
# ---------------------------------------------------------------------------
categorize() {
    local msg="$1"
    local lower
    lower="$(echo "$msg" | tr '[:upper:]' '[:lower:]')"

    # Conventional commits
    case "$lower" in
        feat\(*\):*|feat:*)       echo "Added";   return ;;
        fix\(*\):*|fix:*)         echo "Fixed";   return ;;
        remove\(*\):*|remove:*)   echo "Removed"; return ;;
        revert\(*\):*|revert:*)   echo "Removed"; return ;;
        refactor\(*\):*|refactor:*) echo "Changed"; return ;;
        perf\(*\):*|perf:*)       echo "Changed"; return ;;
        docs\(*\):*|docs:*)       echo "Changed"; return ;;
        style\(*\):*|style:*)     echo "Changed"; return ;;
        chore\(*\):*|chore:*)     echo "Changed"; return ;;
        build\(*\):*|build:*)     echo "Changed"; return ;;
        ci\(*\):*|ci:*)           echo "Changed"; return ;;
        test\(*\):*|test:*)       echo "Changed"; return ;;
    esac

    # Keyword fallback
    case "$lower" in
        *"add "*|*"added "*|*"create "*|*"implement "*|*"introduce "*)
            echo "Added"; return ;;
        *"fix "*|*"fixed "*|*"bugfix"*|*"patch "*|*"resolve "*)
            echo "Fixed"; return ;;
        *"remove "*|*"removed "*|*"delete "*|*"drop "*|*"deprecate "*)
            echo "Removed"; return ;;
        *)
            echo "Changed" ;;
    esac
}

# ---------------------------------------------------------------------------
# Strip conventional commit prefix for cleaner display
# ---------------------------------------------------------------------------
clean_message() {
    local msg="$1"
    # Remove "type(scope): " or "type: " prefix
    echo "$msg" | sed -E 's/^[a-z]+(\([^)]*\))?:\s*//'
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    if ! git rev-parse --is-inside-work-tree &>/dev/null; then
        echo "Error: not inside a git repository" >&2
        exit 1
    fi

    local from_ref
    from_ref="$(resolve_from_ref)"

    # Collect commits (hash + subject)
    local commits
    commits="$(git log --pretty=format:'%h|%s' "${from_ref}..${TO_REF}" 2>/dev/null || true)"

    if [[ -z "$commits" ]]; then
        echo "No commits found between ${from_ref} and ${TO_REF}" >&2
        exit 0
    fi

    # Buckets
    local added=() fixed=() changed=() removed=()

    while IFS='|' read -r hash subject; do
        local category
        category="$(categorize "$subject")"
        local clean
        clean="$(clean_message "$subject")"
        local entry="- ${clean} (\`${hash}\`)"

        case "$category" in
            Added)   added+=("$entry") ;;
            Fixed)   fixed+=("$entry") ;;
            Changed) changed+=("$entry") ;;
            Removed) removed+=("$entry") ;;
        esac
    done <<< "$commits"

    # Build output
    local date_str
    date_str="$(date +%Y-%m-%d)"
    local out=""

    out+="# Changelog"$'\n\n'
    out+="## [${VERSION}] - ${date_str}"$'\n\n'

    if [[ ${#added[@]} -gt 0 ]]; then
        out+="### Added"$'\n\n'
        for line in "${added[@]}"; do out+="${line}"$'\n'; done
        out+=$'\n'
    fi

    if [[ ${#fixed[@]} -gt 0 ]]; then
        out+="### Fixed"$'\n\n'
        for line in "${fixed[@]}"; do out+="${line}"$'\n'; done
        out+=$'\n'
    fi

    if [[ ${#changed[@]} -gt 0 ]]; then
        out+="### Changed"$'\n\n'
        for line in "${changed[@]}"; do out+="${line}"$'\n'; done
        out+=$'\n'
    fi

    if [[ ${#removed[@]} -gt 0 ]]; then
        out+="### Removed"$'\n\n'
        for line in "${removed[@]}"; do out+="${line}"$'\n'; done
        out+=$'\n'
    fi

    # Output
    if [[ -n "$OUTPUT" ]]; then
        echo "$out" > "$OUTPUT"
        echo "Changelog written to ${OUTPUT}" >&2
    else
        echo "$out"
    fi
}

main
