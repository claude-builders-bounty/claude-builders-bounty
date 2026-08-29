#!/usr/bin/env bash
# Generate CHANGELOG.md from git history since the last tag
# Part of the generate-changelog skill

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
error() { echo -e "${RED}Error: $*${NC}" >&2; exit 1; }
warn() { echo -e "${YELLOW}Warning: $*${NC}" >&2; }
info() { echo -e "${GREEN}$*${NC}"; }

# 1. Validate git repository
if ! git rev-parse --git-dir >/dev/null 2>&1; then
    error "Not a git repository. Run this command from within a git repository."
fi

# 2. Find the latest tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [[ -n "$LAST_TAG" ]]; then
    info "Found latest tag: $LAST_TAG"
    COMMIT_RANGE="${LAST_TAG}..HEAD"
else
    warn "No tags found. Using all commits from repository history."
    COMMIT_RANGE="HEAD"
fi

# 3. Get commits since last tag using a temp file to handle NUL bytes
# Use NUL byte (%x00) as delimiter - cannot appear in commit messages
# Format: hash<NUL>subject<NUL>body
COMMITS_FILE=$(mktemp)
trap 'rm -f "$COMMITS_FILE"' EXIT

if [[ "$COMMIT_RANGE" == "HEAD" ]]; then
    git log --pretty=format:"%h%x00%s%x00%b%x00" --reverse HEAD 2>/dev/null > "$COMMITS_FILE" || true
else
    git log --pretty=format:"%h%x00%s%x00%b%x00" --reverse "${COMMIT_RANGE}" 2>/dev/null > "$COMMITS_FILE" || true
fi

if [[ ! -s "$COMMITS_FILE" ]]; then
    info "No commits found since last tag."
fi

# 4. Categorize commits
# Arrays to hold categorized commits
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()

# Classification function - deterministic, handles conventional commits properly
classify_commit() {
    local hash="$1"
    local subject="$2"
    local body="$3"
    local full_msg="${subject} ${body}"
    local lower_subject="${subject,,}"
    local lower_full_msg="${full_msg,,}"

    # ============================================================
    # 1. CONVENTIONAL COMMITS PARSING (highest priority)
    # Parse: type(scope): subject  or  type: subject
    # ============================================================
    # Extract conventional type from subject line
    # Matches: feat:, feat(scope):, fix:, etc. (case-insensitive)
    local conv_type=""
    # Use case statement to match known conventional types at start of subject
    local subject_copy="$lower_subject"
    # List of known conventional types in priority order
    local known_types=("feat" "feature" "fix" "bug" "hotfix" "patch" "refactor" "refact" "perf" "optimize" "improve" "enhance" "style" "format" "test" "tests" "docs" "doc" "chore" "build" "ci" "cd" "remove" "delete" "drop" "rm" "revert" "breaking")
    for t in "${known_types[@]}"; do
        # Check if subject starts with type followed by : or (scope):
        if [[ "$subject_copy" == "${t}:"* ]] || [[ "$subject_copy" == "${t}("*": "* ]]; then
            conv_type="$t"
            break
        fi
    done

    # Map conventional type to category (deterministic mapping)
    case "$conv_type" in
        fix|bug|hotfix|patch)
            echo "fixed"
            return
            ;;
        remove|delete|drop|rm)
            echo "removed"
            return
            ;;
        feat|feature)
            echo "added"
            return
            ;;
        refactor|refact|perf|optimize|improve|enhance|style|format|test|tests|docs|doc|chore|build|ci|cd)
            echo "changed"
            return
            ;;
        revert)
            echo "removed"
            return
            ;;
        breaking)
            echo "changed"
            return
            ;;
    esac

    # ============================================================
    # 2. MULTI-INTENT DETECTION (check for multiple conventional types)
    # If subject contains multiple type-like prefixes, use priority order
    # Priority: fix > remove > feat > refactor/perf/style/test/docs/chore > breaking
    # ============================================================
    local multi_category=""
    # Check for conventional-like prefixes at word boundaries
    # Priority order array
    local priority_types=("fix" "bug" "hotfix" "patch" "remove" "delete" "drop" "rm" "feat" "feature" "refactor" "refact" "perf" "optimize" "improve" "enhance" "style" "format" "test" "tests" "docs" "doc" "chore" "build" "ci" "cd" "revert" "breaking")

    for ptype in "${priority_types[@]}"; do
        # Word-boundary match for type at start or after common separators
        # Use string matching instead of complex regex
        local pattern1="^${ptype}:"   # at start with :
        local pattern2="^${ptype} "   # at start with space
        local pattern3=":${ptype}:"   # after : with :
        local pattern4=":${ptype} "   # after : with space
        local pattern5=";${ptype}:"   # after ; with :
        local pattern6=";${ptype} "   # after ; with space
        local pattern7=",${ptype}:"   # after , with :
        local pattern8=",${ptype} "   # after , with space

        if [[ "$lower_subject" == ${pattern1}* ]] || [[ "$lower_subject" == ${pattern2}* ]] || \
           [[ "$lower_subject" == *${pattern3}* ]] || [[ "$lower_subject" == *${pattern4}* ]] || \
           [[ "$lower_subject" == *${pattern5}* ]] || [[ "$lower_subject" == *${pattern6}* ]] || \
           [[ "$lower_subject" == *${pattern7}* ]] || [[ "$lower_subject" == *${pattern8}* ]]; then
            case "$ptype" in
                fix|bug|hotfix|patch) multi_category="fixed"; break ;;
                remove|delete|drop|rm) multi_category="removed"; break ;;
                feat|feature) multi_category="added"; break ;;
                *) multi_category="changed"; break ;;
            esac
        fi
    done

    if [[ -n "$multi_category" ]]; then
        echo "$multi_category"
        return
    fi

    # ============================================================
    # 3. BREAKING CHANGE DETECTION (in body/footer)
    # ============================================================
    if [[ "$lower_full_msg" =~ (^|\\n)breaking[[:space:]]change: ]]; then
        echo "changed"
        return
    fi

    # ============================================================
    # 4. PRECISE KEYWORD FALLBACK (subject only, word boundaries)
    # Only check subject line, not full message
    # ============================================================
    local lower_subject_trimmed="${lower_subject#"${lower_subject%%[![:space:]]*}"}"  # ltrim

    # Added: new functionality keywords at word boundaries
    if [[ "$lower_subject_trimmed" =~ ^(add|create|implement|introduce|new)([[:space:]]|$) ]] || \
       [[ "$lower_subject_trimmed" =~ (^|[:,;]\\s+)(add|create|implement|introduce|new)([[:space:]]|$) ]]; then
        echo "added"
        return
    fi

    # Fixed: bug fix keywords
    if [[ "$lower_subject_trimmed" =~ ^(fix|bug|patch|hotfix|resolve|correct|repair)([[:space:]]|$) ]] || \
       [[ "$lower_subject_trimmed" =~ (^|[:,;]\\s+)(fix|bug|patch|hotfix|resolve|correct|repair)([[:space:]]|$) ]]; then
        echo "fixed"
        return
    fi

    # Removed: deletion keywords
    if [[ "$lower_subject_trimmed" =~ ^(remove|delete|drop|deprecate|eliminate)([[:space:]]|$) ]] || \
       [[ "$lower_subject_trimmed" =~ (^|[:,;]\\s+)(remove|delete|drop|deprecate|eliminate)([[:space:]]|$) ]]; then
        echo "removed"
        return
    fi

    # Changed: refactoring/update keywords (broadest category, last resort before default)
    if [[ "$lower_subject_trimmed" =~ ^(update|change|modify|improve|enhance|optimize|refactor|migrate|upgrade|reorganize|restructure)([[:space:]]|$) ]] || \
       [[ "$lower_subject_trimmed" =~ (^|[:,;]\\s+)(update|change|modify|improve|enhance|optimize|refactor|migrate|upgrade|reorganize|restructure)([[:space:]]|$) ]]; then
        echo "changed"
        return
    fi

    # ============================================================
    # 5. DEFAULT
    # ============================================================
    echo "changed"
}

# Process commits using NUL delimiter from temp file
# Each commit has 3 NUL-separated fields: hash, subject, body
# (format: %h%x00%s%x00%b%x00 produces exactly 3 NULs per commit)
# Note: git log adds a newline between commits after the 3rd NUL
# For empty body: hash\0subject\0\0\n  (3 NULs then newline)
# For non-empty body: hash\0subject\0body\0\n
while IFS= read -r -d '' hash; do
    [[ -z "$hash" ]] && continue

    # Read subject (consumes 1st NUL)
    IFS= read -r -d '' subject || subject=""

    # Read body (consumes 2nd NUL) - body ends at the 3rd NUL (from %x00 after %b)
    IFS= read -r -d '' body || body=""

    # Consume the trailing newline after the 3rd NUL (git log adds \n between commits)
    # The body read already consumed the 3rd NUL, so next char is \n
    IFS= read -r -n 1 _newline || true

    category=$(classify_commit "$hash" "$subject" "$body")
    case "$category" in
        added) ADDED+=("- $subject ($hash)") ;;
        fixed) FIXED+=("- $subject ($hash)") ;;
        changed) CHANGED+=("- $subject ($hash)") ;;
        removed) REMOVED+=("- $subject ($hash)") ;;
    esac
done < "$COMMITS_FILE"

# 5. Generate CHANGELOG.md
DATE=$(date +%Y-%m-%d)
CHANGELOG_FILE="CHANGELOG.md"
BACKUP_FILE="${CHANGELOG_FILE}.backup"

# Build new [Unreleased] section content
UNRELEASED_CONTENT="## [Unreleased] - ${DATE}

### Added
$(if [[ ${#ADDED[@]} -eq 0 ]]; then echo "- (none)"; else printf '%s\n' "${ADDED[@]}"; fi)

### Fixed
$(if [[ ${#FIXED[@]} -eq 0 ]]; then echo "- (none)"; else printf '%s\n' "${FIXED[@]}"; fi)

### Changed
$(if [[ ${#CHANGED[@]} -eq 0 ]]; then echo "- (none)"; else printf '%s\n' "${CHANGED[@]}"; fi)

### Removed
$(if [[ ${#REMOVED[@]} -eq 0 ]]; then echo "- (none)"; else printf '%s\n' "${REMOVED[@]}"; fi)
"

# Handle existing CHANGELOG.md
if [[ -f "$CHANGELOG_FILE" ]]; then
    info "Existing CHANGELOG.md found. Creating backup at ${BACKUP_FILE}"
    cp "$CHANGELOG_FILE" "$BACKUP_FILE"

    # Check if there's an existing [Unreleased] section to replace
    if grep -q '^## \[Unreleased\]' "$CHANGELOG_FILE"; then
        # Replace the existing [Unreleased] section
        # Use awk to replace from "## [Unreleased]" to the next "## [" or end of file
        awk -v new_content="$UNRELEASED_CONTENT" '
            BEGIN { in_unreleased=0; printed=0 }
            /^## \[Unreleased\]/ {
                if (!printed) {
                    print new_content
                    printed=1
                }
                in_unreleased=1
                next
            }
            /^## \[/ && in_unreleased {
                in_unreleased=0
            }
            !in_unreleased { print }
        ' "$CHANGELOG_FILE" > "${CHANGELOG_FILE}.tmp" && mv "${CHANGELOG_FILE}.tmp" "$CHANGELOG_FILE"
        info "CHANGELOG.md [Unreleased] section updated"
    else
        # No [Unreleased] section, insert new [Unreleased] section after header
        EXISTING_CONTENT=$(cat "$CHANGELOG_FILE")
        # Check if existing content already has "# Changelog" header
        if echo "$EXISTING_CONTENT" | head -1 | grep -q '^# Changelog'; then
            # Already has header, insert [Unreleased] after header, before first version
            # Use awk to insert after the first line (header)
            awk -v new_content="$UNRELEASED_CONTENT" '
                NR == 1 { print; print ""; print new_content; print ""; next }
                { print }
            ' "$CHANGELOG_FILE" > "${CHANGELOG_FILE}.tmp" && mv "${CHANGELOG_FILE}.tmp" "$CHANGELOG_FILE"
        else
            # No header, add it
            echo "# Changelog" > "$CHANGELOG_FILE"
            echo "" >> "$CHANGELOG_FILE"
            echo "$UNRELEASED_CONTENT" >> "$CHANGELOG_FILE"
            echo "" >> "$CHANGELOG_FILE"
            echo "$EXISTING_CONTENT" >> "$CHANGELOG_FILE"
        fi
        info "CHANGELOG.md updated with new [Unreleased] section (previous content preserved)"
    fi
else
    # Create new CHANGELOG.md
    echo "# Changelog" > "$CHANGELOG_FILE"
    echo "" >> "$CHANGELOG_FILE"
    echo "$UNRELEASED_CONTENT" >> "$CHANGELOG_FILE"
    info "CHANGELOG.md created"
fi

# Summary
info "Summary:"
info "  Added:   ${#ADDED[@]}"
info "  Fixed:   ${#FIXED[@]}"
info "  Changed: ${#CHANGED[@]}"
info "  Removed: ${#REMOVED[@]}"
info "Done!"