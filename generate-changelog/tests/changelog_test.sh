#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"
workspace="$(mktemp -d)"
trap 'rm -rf "$workspace"' EXIT

assert_contains() {
  file="$1"
  expected="$2"

  if ! grep -Fq -- "$expected" "$file"; then
    echo "Expected to find: $expected" >&2
    echo "--- $file ---" >&2
    cat "$file" >&2
    exit 1
  fi
}

assert_not_contains() {
  file="$1"
  unexpected="$2"

  if grep -Fq -- "$unexpected" "$file"; then
    echo "Did not expect to find: $unexpected" >&2
    echo "--- $file ---" >&2
    cat "$file" >&2
    exit 1
  fi
}

copy_generator() {
  target="$1"

  cp "$repo_root/changelog.sh" "$target/changelog.sh"
  mkdir -p "$target/generate-changelog"
  cp "$repo_root/generate-changelog/changelog.sh" "$target/generate-changelog/changelog.sh"
}

make_commit() {
  message="$1"
  file="$2"
  content="$3"

  printf '%s\n' "$content" > "$file"
  git add "$file"
  git commit -q -m "$message"
}

init_repo() {
  target="$1"

  mkdir -p "$target"
  cd "$target"
  git init -q
  git config user.name "Changelog Test"
  git config user.email "changelog-test@example.com"
  git config core.autocrlf false
}

test_since_latest_tag() {
  target="$workspace/with-tags"
  init_repo "$target"
  copy_generator "$target"

  make_commit "feat: initial release" "app.txt" "initial"
  git tag v1.0.0
  make_commit "fix: handle empty state" "fix.txt" "fixed"
  make_commit "remove deprecated flag" "remove.txt" "removed"
  make_commit "docs: update usage" "docs.txt" "docs"

  bash changelog.sh --output TEST_CHANGELOG.md

  assert_contains TEST_CHANGELOG.md '_Changes since `v1.0.0`._'
  assert_contains TEST_CHANGELOG.md "### Fixed"
  assert_contains TEST_CHANGELOG.md "fix: handle empty state"
  assert_contains TEST_CHANGELOG.md "### Removed"
  assert_contains TEST_CHANGELOG.md "remove deprecated flag"
  assert_contains TEST_CHANGELOG.md "### Changed"
  assert_contains TEST_CHANGELOG.md "docs: update usage"
  assert_not_contains TEST_CHANGELOG.md "feat: initial release"
}

test_no_tag_fallback() {
  target="$workspace/no-tags"
  init_repo "$target"
  copy_generator "$target"

  make_commit "feat: add dashboard" "dashboard.txt" "dashboard"

  bash changelog.sh --output TEST_CHANGELOG.md

  assert_contains TEST_CHANGELOG.md "_Full project history; no Git tags were found._"
  assert_contains TEST_CHANGELOG.md "### Added"
  assert_contains TEST_CHANGELOG.md "feat: add dashboard"
}

test_preserves_existing_changelog() {
  target="$workspace/preserve-existing"
  init_repo "$target"
  copy_generator "$target"

  make_commit "feat: first feature" "feature.txt" "feature"
  cat > CHANGELOG.md <<'EOF'
# Changelog

## 0.1.0 - 2026-01-01

- Existing release note
EOF

  bash changelog.sh

  assert_contains CHANGELOG.md "feat: first feature"
  assert_contains CHANGELOG.md "## 0.1.0 - 2026-01-01"
  assert_contains CHANGELOG.md "- Existing release note"

  heading_count="$(grep -c '^# Changelog$' CHANGELOG.md)"
  if [ "$heading_count" -ne 1 ]; then
    echo "Expected one top-level changelog heading, found $heading_count" >&2
    cat CHANGELOG.md >&2
    exit 1
  fi
}

test_since_latest_tag
test_no_tag_fallback
test_preserves_existing_changelog

echo "All changelog generator tests passed."
