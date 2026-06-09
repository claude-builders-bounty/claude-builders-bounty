#!/usr/bin/env bash
set -euo pipefail
cd "$(mktemp -d)"
git init -q && git config user.email "test@test.com" && git config user.name "Tester"
echo "# A" > README.md && git add . && git commit -q -m "Initial commit"
echo "x" > a.js && git add . && git commit -q -m "feat: add main module"
echo "y" > b.js && git add . && git commit -q -m "fix: handle null input"
echo "z" > c.js && git add . && git commit -q -m "refactor: clean up exports"
bash /workspace/claude-builders-bounty/skills/changelog/changelog.sh --output CHANGELOG.md
[[ -s CHANGELOG.md ]] && echo "TEST PASS" || echo "TEST FAIL"
