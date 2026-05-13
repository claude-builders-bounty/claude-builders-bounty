#!/usr/bin/env python3
"""Compatibility wrapper for running the source checkout directly."""

from claude_review.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
