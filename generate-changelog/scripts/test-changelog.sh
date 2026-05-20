#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
workspace="$(mktemp -d "${TMPDIR:-/tmp}/generate-changelog-test.XXXXXX")"

cleanup() {
    rm -rf "$workspace"
}
trap cleanup EXIT

cd "$workspace"
git init --quiet
git config user.name "Changelog Test"
git config user.email "changelog-test@example.com"

git commit --allow-empty -m "feat: initial feature" --quiet
git tag v1.0.0
git commit --allow-empty -m "fix: repair parser" --quiet
git commit --allow-empty -m "docs: update guide" --quiet
git commit --allow-empty -m "remove deprecated option" --quiet
git checkout -b feature-branch --quiet
git commit --allow-empty -m "feat: branch feature" --quiet
git checkout - --quiet
git merge --no-ff feature-branch -m "Merge branch feature-branch" --quiet

output="$(bash "$script_dir/changelog.sh" --stdout)"

assert_contains() {
    local expected="$1"
    if ! grep -Fq -- "$expected" <<<"$output"; then
        echo "expected output to contain: $expected" >&2
        echo "$output" >&2
        exit 1
    fi
}

assert_contains 'Commits since the latest tag `v1.0.0`.'
assert_contains '- branch feature'
assert_contains '- Merge branch feature-branch'
assert_contains '### Fixed'
assert_contains '- repair parser'
assert_contains '### Changed'
assert_contains '- update guide'
assert_contains '### Removed'
assert_contains '- remove deprecated option'

bash "$script_dir/changelog.sh" --output CHANGELOG.md >/dev/null
test -s CHANGELOG.md

if bash "$script_dir/changelog.sh" --from does-not-exist --stdout >/dev/null 2>&1; then
    echo "expected invalid --from ref to fail" >&2
    exit 1
fi

echo "generate-changelog tests passed"
