#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'USAGE'
Generate a structured CHANGELOG.md from git history.

Usage:
  bash changelog.sh [--output CHANGELOG.md]
  bash changelog.sh --stdout
  bash changelog.sh --from <ref> [--output CHANGELOG.md]

Options:
  --from <ref>       Use <ref> instead of the latest git tag as the lower bound.
  -o, --output FILE  Write changelog to FILE. Defaults to CHANGELOG.md.
  --stdout          Print changelog instead of writing a file.
  -h, --help        Show this help.
USAGE
}

output_file="CHANGELOG.md"
stdout=false
base_ref=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --from)
            base_ref="${2:-}"
            if [[ -z "$base_ref" ]]; then
                echo "error: --from requires a ref" >&2
                exit 1
            fi
            shift 2
            ;;
        -o|--output)
            output_file="${2:-}"
            if [[ -z "$output_file" ]]; then
                echo "error: --output requires a file path" >&2
                exit 1
            fi
            shift 2
            ;;
        --stdout)
            stdout=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "error: unknown option: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "error: changelog.sh must be run inside a git repository" >&2
    exit 1
fi

if git remote get-url origin >/dev/null 2>&1; then
    git fetch --tags --quiet >/dev/null 2>&1 || true
fi

if [[ -n "$base_ref" ]]; then
    if ! git rev-parse --verify --quiet "${base_ref}^{commit}" >/dev/null; then
        echo "error: --from ref does not exist or is not a commit: $base_ref" >&2
        exit 1
    fi
    range="${base_ref}..HEAD"
    source_note="Commits since ref \`$base_ref\`."
elif last_tag="$(git describe --tags --abbrev=0 2>/dev/null)"; then
    range="${last_tag}..HEAD"
    source_note="Commits since the latest tag \`$last_tag\`."
else
    range="HEAD"
    source_note="Repository has no tags; included all commits."
fi

repo_url="$(git config --get remote.origin.url 2>/dev/null || true)"
if [[ "$repo_url" == git@github.com:* ]]; then
    repo_url="https://github.com/${repo_url#git@github.com:}"
fi
repo_url="${repo_url%.git}"

category_for_subject() {
    local subject_lower prefix
    subject_lower="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
    prefix="${subject_lower%%:*}"
    prefix="${prefix%%!*}"
    prefix="${prefix%%\(*}"

    case "$prefix" in
        feat|feature)
            echo "Added"
            return
            ;;
        fix|bugfix|hotfix)
            echo "Fixed"
            return
            ;;
        remove|removed|delete|deleted|drop|dropped|deprecate|deprecated)
            echo "Removed"
            return
            ;;
        change|changed|refactor|style|perf|performance|docs|doc|test|tests|build|ci|chore|revert)
            echo "Changed"
            return
            ;;
    esac

    if [[ "$subject_lower" == *remove* || "$subject_lower" == *delete* || "$subject_lower" == *drop* || "$subject_lower" == *deprecat* ]]; then
        echo "Removed"
    elif [[ "$subject_lower" == *fix* || "$subject_lower" == *bug* || "$subject_lower" == *patch* ]]; then
        echo "Fixed"
    elif [[ "$subject_lower" == *add* || "$subject_lower" == *new* || "$subject_lower" == *implement* ]]; then
        echo "Added"
    else
        echo "Changed"
    fi
}

clean_subject() {
    local subject="$1"
    local conventional_commit_regex='^[A-Za-z]+(\([^)]*\))?!?:[[:space:]]*(.*)$'

    if [[ "$subject" =~ $conventional_commit_regex && -n "${BASH_REMATCH[2]}" ]]; then
        printf '%s' "${BASH_REMATCH[2]}"
    else
        printf '%s' "$subject"
    fi
}

commit_reference() {
    local hash="$1"
    local short_hash="${hash:0:7}"
    if [[ "$repo_url" == https://github.com/* ]]; then
        printf '[`%s`](%s/commit/%s)' "$short_hash" "$repo_url" "$hash"
    else
        printf '`%s`' "$short_hash"
    fi
}

added=""
fixed=""
changed=""
removed=""

if ! git_output="$(git log --pretty=format:'%H%x1f%s' "$range")"; then
    echo "error: failed to read git history for range: $range" >&2
    exit 1
fi

while IFS=$'\x1f' read -r hash subject || [[ -n "${hash:-}" ]]; do
    [[ -n "${hash:-}" ]] || continue
    category="$(category_for_subject "$subject")"
    message="$(clean_subject "$subject")"
    entry="- ${message} ($(commit_reference "$hash"))"$'\n'

    case "$category" in
        Added) added+="$entry" ;;
        Fixed) fixed+="$entry" ;;
        Changed) changed+="$entry" ;;
        Removed) removed+="$entry" ;;
    esac
done <<< "$git_output"

print_category() {
    local title="$1"
    local entries="$2"

    printf '### %s\n' "$title"
    if [[ -n "$entries" ]]; then
        printf '%s' "$entries"
    else
        printf -- '- No changes.\n'
    fi
    printf '\n'
}

generate_changelog() {
    printf '# Changelog\n\n'
    printf '## [Unreleased] - %s\n\n' "$(date +%F)"
    printf '%s\n\n' "$source_note"
    print_category "Added" "$added"
    print_category "Fixed" "$fixed"
    print_category "Changed" "$changed"
    print_category "Removed" "$removed"
}

if [[ "$stdout" == true ]]; then
    generate_changelog
else
    generate_changelog > "$output_file"
    printf 'Wrote %s\n' "$output_file"
fi
