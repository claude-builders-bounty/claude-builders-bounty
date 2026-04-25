#!/usr/bin/env bash
#
# changelog.sh — Generate a structured CHANGELOG.md from git history.
#
# Usage:
#   bash changelog.sh              # generate from last tag to HEAD
#   bash changelog.sh v1.0.0       # generate from a specific tag
#   bash changelog.sh --all        # generate full history (all tags)
#
# Auto-categorizes commits into: Added / Fixed / Changed / Removed
#

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || { echo "Error: not inside a git repository" >&2; exit 1; })"
OUTPUT="${REPO_ROOT}/CHANGELOG.md"

# ── helpers ──────────────────────────────────────────────────────────────────

# Strip conventional-commit prefix (e.g. "feat:", "fix(core):") then classify.
# Supports both plain subjects and conventional-commit format.
classify() {
    local subject="$1"

    # Strip conventional-commit scope prefix: "feat(scope):" -> "feat:", "fix:" stays
    local stripped
    stripped="$(echo "$subject" | sed -E 's/^[a-z]+\([^)]*\)://')"

    # Build a single string to test: concatenate original + stripped
    local combined
    combined="$(echo "$subject $stripped" | tr '[:upper:]' '[:lower:]')"

    if echo "$combined" | grep -qiE '(^| )add\b|(^| )create\b|(^| )introduce\b|(^| )implement\b|(^| )support\b|(^| )new\b|^feat\b|(^| )added\b'; then
        echo "Added"
    elif echo "$combined" | grep -qiE '(^| )fix\b|(^| )repair\b|(^| )resolve\b|(^| )correct\b|(^| )patch\b|(^| )bugfix\b|(^| )hotfix\b|(^| )close\b|(^| )handle\b|fixed\b'; then
        echo "Fixed"
    elif echo "$combined" | grep -qiE '(^| )remove\b|(^| )delete\b|(^| )drop\b|(^| )eliminate\b|(^| )deprecate\b|(^| )strip\b|removed\b'; then
        echo "Removed"
    else
        echo "Changed"
    fi
}

# Build changelog body for a commit range.
build_section() {
    local range="$1"
    local version="$2"
    local date="$3"

    local log
    log="$(git -C "$REPO_ROOT" log "$range" --pretty=format:"%h||%s" --no-merges 2>/dev/null || true)"
    [ -z "$log" ] && return 0

    printf "## [%s] - %s\n\n" "$version" "$date"

    local added="" fixed="" changed="" removed=""
    local hash subject cat bullet nl
    nl=$'\n'

    while IFS= read -r line; do
        [ -z "$line" ] && continue
        hash="${line%%||*}"
        subject="${line#*||}"

        cat="$(classify "$subject")"
        bullet="- $subject ($hash)"

        case "$cat" in
            Added)   added="${added}${bullet}${nl}" ;;
            Fixed)   fixed="${fixed}${bullet}${nl}" ;;
            Removed) removed="${removed}${bullet}${nl}" ;;
            *)       changed="${changed}${bullet}${nl}" ;;
        esac
    done <<< "$log"

    [ -n "$added" ]   && { printf "### Added\n\n%s\n" "$added"; }
    [ -n "$fixed" ]   && { printf "### Fixed\n\n%s\n" "$fixed"; }
    [ -n "$changed" ] && { printf "### Changed\n\n%s\n" "$changed"; }
    [ -n "$removed" ] && { printf "### Removed\n\n%s\n" "$removed"; }
}

# ── main ─────────────────────────────────────────────────────────────────────

main() {
    cd "$REPO_ROOT"

    local arg="${1:-}"
    local today
    today="$(date +%Y-%m-%d)"

    {
        printf "# Changelog\n\n"
        printf "All notable changes to this project will be documented in this file.\n\n"

        local prev_tag
        prev_tag="$(git describe --tags --abbrev=0 HEAD 2>/dev/null || true)"

        if [ "$arg" = "--all" ]; then
            local tags
            tags="$(git tag --sort=-version:refname 2>/dev/null || true)"

            if [ -n "$tags" ]; then
                local newest
                newest="$(echo "$tags" | head -n1)"
                build_section "$newest..HEAD" "Unreleased" "$today"

                local prev=""
                while IFS= read -r tag; do
                    if [ -n "$prev" ]; then
                        local t_date
                        t_date="$(git log -1 --format=%ai "$prev" 2>/dev/null | cut -d' ' -f1 || echo "$today")"
                        build_section "$tag..$prev" "$prev" "$t_date"
                    fi
                    prev="$tag"
                done <<< "$tags"

                local oldest
                oldest="$(echo "$tags" | tail -n1)"
                local oldest_date
                oldest_date="$(git log -1 --format=%ai "$oldest" 2>/dev/null | cut -d' ' -f1 || echo "$today")"
                build_section "$(git rev-list --max-parents=0 HEAD | head -n1)..$oldest" "$oldest" "$oldest_date"
            else
                build_section "$(git rev-list --max-parents=0 HEAD | head -n1)..HEAD" "Unreleased" "$today"
            fi
        else
            local from_tag="${arg:-$prev_tag}"
            if [ -n "$from_tag" ]; then
                build_section "$from_tag..HEAD" "Unreleased" "$today"
            else
                build_section "$(git rev-list --max-parents=0 HEAD | head -n1)..HEAD" "Unreleased" "$today"
            fi
        fi
    } > "$OUTPUT"

    echo "✅  CHANGELOG.md generated at $OUTPUT"
}

main "$@"
