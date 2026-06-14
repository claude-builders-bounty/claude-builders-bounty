#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fixture="$(mktemp -d)"
trap 'rm -rf "$fixture"' EXIT

grep -q '^name: generate-changelog$' "$root/.claude/skills/generate-changelog/SKILL.md"
grep -q '^tools: Bash$' "$root/.claude/skills/generate-changelog/SKILL.md"

git -C "$fixture" init -q
git -C "$fixture" config user.email test@example.com
git -C "$fixture" config user.name Test

printf 'base\n' > "$fixture/file.txt"
git -C "$fixture" add file.txt
git -C "$fixture" commit -qm "chore: initial"
git -C "$fixture" tag v1.0.0

printf 'feature\n' >> "$fixture/file.txt"
git -C "$fixture" commit -qam "feat: add export | preserve delimiter"
printf 'fix\n' >> "$fixture/file.txt"
git -C "$fixture" commit -qam "fix: handle empty config"
printf 'breaking\n' >> "$fixture/file.txt"
git -C "$fixture" commit -qam "feat!: require Node 20"

(cd "$fixture" && bash "$root/changelog.sh" TEST_CHANGELOG.md >/dev/null)

grep -q 'Changes since v1.0.0' "$fixture/TEST_CHANGELOG.md"
grep -q '### Breaking Changes' "$fixture/TEST_CHANGELOG.md"
grep -q 'require Node 20' "$fixture/TEST_CHANGELOG.md"
grep -q '### Added' "$fixture/TEST_CHANGELOG.md"
grep -q 'add export | preserve delimiter' "$fixture/TEST_CHANGELOG.md"
grep -q '### Fixed' "$fixture/TEST_CHANGELOG.md"
grep -q 'handle empty config' "$fixture/TEST_CHANGELOG.md"
! grep -q 'initial' "$fixture/TEST_CHANGELOG.md"

printf 'changelog regression tests passed\n'
