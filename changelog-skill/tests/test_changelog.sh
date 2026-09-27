#!/usr/bin/env bash
# test_changelog.sh — asserts for changelog.sh (no deps).
cd "$(dirname "$0")/.."
T=/tmp/changelog-test-out.md
pass=0; fail=0
chk() { if eval "$2"; then pass=$((pass+1)); echo "GREEN $1"; else fail=$((fail+1)); echo "RED $1"; fi; }

bash changelog.sh --repo /tmp/homelab --out "$T" >/dev/null 2>&1
chk "exit 0 on real repo" "[[ -f $T ]]"
chk "4 required groups" "grep -q '### Added' $T && grep -q '### Fixed' $T && grep -q '### Changed' $T && grep -q '### Removed' $T"
chk "feat->Added" "grep -A20 '### Added' $T | grep -qi 'feat'"
chk "fix->Fixed" "grep -A20 '### Fixed' $T | grep -qi 'fix'"
chk "short-SHA attached" "grep -Eq '\([0-9a-f]{7}\)' $T"
chk "Keep-a-Changelog header + UTC date" "grep -q 'Keep a Changelog' $T && grep -Eq '[0-9]{4}-[0-9]{2}-[0-9]{2}' $T"
chk "preview writes nothing" "rm -f /tmp/prev.md && bash changelog.sh --repo /tmp/homelab --out /tmp/prev.md --preview | grep -q '### Added' && [[ ! -f /tmp/prev.md ]]"
chk "unknown tag fails closed" "! bash changelog.sh --repo /tmp/homelab --since no-such-tag-xyz --out /tmp/nw.md 2>/dev/null && [[ ! -f /tmp/nw.md ]]"
chk "empty range fails closed" "git -C /tmp/homelab stash list >/dev/null 2>&1; ! bash changelog.sh --repo /tmp/homelab --since HEAD --out /tmp/nw2.md 2>/dev/null && [[ ! -f /tmp/nw2.md ]]"
chk "version flag" "bash changelog.sh --repo /tmp/homelab --version v1.2.0 --out $T >/dev/null 2>&1 && grep -q '\[v1.2.0\]' $T"
echo "RESULT: $pass green / $fail red"
[[ $fail -eq 0 ]]
