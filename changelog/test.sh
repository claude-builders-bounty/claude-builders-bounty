#!/usr/bin/env bash
# test.sh - exercises changelog.sh against throwaway git repos. Usage: bash test.sh
set -uo pipefail
script="$(cd "$(dirname "$0")" && pwd)/changelog.sh"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
pass=0 fail=0

check() { # check <description> <command...>
  if "${@:2}"; then pass=$((pass + 1)); echo "ok   - $1"
  else fail=$((fail + 1)); echo "FAIL - $1"; fi
}
has() { grep -qF -- "$2" "$1"; }
lacks() { ! grep -qF -- "$2" "$1"; }
count() { [ "$(grep -cF -- "$2" "$1")" = "$3" ]; }
commit() { git commit -q --allow-empty -m "$1" ${2:+-m "$2"}; }
newrepo() {
  mkdir -p "$work/$1" && cd "$work/$1" && git init -q &&
    git config user.email t@example.com && git config user.name tester && git config commit.gpgsign false
}

# 1. Outside a git repo: clean error, non-zero exit, no file written.
mkdir "$work/plain" && cd "$work/plain"
bash "$script" >/dev/null 2>err.txt; rc=$?
check "non-repo exits 1" [ "$rc" = 1 ]
check "non-repo explains why" has err.txt "not inside a git repository"
check "non-repo writes nothing" [ ! -e CHANGELOG.md ]

# 2. Empty history (git init, no commits).
newrepo empty
check "empty repo succeeds" bash "$script" 2>/dev/null
check "empty repo says no commits" has CHANGELOG.md "_No commits yet._"
check "empty repo has Unreleased heading" has CHANGELOG.md "## [Unreleased]"

# 3. No tags: every commit is categorized; special characters survive.
newrepo notags
commit 'feat(api): add /users endpoint'
commit 'fix: handle "quoted" $HOME `ticks` & <script>alert(1)</script> \n back\slash'
commit 'refactor!: rename config keys'
commit 'chore: remove legacy build script'
commit 'Add dark mode toggle'
commit 'Fixed crash on startup'
commit 'Delete unused assets'
commit 'Update dependencies'
commit 'perf: speed up parser' 'BREAKING CHANGE: drops Node 16'
commit 'docs: address review notes'
commit 'feat: emoji 🎉 and ünïcödé'
git checkout -q -b side && commit 'feat: side branch work' && git checkout -q - && git merge -q --no-ff side -m 'Merge branch side'
bash "$script" 2>/dev/null
f=CHANGELOG.md
check "Added section"   has $f "### Added"
check "Fixed section"   has $f "### Fixed"
check "Changed section" has $f "### Changed"
check "Removed section" has $f "### Removed"
check "scope rendered bold"         has $f '- **api:** add /users endpoint'
check "plain 'Add' -> Added"        bash -c "sed -n '/### Added/,/### Fixed/p' $f | grep -qF 'Add dark mode toggle'"
check "plain 'Fixed' -> Fixed"      bash -c "sed -n '/### Fixed/,/### Changed/p' $f | grep -qF 'Fixed crash on startup'"
check "chore: remove -> Removed"    bash -c "sed -n '/### Removed/,\$p' $f | grep -qF 'remove legacy build script'"
check "plain 'Delete' -> Removed"   bash -c "sed -n '/### Removed/,\$p' $f | grep -qF 'Delete unused assets'"
check "'address' is not 'add'"      bash -c "sed -n '/### Changed/,/### Removed/p' $f | grep -qF 'address review notes'"
check "! marks breaking"            has $f '- **BREAKING:** **refactor:** rename config keys'
check "footer marks breaking"       has $f '- **BREAKING:** **perf:** speed up parser'
check "non-feat/fix type shown"     has $f '- **chore:** remove legacy build script'
check "feat type implied by section" lacks $f '**feat'
check "special chars kept, HTML escaped" has $f 'handle "quoted" $HOME `ticks` &amp; &lt;script&gt;alert(1)&lt;/script&gt; \n back\slash'
check "unicode kept"                has $f 'emoji 🎉 and ünïcödé'
check "merge commits skipped"       lacks $f "Merge branch"
check "merged branch commit kept"   has $f "side branch work"
check "short hash included"         grep -qE '\(`[0-9a-f]{7,}`\)' $f

# 4. Tagged repo: only commits after the latest tag go into [Unreleased].
newrepo tagged
commit 'feat: first feature'
git tag v1.0.0
commit 'fix: post-release bug'
commit 'feat: shiny thing'
bash "$script" 2>/dev/null
check "since-tag: new commits listed" has CHANGELOG.md "post-release bug"
check "since-tag: old commits excluded" lacks CHANGELOG.md "first feature"
cp CHANGELOG.md before.md
bash "$script" 2>/dev/null
check "re-run is idempotent" cmp -s before.md CHANGELOG.md

# 5. HEAD on a tag: documents that release vs the previous tag, replaces [Unreleased], keeps history.
git tag v1.1.0
printf '\n## [v1.0.0] - 2020-01-01\n\n### Added\n\n- first feature\n' >>CHANGELOG.md
chmod 644 CHANGELOG.md
bash "$script" 2>/dev/null
check "release heading with date" grep -qE '^## \[v1\.1\.0\] - [0-9]{4}-[0-9]{2}-[0-9]{2}$' CHANGELOG.md
check "stale [Unreleased] replaced" lacks CHANGELOG.md "## [Unreleased]"
check "release lists its commits" has CHANGELOG.md "shiny thing"
check "older release kept" has CHANGELOG.md "## [v1.0.0] - 2020-01-01"
check "single title line" count CHANGELOG.md "# Changelog" 1
check "new release above older one" bash -c "[ \$(grep -n 'v1.1.0' CHANGELOG.md | head -1 | cut -d: -f1) -lt \$(grep -n 'v1.0.0' CHANGELOG.md | head -1 | cut -d: -f1) ]"
check "file permissions kept" bash -c "[ \"\$(ls -l CHANGELOG.md | cut -c1-10)\" = '-rw-r--r--' ]"

# 6. Tag on HEAD and nothing new afterwards, plus stdout mode and custom path.
commit 'chore: bump'
git tag v1.2.0
git tag v1.3.0
bash "$script" - >out.md 2>/dev/null
check "stdout mode prints changelog" has out.md "## [v1."
check "custom output path" bash -c "bash '$script' docs-CHANGELOG.md 2>/dev/null && [ -s docs-CHANGELOG.md ]"
newrepo onlymerge
commit 'feat: x' && commit 'feat: a' && git tag v0.1.0
git reset -q --hard "$(git commit-tree 'HEAD^{tree}' -p HEAD -p HEAD~1 -m 'Merge only')" # merge commit, nothing else new
bash "$script" - >out.md 2>/dev/null
check "nothing notable since tag" has out.md '_No changes since `v0.1.0`._'

# 7. GitHub remote: hashes become links, credentials never leak.
newrepo remote
git remote add origin https://user:secret-token@github.com/acme/widgets.git
commit 'feat: linked'
bash "$script" 2>/dev/null
check "commit links to GitHub" grep -qE '\]\(https://github.com/acme/widgets/commit/[0-9a-f]+\)' CHANGELOG.md
check "credentials not leaked" lacks CHANGELOG.md "secret-token"

echo "---"
echo "$pass passed, $fail failed"
[ "$fail" = 0 ]
