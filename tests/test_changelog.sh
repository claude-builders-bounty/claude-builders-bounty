#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
script="$repo_root/skills/generate-changelog/changelog.sh"
skill="$repo_root/skills/generate-changelog/SKILL.md"

test -f "$skill"
grep -q "trigger: /generate-changelog" "$skill"
grep -q "bash skills/generate-changelog/changelog.sh" "$skill"

tmp_repo="$(mktemp -d)"
outside_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_repo" "$outside_dir"' EXIT

git -C "$tmp_repo" init -q
git -C "$tmp_repo" config user.email "test@example.com"
git -C "$tmp_repo" config user.name "Test User"

printf 'one\n' > "$tmp_repo/file.txt"
git -C "$tmp_repo" add file.txt
git -C "$tmp_repo" commit -q -m "chore: initial release"
git -C "$tmp_repo" tag v1.0.0

printf 'two\n' >> "$tmp_repo/file.txt"
git -C "$tmp_repo" commit -am "feat: add webhook retry queue" -q

printf 'three\n' >> "$tmp_repo/file.txt"
git -C "$tmp_repo" commit -am "fix: handle empty API responses" -q

printf 'four\n' >> "$tmp_repo/file.txt"
git -C "$tmp_repo" commit -am "docs: clarify setup steps" -q

printf 'five\n' >> "$tmp_repo/file.txt"
git -C "$tmp_repo" commit -am "remove: drop legacy config loader" -q

(cd "$tmp_repo" && bash "$script" --output CHANGELOG.md)

grep -q "Generated from git history since v1.0.0" "$tmp_repo/CHANGELOG.md"
grep -q "## Unreleased -" "$tmp_repo/CHANGELOG.md"
grep -q "### Added" "$tmp_repo/CHANGELOG.md"
grep -q "feat: add webhook retry queue" "$tmp_repo/CHANGELOG.md"
grep -q "### Fixed" "$tmp_repo/CHANGELOG.md"
grep -q "fix: handle empty API responses" "$tmp_repo/CHANGELOG.md"
grep -q "### Changed" "$tmp_repo/CHANGELOG.md"
grep -q "docs: clarify setup steps" "$tmp_repo/CHANGELOG.md"
grep -q "### Removed" "$tmp_repo/CHANGELOG.md"
grep -q "remove: drop legacy config loader" "$tmp_repo/CHANGELOG.md"

bash "$script" --repo "$tmp_repo" --since v1.0.0 --version v1.1.0 --output docs/CHANGELOG.md

grep -q "## v1.1.0 -" "$tmp_repo/docs/CHANGELOG.md"
grep -q "Generated from git history since v1.0.0" "$tmp_repo/docs/CHANGELOG.md"

stdout_output="$(cd "$outside_dir" && bash "$script" --repo "$tmp_repo" --since v1.0.0 --version v1.1.0 --stdout)"
printf '%s\n' "$stdout_output" | grep -q "# Changelog"
printf '%s\n' "$stdout_output" | grep -q "## v1.1.0 -"
printf '%s\n' "$stdout_output" | grep -q "feat: add webhook retry queue"

if bash "$script" --repo "$tmp_repo" --since --format=%s --stdout 2>"$outside_dir/since-option.err"; then
  echo "expected option-like --since ref to fail" >&2
  exit 1
fi
grep -q "error: --since ref cannot start with '-'" "$outside_dir/since-option.err"

if bash "$script" --repo "$tmp_repo" --output ../CHANGELOG.md 2>"$outside_dir/output-escape.err"; then
  echo "expected escaping --output path to fail" >&2
  exit 1
fi
grep -q "error: --output must stay inside the target repository" "$outside_dir/output-escape.err"

if bash "$script" --repo "$tmp_repo" --output "$outside_dir/CHANGELOG.md" 2>"$outside_dir/output-absolute.err"; then
  echo "expected absolute --output path outside repo to fail" >&2
  exit 1
fi
grep -q "error: --output must stay inside the target repository" "$outside_dir/output-absolute.err"
test ! -f "$outside_dir/CHANGELOG.md"

echo "test_changelog.sh passed"
