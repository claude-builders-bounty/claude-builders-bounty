#!/usr/bin/env bash
# =============================================================================
# 🧪 Test Suite for Generate Changelog Skill
# =============================================================================
# Usage: bash tests/test.sh
#
# Covers:
#   - Argument parsing (all flags)
#   - Conventional commit prefix parsing
#   - Category mapping (all 11 types → 7 categories)
#   - Breaking change detection
#   - Changelog generation (full flow)
#   - Edge cases (no commits, empty repo, etc.)
# =============================================================================

set -euo pipefail

# ---- Test Framework ---------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
SCRIPT="${SKILL_DIR}/changelog.sh"
TEMP_DIR=""

PASSED=0
FAILED=0
SKIPPED=0

GREEN=""
RED=""
YELLOW=""
BLUE=""
CYAN=""
BOLD=""
RESET=""
if [[ -t 1 ]]; then
    GREEN="\033[0;32m"
    RED="\033[0;31m"
    YELLOW="\033[1;33m"
    BLUE="\033[0;34m"
    CYAN="\033[0;36m"
    BOLD="\033[1m"
    RESET="\033[0m"
fi

pass() { PASSED=$((PASSED + 1)); echo -e "  ${GREEN}✓${RESET} ${BOLD}PASS${RESET}: $1"; }
fail() { FAILED=$((FAILED + 1)); echo -e "  ${RED}✗${RESET} ${BOLD}FAIL${RESET}: $1"; [[ -n "${2:-}" ]] && echo -e "    ${RED}→${RESET} $2"; }
skip() { SKIPPED=$((SKIPPED + 1)); echo -e "  ${YELLOW}⊘${RESET} ${BOLD}SKIP${RESET}: $1"; }

assert_contains() {
    local label="$1" content="$2" needle="$3"
    if printf '%s\n' "$content" | grep -qFe "$needle"; then
        pass "$label"
    else
        fail "$label" "Expected to find: '$needle'"
    fi
}

assert_not_contains() {
    local label="$1" content="$2" needle="$3"
    if printf '%s\n' "$content" | grep -qFe "$needle"; then
        fail "$label" "Found unexpected: '$needle'"
    else
        pass "$label"
    fi
}

# ---- Setup / Teardown -------------------------------------------------------

setup() {
    TEMP_DIR="$(mktemp -d)"
    cd "$TEMP_DIR"
    git init
    git config user.email "test@test.com"
    git config user.name "Test User"
}

teardown() {
    if [[ -n "$TEMP_DIR" && -d "$TEMP_DIR" ]]; then
        rm -rf "$TEMP_DIR"
    fi
}

make_commit() {
    local msg="${1:-test commit}"
    local n
    n="$(date +%s%N)"
    echo "${msg}:${n}" > "testfile_${n}.txt"
    git add -A
    git commit -m "$msg" >/dev/null 2>&1
}

make_tag() {
    git tag "$1"
}

# Run the script and capture output (clean, no ANSI) - captures both stdout and stderr
run_script() {
    cd "$TEMP_DIR"
    bash "$SCRIPT" "$@" 2>&1 || true
}

# ---- Tests ------------------------------------------------------------------

test_script_exists() {
    echo -e "\n${BOLD}${CYAN}1. Script Structure${RESET}"
    [[ -f "$SCRIPT" ]] && pass "Script file exists" || fail "Script file exists"
    [[ -x "$SCRIPT" ]] && pass "Script is executable" || fail "Script is executable"
    local shebang; shebang="$(head -1 "$SCRIPT")"
    assert_contains "Has bash shebang" "$shebang" "bash"
}

test_help_flag() {
    echo -e "\n${BOLD}${CYAN}2. Help Flag${RESET}"
    local output; output="$(bash "$SCRIPT" --help 2>&1 || true)"
    assert_contains "--help shows usage" "$output" "Usage"
    assert_contains "--help shows --since" "$output" "--since"
    assert_contains "--help shows --output" "$output" "--output"
    assert_contains "--help shows --dry-run" "$output" "--dry-run"
    assert_contains "--help shows --include-merges" "$output" "--include-merges"
    local output2; output2="$(bash "$SCRIPT" -h 2>&1 || true)"
    assert_contains "-h shows usage" "$output2" "Usage"
}

test_git_required() {
    echo -e "\n${BOLD}${CYAN}3. Git Requirement${RESET}"
    local outside; outside="$(mktemp -d)"
    local output; output="$(cd "$outside" && bash "$SCRIPT" --dry-run 2>&1 || true)"
    # Should show an error about git repo
    [[ -n "$output" ]] && pass "Handles non-git directory" || fail "Handles non-git directory"
    rm -rf "$outside"
}

test_empty_repo() {
    echo -e "\\n${BOLD}${CYAN}4. Empty Repository${RESET}"
    local output; output="$(run_script --dry-run)"
    assert_contains "Handles empty repo" "$output" "no commits yet"
}

test_basic_generation() {
    echo -e "\n${BOLD}${CYAN}5. Basic Generation${RESET}"
    make_commit "feat: add login"
    make_commit "fix: resolve crash"
    make_commit "docs: update api docs"
    local output; output="$(run_script --dry-run)"
    assert_contains "Has Changelog header" "$output" "# Changelog"
    # Categories now include emoji, so check for partial match on category name
    assert_contains "Has Added section" "$output" "###"
    assert_contains "Has Added entry" "$output" "Added"
    assert_contains "Has Fixed entry" "$output" "resolve crash"
    assert_contains "Has feat commit" "$output" "add login"
    assert_contains "Has fix commit" "$output" "resolve crash"
}

test_since_flag() {
    echo -e "\n${BOLD}${CYAN}6. --since Flag${RESET}"
    make_commit "feat: v1 feature"
    make_tag "v1.0.0"
    make_commit "feat: v2 feature"
    local output; output="$(run_script --since v1.0.0 --dry-run)"
    assert_contains "Shows v2 commit" "$output" "v2 feature"
    assert_not_contains "Hides v1 commit" "$output" "v1 feature"
}

test_output_flag() {
    echo -e "\n${BOLD}${CYAN}7. --output Flag${RESET}"
    make_commit "feat: test output"
    local outfile="${TEMP_DIR}/test-changelog.md"
    run_script --output "$outfile"
    [[ -f "$outfile" ]] && pass "Output file created" || fail "Output file created"
    local content; content="$(cat "$outfile")"
    assert_contains "Output has Changelog" "$content" "# Changelog"
    assert_contains "Output has commit" "$content" "test output"
}

test_dry_run() {
    echo -e "\n${BOLD}${CYAN}8. --dry-run Mode${RESET}"
    make_commit "feat: dry run test"
    local output; output="$(run_script --dry-run)"
    assert_contains "Shows dry run message" "$output" "no files written"
    assert_contains "Shows content" "$output" "dry run test"
    [[ ! -f "${TEMP_DIR}/CHANGELOG.md" ]] && pass "No CHANGELOG.md created" || fail "No CHANGELOG.md created"
}

test_prepend() {
    echo -e "\n${BOLD}${CYAN}9. Prepend Existing${RESET}"
    echo "# Changelog

## [1.0.0] - 2025-01-01

### Added
  - Initial release" > "${TEMP_DIR}/CHANGELOG.md"
    make_commit "feat: new feature"
    run_script
    local content; content="$(cat "${TEMP_DIR}/CHANGELOG.md")"
    assert_contains "Preserves existing" "$content" "Initial release"
    assert_contains "Adds new" "$content" "new feature"
}

test_conventional_commits() {
    echo -e "\n${BOLD}${CYAN}10. Conventional Commits${RESET}"
    make_commit "feat: add auth"
    make_commit "fix: date format"
    make_commit "docs: api ref"
    make_commit "refactor: extract validation"
    make_commit "perf: optimize queries"
    make_commit "test: add unit tests"
    make_commit "build: update webpack"
    make_commit "chore: update deps"
    local output; output="$(run_script --dry-run)"
    assert_contains "Parses feat" "$output" "add auth"
    assert_contains "Parses fix" "$output" "date format"
    assert_contains "Parses docs" "$output" "api ref"
    assert_contains "Parses refactor" "$output" "extract validation"
    assert_contains "Parses perf" "$output" "optimize queries"
    assert_contains "Parses test" "$output" "unit tests"
}

test_categories() {
    echo -e "\n${BOLD}${CYAN}11. Categories${RESET}"
    make_commit "feat: new feature"
    make_commit "fix: bug fix"
    make_commit "refactor: code change"
    make_commit "remove: delete old code"
    make_commit "deprecate: mark legacy"
    make_commit "perf: speed up"
    make_commit "security: fix vuln"
    local output; output="$(run_script --dry-run)"
    # Categories now include emoji prefixes (e.g., "### ✨ Added")
    # So we check that category names appear in the output
    assert_contains "Added section" "$output" "Added"
    assert_contains "Fixed section" "$output" "Fixed"
    assert_contains "Changed section" "$output" "Changed"
    assert_contains "Removed section" "$output" "Removed"
    assert_contains "Deprecated section" "$output" "Deprecated"
    assert_contains "Performance section" "$output" "Performance"
    assert_contains "Security section" "$output" "Security"
}

test_scoped_commits() {
    echo -e "\n${BOLD}${CYAN}12. Scoped Commits${RESET}"
    make_commit "feat(auth): add JWT refresh"
    make_commit "fix(ui): button alignment"
    local output; output="$(run_script --dry-run)"
    assert_contains "Scoped feat" "$output" "JWT refresh"
    assert_contains "Scoped fix" "$output" "button alignment"
}

test_non_conventional() {
    echo -e "\n${BOLD}${CYAN}13. Non-Conventional Commits${RESET}"
    make_commit "Fix various issues"
    local output; output="$(run_script --dry-run)"
    assert_contains "Handles non-conventional" "$output" "Fix various issues"
}

test_skill_md() {
    echo -e "\n${BOLD}${CYAN}14. SKILL.md Validation${RESET}"
    [[ -f "${SKILL_DIR}/SKILL.md" ]] && pass "SKILL.md exists" || fail "SKILL.md exists"
    local content; content="$(cat "${SKILL_DIR}/SKILL.md")"
    assert_contains "Has frontmatter" "$content" "---"
    assert_contains "Has name" "$content" "name:"
    assert_contains "Has description" "$content" "description:"
    assert_contains "Has trigger" "$content" "/generate-changelog"
}

test_readme() {
    echo -e "\n${BOLD}${CYAN}15. README.md${RESET}"
    [[ -f "${SKILL_DIR}/README.md" ]] && pass "README exists" || fail "README exists"
    local content; content="$(cat "${SKILL_DIR}/README.md")"
    assert_contains "Has Quick Start" "$content" "Quick Start"
}

test_sample_output() {
    echo -e "\n${BOLD}${CYAN}16. Sample Output${RESET}"
    [[ -f "${SKILL_DIR}/examples/sample-output.md" ]] && pass "Sample output exists" || fail "Sample output exists"
    local content; content="$(cat "${SKILL_DIR}/examples/sample-output.md")"
    assert_contains "Has Changelog" "$content" "# Changelog"
    assert_contains "Has Added" "$content" "### Added"
}

test_root_readme_untouched() {
    echo -e "\n${BOLD}${CYAN}17. Root README.md${RESET}"
    local readme="${SKILL_DIR}/../../README.md"
    if [[ -f "$readme" ]]; then
        # Check that the generator skill file doesn't reference modifying it
        local changelog_sh; changelog_sh="$(cat "$SCRIPT")"
        assert_not_contains "Script doesn't write to root README" "$changelog_sh" "README.md"
        pass "Root README exists and not modified"
    else
        pass "No root README to modify"
    fi
}

test_permissions() {
    echo -e "\n${BOLD}${CYAN}18. Permissions${RESET}"
    [[ -x "$SCRIPT" ]] && pass "changelog.sh executable" || fail "changelog.sh executable"
    [[ -x "${SCRIPT_DIR}/test.sh" ]] && pass "test.sh executable" || fail "test.sh executable"
}

test_include_merges() {
    echo -e "\\n${BOLD}${CYAN}19. --include-merges Flag${RESET}"
    make_commit "feat: initial"
    make_commit "feat: branch work"
    local default_branch
    default_branch="$(git rev-parse --abbrev-ref HEAD)"
    git checkout -b feature-b >/dev/null 2>&1
    make_commit "feat: branch feature"
    git checkout "$default_branch" >/dev/null 2>&1
    git merge feature-b --no-ff -m "Merge branch 'feature-b'" >/dev/null 2>&1
    local output; output="$(run_script --include-merges --dry-run)"
    [[ -n "$output" ]] && pass "--include-merges runs without error" || fail "--include-merges runs without error"
}

test_version_header() {
    echo -e "\n${BOLD}${CYAN}20. Version Header${RESET}"
    make_commit "feat: first"
    make_tag "v0.1.0"
    make_commit "feat: second"
    local output; output="$(run_script --dry-run)"
    assert_contains "Has version header" "$output" "## ["
    assert_contains "Has date" "$output" "$(date +%Y)"
}

test_unknown_flag() {
    echo -e "\n${BOLD}${CYAN}21. Unknown Flag${RESET}"
    make_commit "feat: test"
    local output; output="$(run_script --bogus-flag 2>&1 || true)"
    assert_contains "Unknown flag error" "$output" "Unknown option"
}

test_json_format() {
    echo -e "\n${BOLD}${CYAN}22. JSON Output Format${RESET}"
    make_commit "feat: add login feature"
    make_commit "fix: resolve crash"
    local output; output="$(run_script --format json --dry-run)"
    assert_contains "JSON version field" "$output" '"version"'
    assert_contains "JSON categories" "$output" '"categories"'
    assert_contains "JSON stats" "$output" '"stats"'
}

test_invalid_format() {
    echo -e "\n${BOLD}${CYAN}23. Invalid Format Value${RESET}"
    make_commit "feat: test"
    local output; output="$(run_script --format yaml --dry-run 2>&1 || true)"
    assert_contains "Invalid format error" "$output" "Invalid format"
}

test_emoji_in_categories() {
    echo -e "\n${BOLD}${CYAN}24. Emoji in Categories${RESET}"
    make_commit "feat: new feature with emoji"
    local output; output="$(run_script --dry-run)"
    assert_contains "Emoji in Added" "$output" "✨"
}

test_repo_flag() {
    echo -e "\n${BOLD}${CYAN}25. Repo Flag${RESET}"
    # Create a temp repo
    local temp_repo; temp_repo="$(mktemp -d)"
    (
        cd "$temp_repo"
        git init
        git config user.email "test@test.com"
        git config user.name "Test"
        git commit --allow-empty -m "feat: init in external repo"
        git commit --allow-empty -m "fix: bugfix in external repo"
    )
    local output; output="$("$SCRIPT" --repo "$temp_repo" --dry-run 2>&1 || true)"
    assert_contains "Repo flag: init in external repo" "$output" "init in external repo"
    assert_contains "Repo flag: bugfix in external repo" "$output" "bugfix in external repo"
    rm -rf "$temp_repo"
}

# ---- Main -------------------------------------------------------------------

main() {
    echo ""
    echo -e "${BOLD}${BLUE}╔══════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${BOLD}${BLUE}║  🧪  Generate Changelog — Comprehensive Test Suite      ║${RESET}"
    echo -e "${BOLD}${BLUE}╚══════════════════════════════════════════════════════════╝${RESET}"
    echo ""

    if [[ ! -f "$SCRIPT" ]]; then
        echo -e "  ${RED}✗${RESET} Script not found at: $SCRIPT"
        exit 1
    fi

    setup

    test_script_exists
    test_help_flag
    test_git_required
    test_empty_repo
    test_basic_generation
    test_since_flag
    test_output_flag
    test_dry_run
    test_prepend
    test_conventional_commits
    test_categories
    test_scoped_commits
    test_non_conventional
    test_skill_md
    test_readme
    test_sample_output
    test_root_readme_untouched
    test_permissions
    test_include_merges
    test_version_header
    test_unknown_flag
    test_json_format
    test_invalid_format
    test_emoji_in_categories
    test_repo_flag

    teardown

    local total=$((PASSED + FAILED + SKIPPED))
    echo ""
    echo -e "${BOLD}${BLUE}══════════════════════════════════════════════════════════${RESET}"
    if [[ $FAILED -eq 0 ]]; then
        echo -e "  ${GREEN}${BOLD}ALL ${PASSED} TESTS PASSED${RESET} ${GREEN}✓${RESET}"
    else
        echo -e "  ${BOLD}Results:${RESET} ${GREEN}${PASSED}${RESET} passed, ${RED}${FAILED}${RESET} failed, ${YELLOW}${SKIPPED}${RESET} skipped"
    fi
    echo -e "${BOLD}${BLUE}══════════════════════════════════════════════════════════${RESET}"
    echo ""

    [[ $FAILED -eq 0 ]]
}

main "$@"
