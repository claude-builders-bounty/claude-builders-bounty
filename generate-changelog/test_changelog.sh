#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(mktemp -d)"
trap 'rm -rf "$repo_dir"' EXIT

assert_contains() {
  needle="$1"
  file="$2"

  if ! grep -Fq -- "$needle" "$file"; then
    echo "Expected to find: $needle" >&2
    echo "--- $file ---" >&2
    cat "$file" >&2
    exit 1
  fi
}

commit_file() {
  message="$1"
  content="$2"

  printf '%s\n' "$content" >> app.txt
  git add app.txt
  git commit -m "$message" >/dev/null
}

cd "$repo_dir"
git init -q
git config user.email "test@example.com"
git config user.name "Changelog Test"

commit_file "chore: bootstrap project" "bootstrap"
git tag v0.1.0
commit_file "feat: add profile page" "profile"
commit_file "feat(api)!: require signed requests" "api"
commit_file "fix: correct login redirect" "login"
commit_file "refactor: simplify session store" "session"
commit_file "remove: delete legacy flag" "legacy"

bash "$script_dir/changelog.sh" --output "$repo_dir/CHANGELOG.md" >/dev/null

assert_contains "_Previous tag: v0.1.0._" "$repo_dir/CHANGELOG.md"
assert_contains "### Added" "$repo_dir/CHANGELOG.md"
assert_contains "- feat: add profile page" "$repo_dir/CHANGELOG.md"
assert_contains "- feat(api)!: require signed requests" "$repo_dir/CHANGELOG.md"
assert_contains "### Fixed" "$repo_dir/CHANGELOG.md"
assert_contains "- fix: correct login redirect" "$repo_dir/CHANGELOG.md"
assert_contains "### Changed" "$repo_dir/CHANGELOG.md"
assert_contains "- refactor: simplify session store" "$repo_dir/CHANGELOG.md"
assert_contains "### Removed" "$repo_dir/CHANGELOG.md"
assert_contains "- remove: delete legacy flag" "$repo_dir/CHANGELOG.md"

command_file="$(cd "$script_dir/.." && pwd)/.claude/commands/generate-changelog.md"
assert_contains "bash changelog.sh" "$command_file"
assert_contains "/generate-changelog" "$script_dir/README.md"

echo "test_changelog.sh passed"
