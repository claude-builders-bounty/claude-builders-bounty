"""
Unit tests for GitChangelogGenerator skill utility.
"""

import sys
from pathlib import Path

# Add script directory to python path for imports
SKILL_SCRIPT_DIR = Path(__file__).parent.parent / "skills" / "generate_changelog" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPT_DIR))

from generate_changelog import GitChangelogGenerator


def test_parse_conventional_commit():
    generator = GitChangelogGenerator()
    
    # Test feature commit with scope
    res = generator.parse_commit_message("feat(auth): add OAuth2 provider support")
    assert res["type"] == "feat"
    assert res["scope"] == "auth"
    assert res["subject"] == "add OAuth2 provider support"
    assert res["is_breaking"] is False
    assert res["is_conventional"] is True

    # Test fix commit without scope
    res2 = generator.parse_commit_message("fix: prevent deadlock in queue consumer")
    assert res2["type"] == "fix"
    assert res2["scope"] == ""
    assert res2["subject"] == "prevent deadlock in queue consumer"
    assert res2["is_breaking"] is False

    # Test breaking change commit
    res3 = generator.parse_commit_message("refactor(api)!: change user response payload format")
    assert res3["type"] == "refactor"
    assert res3["scope"] == "api"
    assert res3["is_breaking"] is True


def test_parse_non_conventional_commit():
    generator = GitChangelogGenerator()
    res = generator.parse_commit_message("Update README setup guide")
    assert res["type"] == "chore"
    assert res["is_conventional"] is False
    assert res["subject"] == "Update README setup guide"


def test_generate_markdown_formatting():
    generator = GitChangelogGenerator()
    commits = [
        {
            "type": "feat",
            "scope": "billing",
            "subject": "add Stripe webhook handler",
            "is_breaking": False,
            "hash": "abc1234",
        },
        {
            "type": "fix",
            "scope": "auth",
            "subject": "fix token expiration boundary check",
            "is_breaking": False,
            "hash": "def5678",
        },
        {
            "type": "feat",
            "scope": "api",
            "subject": "redesign v2 authentication endpoints",
            "is_breaking": True,
            "hash": "ghi9012",
        },
    ]

    md = generator.generate_markdown(commits, version="v1.0.0", date_str="2026-10-01")

    assert "## [v1.0.0] - 2026-10-01" in md
    assert "### ⚠️ BREAKING CHANGES" in md
    assert "- **api**: redesign v2 authentication endpoints (ghi9012)" in md
    assert "### Features" in md
    assert "- **billing**: add Stripe webhook handler (abc1234)" in md
    assert "### Bug Fixes" in md
    assert "- **auth**: fix token expiration boundary check (def5678)" in md
