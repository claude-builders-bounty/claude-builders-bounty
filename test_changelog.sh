#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd)
run_test(){ name=$1; shift; "$@" || { echo "FAIL: $name" >&2; exit 1; }; echo "PASS: $name"; }
mk(){ d=$(mktemp -d); git -C "$d" init -q; git -C "$d" config user.email test@example.com; git -C "$d" config user.name Test; }
commit(){ git -C "$1" add .; git -C "$1" commit -qm "$2"; }
run_tagged(){ mk; echo one > "$d/a"; commit "$d" "Add: first feature"; git -C "$d" tag v1.0.0; echo two > "$d/a"; commit "$d" "Fix: correct parser"; echo three > "$d/b"; commit "$d" "Update: documentation"; rm "$d/b"; commit "$d" "Remove: obsolete file"; (cd "$d" && bash "$ROOT/changelog.sh") >/dev/null; grep -q "Fix: correct parser" "$d/CHANGELOG.md"; grep -q "Update: documentation" "$d/CHANGELOG.md"; grep -q "Remove: obsolete file" "$d/CHANGELOG.md"; ! grep -q "Add: first feature" "$d/CHANGELOG.md"; }
run_notag(){ mk; echo x > "$d/a"; commit "$d" "Add: initial"; echo y > "$d/b"; commit "$d" "Fix: second"; (cd "$d" && bash "$ROOT/changelog.sh") >/dev/null; grep -q "Add: initial" "$d/CHANGELOG.md"; grep -q "Fix: second" "$d/CHANGELOG.md"; }
run_pipe(){ mk; echo x > "$d/a"; commit "$d" "Change: parser | handles pipes"; (cd "$d" && bash "$ROOT/changelog.sh") >/dev/null; grep -qF "Change: parser | handles pipes" "$d/CHANGELOG.md"; }
run_empty_history(){ mk; if (cd "$d" && bash "$ROOT/changelog.sh") >/dev/null 2>&1; then return 1; fi; }
run_git_error(){ d=$(mktemp -d); if (cd "$d" && bash "$ROOT/changelog.sh") >/dev/null 2>&1; then return 1; fi; }
run_test tagged run_tagged; run_test no-tag run_notag; run_test unusual-subject run_pipe; run_test empty-history run_empty_history; run_test git-error run_git_error
