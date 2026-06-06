#!/usr/bin/env python3
"""Verify the bundled sample changelog output."""

from __future__ import annotations

from pathlib import Path


REQUIRED_SNIPPETS = [
    "# Changelog",
    "All notable changes are documented in this file.",
    "## [Unreleased]",
    "### Changed",
    "Generated from commits after `v2.34.2`",
]


def main() -> int:
    sample = Path(__file__).resolve().parents[1] / "samples" / "CHANGELOG.sample.md"
    content = sample.read_text(encoding="utf-8")

    missing = [snippet for snippet in REQUIRED_SNIPPETS if snippet not in content]
    if missing:
        print("Missing sample snippet(s):")
        for snippet in missing:
            print(f"- {snippet}")
        return 1

    if content.count("### ") < 1:
        print("Expected at least one changelog section heading.")
        return 1

    print("Sample changelog verification passed.")
    print(f"Checked {len(REQUIRED_SNIPPETS)} required snippets and section headings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
