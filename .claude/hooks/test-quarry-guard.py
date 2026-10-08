#!/usr/bin/env python3
"""Focused regressions for quarry-guard.py.

Pins wrapper-option-operand handling in unwrap(): for sudo/doas/env, options
that take a following operand must not leave that operand as the apparent
command. Run: python3 .claude/hooks/test-quarry-guard.py
"""

import importlib.util
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "quarry_guard", Path(__file__).with_name("quarry-guard.py"))
quarry_guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(quarry_guard)

BLOCKED_CASES = [
    "sudo -u root rm -rf /tmp/x",
    "sudo -H -u root git push --force",
    "sudo -u postgres psql -c 'DROP TABLE users'",
    "doas -u root rm -rf /tmp/x",
    "sudo -p 'pw: ' rm -rf /tmp/x",
    "sudo -uroot rm -rf /tmp/x",
    "sudo --user root rm -rf /tmp/x",
    "sudo --prompt='pw: ' rm -rf /tmp/x",
    "env -u FOO rm -rf /tmp/x",
    "env --chdir=/tmp rm -rf x",
    "doas -n rm -rf /tmp/x",
    "env -S 'rm -rf /tmp/x'",
    "env -S 'sudo -u root rm -rf /tmp/x'",
    "env --split-string 'rm -rf /tmp/x'",
    "env --split-string='rm -rf /tmp/x'",
    "env -S'rm -rf /tmp/x'",
    "env -S \"psql -c 'DROP TABLE users'\"",
    "env -S 'git push --force'",
    "sudo rm -rf /tmp/x",
    "git push --force origin main",
    "bash -c 'rm -rf /tmp/x'",
    "psql -c 'DROP TABLE users'",
    "env -S 'rm -rf /tmp/x'",
    "env -S 'sudo -u root rm -rf /tmp/x'",
    "env --split-string 'rm -rf /tmp/x'",
    "env --split-string='rm -rf /tmp/x'",
    "env -S'rm -rf /tmp/x'",
    "env -S \"psql -c 'DROP TABLE users'\"",
    "env -S 'git push --force'",
]

ALLOWED_CASES = [
    "sudo -u root ls -la /tmp",
    "sudo -n true",
    "env FOO=1 ls",
    "sudo -V",
    "echo DROP TABLE",
    "env -S 'ls -la /tmp'",
    "env -S 'echo hello'",
    "env -S 'echo DROP TABLE'",
]

failures = []
for command in BLOCKED_CASES:
    reason = quarry_guard.classify(command)
    if reason is None:
        failures.append("expected block: %r" % command)
for command in ALLOWED_CASES:
    reason = quarry_guard.classify(command)
    if reason is not None:
        failures.append("expected allow (%s): %r" % (reason, command))

if failures:
    for failure in failures:
        print("FAIL", failure)
    sys.exit(1)
print("%d blocked + %d allowed cases pass" % (len(BLOCKED_CASES), len(ALLOWED_CASES)))
