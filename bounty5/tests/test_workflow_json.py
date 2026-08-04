#!/usr/bin/env python3
"""Validate n8n workflow JSON structure for bounty #5."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WF = json.loads((ROOT / "weekly-dev-summary.workflow.json").read_text(encoding="utf-8"))


def test_nodes_present():
    names = {n["name"] for n in WF["nodes"]}
    required = {
        "Friday 17:00",
        "Config",
        "GitHub Commits",
        "GitHub Closed Issues",
        "GitHub Pulls",
        "Build Prompt",
        "Claude Summary",
        "Extract Text",
        "Has Discord?",
        "Discord Webhook",
        "Email Summary",
    }
    missing = required - names
    assert not missing, missing


def test_model_and_cron():
    raw = json.dumps(WF)
    assert "claude-sonnet-4-20250514" in raw
    assert "0 17 * * 5" in raw
    assert "api.github.com" in raw
    assert "api.anthropic.com" in raw


def test_connections():
    c = WF["connections"]
    assert "Friday 17:00" in c
    assert "Claude Summary" in c
    assert "Has Discord?" in c


if __name__ == "__main__":
    test_nodes_present()
    test_model_and_cron()
    test_connections()
    print("ok: bounty5 workflow checks 3/3")
