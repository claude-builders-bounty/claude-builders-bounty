#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
cd "$TMP"
git init -q
git config user.name 'Changelog Test'
git config user.email 'test@example.invalid'
printf 'base\n' > app.txt
git add app.txt
git commit -qm 'chore: initial release'
git tag v1.0.0
printf 'feature\n' >> app.txt; git commit -qam 'feat: add export command'
printf 'fix\n' >> app.txt; git commit -qam 'fix(parser): handle empty input'
printf 'docs\n' >> app.txt; git commit -qam 'docs: explain configuration'
printf 'old\n' > legacy.txt; git add legacy.txt; git commit -qm 'remove: legacy adapter'
printf 'breaking\n' >> app.txt; git commit -qam 'feat!: replace output schema'

bash "$ROOT/changelog.sh" --output CHANGELOG.md
test -s CHANGELOG.md
grep -q '^### Added$' CHANGELOG.md
grep -q 'feat: add export command' CHANGELOG.md
grep -q '^### Fixed$' CHANGELOG.md
grep -q 'fix(parser): handle empty input' CHANGELOG.md
grep -q '^### Changed$' CHANGELOG.md
grep -q 'docs: explain configuration' CHANGELOG.md
grep -q 'BREAKING: feat!: replace output schema' CHANGELOG.md
grep -q '^### Removed$' CHANGELOG.md
grep -q 'remove: legacy adapter' CHANGELOG.md
if grep -q 'initial release' CHANGELOG.md; then
  echo 'Failure: commit at the latest tag leaked into output' >&2
  exit 1
fi
stdout=$(bash "$ROOT/changelog.sh" --from v1.0.0 --stdout)
grep -q 'add export command' <<<"$stdout"
printf 'PASS: real Git history categorized correctly and tag boundary respected.\n'
