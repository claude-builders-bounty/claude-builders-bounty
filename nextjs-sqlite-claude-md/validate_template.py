#!/usr/bin/env python3
"""Minimal checks for bounty issue #2 template quality gates."""

from __future__ import annotations

from pathlib import Path
import re
import sys

TEMPLATE = Path(__file__).with_name("CLAUDE.md")

REQUIRED_PHRASES = [
    "Stack and Runtime Baseline",
    "Canonical Project Layout",
    "Database and Migration Rules",
    "Dev Commands and Workflow",
    "What We Do Not Do (And Why)",
]


def fail(msg: str) -> int:
    print(f"ERROR: {msg}")
    return 1


def main() -> int:
    if not TEMPLATE.exists():
        return fail("CLAUDE.md not found")

    content = TEMPLATE.read_text(encoding="utf-8")

    for phrase in REQUIRED_PHRASES:
        if phrase not in content:
            return fail(f"missing required section: {phrase}")

    rule_count = len(re.findall(r"^- Rule:", content, flags=re.MULTILINE))
    why_count = len(re.findall(r"^- Why:", content, flags=re.MULTILINE))
    if rule_count == 0:
        return fail("no opinionated rules found")
    if why_count < rule_count:
        return fail("every rule must include a matching Why line")

    required_commands = [
        "pnpm dev",
        "pnpm lint",
        "pnpm typecheck",
        "pnpm db:generate",
        "pnpm db:migrate",
    ]
    for command in required_commands:
        if command not in content:
            return fail(f"missing required command: {command}")

    print("OK: template includes required sections and rule reasons.")
    print(f"Rule count: {rule_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
