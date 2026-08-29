#!/usr/bin/env bash
# Comprehensive test suite for generate-changelog skill
# Tests all 10 scenarios with temporary git repositories

# set -euo pipefail  # Disabled to allow all tests to run even if some fail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS=0
FAIL=0

info() { echo -e "${BLUE}[INFO]${NC} $*"; }
pass() { echo -e "${GREEN}[PASS]${NC} $*"; ((PASS++)); }
fail() { echo -e "${RED}[FAIL]${NC} $*"; ((FAIL++)); }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }

# Path to the changelog script (absolute)
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.claude/skills/generate-changelog/changelog.sh"

run_test() {
    local test_name="$1"
    local test_fn="$2"

    info "Running test: $test_name"
    # Create temp directory
    local tmpdir=$(mktemp -d)
    local orig_dir="$PWD"
    pushd "$tmpdir" >/dev/null

    if $test_fn; then
        pass "$test_name"
    else
        fail "$test_name"
    fi

    popd >/dev/null
    rm -rf "$tmpdir"
}

# Test 1: Tag + commits normais
test_tag_and_commits() {
    git init -q
    git config user.email "test@test.com"
    git config user.name "Test User"

    echo "initial" > file.txt
    git add file.txt
    git commit -q -m "initial commit"
    git tag -a v1.0 -m "v1.0"

    echo "feature" > feature.txt
    git add feature.txt
    git commit -q -m "feat: add new feature"

    echo "fix" > fix.txt
    git add fix.txt
    git commit -q -m "fix: resolve bug"

    bash "$SCRIPT_PATH" >/dev/null 2>&1

    # Check CHANGELOG.md
    if grep -q "feat: add new feature" CHANGELOG.md && \
       grep -q "fix: resolve bug" CHANGELOG.md && \
       ! grep -q "initial commit" CHANGELOG.md; then
        return 0
    fi
    cat CHANGELOG.md
    return 1
}

# Test 2: Body multilinha
test_multiline_body() {
    git init -q
    git config user.email "test@test.com"
    git config user.name "Test User"

    echo "initial" > file.txt
    git add file.txt
    git commit -q -m "initial commit"
    git tag -a v1.0 -m "v1.0"

    # Create commit with multi-line body
    git commit -q --allow-empty -m $'feat: add authentication\n\nThis is the first line of the body.\nThis is the second line.\nThis is the third line.'

    bash "$SCRIPT_PATH" >/dev/null 2>&1

    # Should have exactly 1 commit in Added, no phantom commits
    local added_count=$(grep -c "feat: add authentication" CHANGELOG.md || true)
    local total_commits=$(grep -c "^-\|^###" CHANGELOG.md || true)

    if [[ $added_count -eq 1 ]] && [[ $(grep -c "This is the" CHANGELOG.md) -eq 0 ]]; then
        return 0
    fi
    cat CHANGELOG.md
    return 1
}

# Test 3: Pipe no subject
test_pipe_in_subject() {
    git init -q
    git config user.email "test@test.com"
    git config user.name "Test User"

    echo "initial" > file.txt
    git add file.txt
    git commit -q -m "initial commit"
    git tag -a v1.0 -m "v1.0"

    git commit -q --allow-empty -m "refactor: improve auth | token handling"

    bash "$SCRIPT_PATH" >/dev/null 2>&1

    if grep -q "refactor: improve auth | token handling" CHANGELOG.md; then
        return 0
    fi
    cat CHANGELOG.md
    return 1
}

# Test 4: Pipe no body
test_pipe_in_body() {
    git init -q
    git config user.email "test@test.com"
    git config user.name "Test User"

    echo "initial" > file.txt
    git add file.txt
    git commit -q -m "initial commit"
    git tag -a v1.0 -m "v1.0"

    git commit -q --allow-empty -m $'feat: add feature\n\nChanged behavior from A | B.'

    bash "$SCRIPT_PATH" >/dev/null 2>&1

    if grep -q "feat: add feature" CHANGELOG.md && \
       ! grep -q "A | B" CHANGELOG.md; then
        return 0
    fi
    cat CHANGELOG.md
    return 1
}

# Test 5: Commit sem body
test_no_body() {
    git init -q
    git config user.email "test@test.com"
    git config user.name "Test User"

    echo "initial" > file.txt
    git add file.txt
    git commit -q -m "initial commit"
    git tag -a v1.0 -m "v1.0"

    git commit -q --allow-empty -m "fix: resolve authentication bug"

    bash "$SCRIPT_PATH" >/dev/null 2>&1

    if grep -q "fix: resolve authentication bug" CHANGELOG.md; then
        return 0
    fi
    cat CHANGELOG.md
    return 1
}

# Test 6: Classification
test_classification() {
    git init -q
    git config user.email "test@test.com"
    git config user.name "Test User"

    echo "initial" > file.txt
    git add file.txt
    git commit -q -m "initial commit"
    git tag -a v1.0 -m "v1.0"

    # Test various commit types
    git commit -q --allow-empty -m "feat: add feature"
    git commit -q --allow-empty -m "fix: fix bug"
    git commit -q --allow-empty -m "refactor: reorganize code"
    git commit -q --allow-empty -m "remove deprecated code"
    git commit -q --allow-empty -m "Update documentation"
    git commit -q --allow-empty -m "Improve performance"
    git commit -q --allow-empty -m "Delete unused file"
    git commit -q --allow-empty -m "chore: update deps"
    git commit -q --allow-empty -m "docs: fix typo"
    git commit -q --allow-empty -m "test: add unit tests"

    bash "$SCRIPT_PATH" >/dev/null 2>&1

    # Check classifications - use awk to extract sections properly
    local ok=1
    grep -q "### Added" CHANGELOG.md || ok=0
    grep -q "### Fixed" CHANGELOG.md || ok=0
    grep -q "### Changed" CHANGELOG.md || ok=0
    grep -q "### Removed" CHANGELOG.md || ok=0

    # Use larger context to capture all items in each section
    # feat -> Added
    grep -A10 "### Added" CHANGELOG.md | grep -q "feat: add feature" || ok=0
    # fix -> Fixed
    grep -A10 "### Fixed" CHANGELOG.md | grep -q "fix: fix bug" || ok=0
    # refactor -> Changed
    grep -A10 "### Changed" CHANGELOG.md | grep -q "refactor: reorganize code" || ok=0
    # remove -> Removed
    grep -A10 "### Removed" CHANGELOG.md | grep -q "remove deprecated code" || ok=0
    # Update -> Changed
    grep -A10 "### Changed" CHANGELOG.md | grep -q "Update documentation" || ok=0
    # Improve -> Changed
    grep -A10 "### Changed" CHANGELOG.md | grep -q "Improve performance" || ok=0
    # Delete -> Removed
    grep -A10 "### Removed" CHANGELOG.md | grep -q "Delete unused file" || ok=0
    # chore -> Changed
    grep -A10 "### Changed" CHANGELOG.md | grep -q "chore: update deps" || ok=0
    # docs -> Changed
    grep -A10 "### Changed" CHANGELOG.md | grep -q "docs: fix typo" || ok=0
    # test -> Changed
    grep -A10 "### Changed" CHANGELOG.md | grep -q "test: add unit tests" || ok=0

    [[ $ok -eq 1 ]]
}

# Test 7: CHANGELOG existente
test_existing_changelog() {
    git init -q
    git config user.email "test@test.com"
    git config user.name "Test User"

    echo "initial" > file.txt
    git add file.txt
    git commit -q -m "initial commit"
    git tag -a v1.0 -m "v1.0"

    # Create existing CHANGELOG without [Unreleased]
    cat > CHANGELOG.md <<'EOF'
# Changelog

## [1.0.0] - 2026-01-01

### Added
- Initial release
EOF

    git add CHANGELOG.md
    git commit -q -m "chore: add changelog"

    # Add new commit
    git commit -q --allow-empty -m "feat: new feature"

    bash "$SCRIPT_PATH" >/dev/null 2>&1

    # Check: only one "# Changelog", [Unreleased] added, history preserved
    local changelog_count=$(grep -c "^# Changelog" CHANGELOG.md)
    local has_unreleased=$(grep -c "## \[Unreleased\]" CHANGELOG.md)
    local has_history=$(grep -c "1.0.0" CHANGELOG.md)
    local has_new=$(grep -c "feat: new feature" CHANGELOG.md)

    if [[ $changelog_count -eq 1 ]] && [[ $has_unreleased -eq 1 ]] && [[ $has_history -eq 1 ]] && [[ $has_new -eq 1 ]]; then
        return 0
    fi
    cat CHANGELOG.md
    return 1
}

# Test 8: Execução repetida
test_repeated_execution() {
    git init -q
    git config user.email "test@test.com"
    git config user.name "Test User"

    echo "initial" > file.txt
    git add file.txt
    git commit -q -m "initial commit"
    git tag -a v1.0 -m "v1.0"

    git commit -q --allow-empty -m "feat: add feature"

    bash "$SCRIPT_PATH" >/dev/null 2>&1
    bash "$SCRIPT_PATH" >/dev/null 2>&1
    bash "$SCRIPT_PATH" >/dev/null 2>&1

    # Should only have one entry for the feature
    local count=$(grep -c "feat: add feature" CHANGELOG.md)

    [[ $count -eq 1 ]]
}

# Test 9: Repositório sem tags
test_no_tags() {
    git init -q
    git config user.email "test@test.com"
    git config user.name "Test User"

    echo "initial" > file.txt
    git add file.txt
    git commit -q -m "initial commit"

    git commit -q --allow-empty -m "feat: first feature"
    git commit -q --allow-empty -m "fix: first fix"

    bash "$SCRIPT_PATH" >/dev/null 2>&1

    # Should include ALL commits since no tags
    local has_initial=$(grep -c "initial commit" CHANGELOG.md)
    local has_feat=$(grep -c "feat: first feature" CHANGELOG.md)
    local has_fix=$(grep -c "fix: first fix" CHANGELOG.md)

    [[ $has_initial -eq 1 ]] && [[ $has_feat -eq 1 ]] && [[ $has_fix -eq 1 ]]
}

# Test 10: Caracteres especiais
test_special_chars() {
    git init -q
    git config user.email "test@test.com"
    git config user.name "Test User"

    echo "initial" > file.txt
    git add file.txt
    git commit -q -m "initial commit"
    git tag -a v1.0 -m "v1.0"

    # Test various special characters
    git commit -q --allow-empty -m $'feat: add "quotes" and \'apostrophes\''
    git commit -q --allow-empty -m $'fix: handle \$dollar and |pipe|'
    git commit -q --allow-empty -m $'refactor: use & and : and (parens)'

    bash "$SCRIPT_PATH" >/dev/null 2>&1

    local ok=1
    grep -Fq 'feat: add "quotes" and' CHANGELOG.md || ok=0
    grep -Fq 'fix: handle \$dollar and |pipe|' CHANGELOG.md || ok=0
    grep -Fq 'refactor: use & and : and (parens)' CHANGELOG.md || ok=0

    [[ $ok -eq 1 ]]
}

# Run all tests
info "Starting comprehensive test suite..."
echo ""

run_test "Test 1: Tag + commits normais" test_tag_and_commits
run_test "Test 2: Body multilinha" test_multiline_body
run_test "Test 3: Pipe no subject" test_pipe_in_subject
run_test "Test 4: Pipe no body" test_pipe_in_body
run_test "Test 5: Commit sem body" test_no_body
run_test "Test 6: Classification" test_classification
run_test "Test 7: CHANGELOG existente" test_existing_changelog
run_test "Test 8: Execução repetida" test_repeated_execution
run_test "Test 9: Repositório sem tags" test_no_tags
run_test "Test 10: Caracteres especiais" test_special_chars

echo ""
echo "=========================="
echo "Results: $PASS passed, $FAIL failed"
echo "=========================="

if [[ $FAIL -eq 0 ]]; then
    exit 0
else
    exit 1
fi