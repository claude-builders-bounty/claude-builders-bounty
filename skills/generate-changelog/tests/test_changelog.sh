#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
script="$script_dir/scripts/changelog.sh"
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

repo="$tmpdir/repo"
mkdir "$repo"
git -C "$repo" init -q
git -C "$repo" config user.name "Changelog Test"
git -C "$repo" config user.email "changelog@example.com"

commit_file() {
  local subject="$1"
  printf '%s\n' "$subject" >> "$repo/file.txt"
  git -C "$repo" add file.txt
  git -C "$repo" commit -q -m "$subject"
}

commit_file "chore: initial release"
git -C "$repo" tag v0.1.0
commit_file "feat(parser): add commit grouping"
commit_file "fix: handle empty tag ranges"
commit_file "docs: update usage examples"
commit_file "remove: drop deprecated flag"
commit_file "feat!: change output schema"

output="$tmpdir/CHANGELOG.md"
bash "$script" --repo "$repo" --output "$output"

grep -q "Generated from \`v0.1.0..HEAD\`" "$output"
grep -q "### Added" "$output"
grep -q "add commit grouping" "$output"
grep -q "### Fixed" "$output"
grep -q "handle empty tag ranges" "$output"
grep -q "### Changed" "$output"
grep -q "update usage examples" "$output"
grep -q "### Removed" "$output"
grep -q "drop deprecated flag" "$output"
grep -q "### Breaking Changes" "$output"
grep -q "change output schema" "$output"

no_tag_repo="$tmpdir/no-tag-repo"
mkdir "$no_tag_repo"
git -C "$no_tag_repo" init -q
git -C "$no_tag_repo" config user.name "Changelog Test"
git -C "$no_tag_repo" config user.email "changelog@example.com"
printf 'hello\n' > "$no_tag_repo/hello.txt"
git -C "$no_tag_repo" add hello.txt
git -C "$no_tag_repo" commit -q -m "add: initial file"

no_tag_output="$tmpdir/no-tag.md"
bash "$script" --repo "$no_tag_repo" --output "$no_tag_output"
grep -q "full history through HEAD" "$no_tag_output"
grep -q "initial file" "$no_tag_output"

echo "changelog tests passed"
