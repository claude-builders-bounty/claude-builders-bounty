#!/usr/bin/env python3
"""Backward-compatible wrapper for the claude-review CLI."""

from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).with_name("claude-review")), run_name="__main__")
