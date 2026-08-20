#!/usr/bin/env bash
set -e

TMP_DIR=$(mktemp -d)
cd "$TMP_DIR"
git init -q
git config user.name "Tester"
git config user.email "tester@example.com"

echo "init" > file.txt
git add file.txt
git commit -m "chore: initial commit" -q

git tag v1.0.0

echo "feat1" >> file.txt
git commit -am "feat(api): add auth endpoint" -q

echo "fix1" >> file.txt
git commit -am "fix(db): resolve connection pool leak" -q

echo "refactor1" >> file.txt
git commit -am "refactor: simplify token parser" -q

echo "remove1" >> file.txt
git commit -am "remove: legacy auth v1" -q

bash /root/bounty_submissions/samuel_git_changelog/changelog.sh --output CHANGELOG.md

cat CHANGELOG.md

grep -q "### Added" CHANGELOG.md
grep -q "### Fixed" CHANGELOG.md
grep -q "### Changed" CHANGELOG.md
grep -q "### Removed" CHANGELOG.md

rm -rf "$TMP_DIR"
echo "✅ Changelog generator tests passed!"
