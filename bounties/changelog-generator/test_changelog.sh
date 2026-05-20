#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

repo="$tmp_dir/repo"
mkdir "$repo"
git -C "$repo" init -q
git -C "$repo" config user.name "Changelog Test"
git -C "$repo" config user.email "changelog-test@example.com"

commit_file() {
  local message="$1"
  local filename="$2"
  printf '%s\n' "$message" > "$repo/$filename"
  git -C "$repo" add "$filename"
  git -C "$repo" commit -q -m "$message"
}

commit_file "feat: add signup flow" "signup.txt"
git -C "$repo" tag v1.0.0
commit_file "fix: resolve login redirect" "fix.txt"
commit_file "remove deprecated endpoint" "remove.txt"
commit_file "docs: update setup guide" "docs.txt"
commit_file "feat(api): add billing endpoint" "billing.txt"

bash "$script_dir/changelog.sh" --repo "$repo" --output CHANGELOG.md --version Unreleased >/dev/null

changelog="$repo/CHANGELOG.md"

grep -q "Commits since \`v1.0.0\`." "$changelog"
grep -q "### Added" "$changelog"
grep -q "add billing endpoint" "$changelog"
grep -q "### Fixed" "$changelog"
grep -q "resolve login redirect" "$changelog"
grep -q "### Changed" "$changelog"
grep -q "update setup guide" "$changelog"
grep -q "### Removed" "$changelog"
grep -q "deprecated endpoint" "$changelog"

if grep -q "signup flow" "$changelog"; then
  echo "Tagged commit should not appear in generated changelog" >&2
  exit 1
fi

echo "changelog generator tests passed"

