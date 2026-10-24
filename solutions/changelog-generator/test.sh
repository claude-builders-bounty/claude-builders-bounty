#!/usr/bin/env bash
set -euo pipefail
script=$(cd "$(dirname "$0")" && pwd)/changelog.sh
root=$(mktemp -d)
trap 'rm -rf "$root"' EXIT
cd "$root"
git init -q
git -c user.name=Test -c user.email=test@example.com commit -q --allow-empty -m 'initial'
git tag v0.1.0
for message in 'feat: new feature' 'fix(api): repair' 'remove: old option' 'docs: explain'; do
 git -c user.name=Test -c user.email=test@example.com commit -q --allow-empty -m "$message"
done
bash "$script"
grep -q '## Added' CHANGELOG.md
grep -q 'feat: new feature' CHANGELOG.md
grep -q 'fix(api): repair' CHANGELOG.md
grep -q 'remove: old option' CHANGELOG.md
grep -q 'docs: explain' CHANGELOG.md
if grep -q 'initial' CHANGELOG.md; then echo 'tag range failure' >&2; exit 1; fi
bash "$script"; echo 'PASS: categories, tag range, idempotence'
