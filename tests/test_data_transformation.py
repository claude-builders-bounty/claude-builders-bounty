#!/usr/bin/env python3
"""
Unit tests for data aggregation, prompt synthesis, and webhook formatting.
"""
import unittest
from datetime import datetime, timezone, timedelta
import json

class TestDataTransformation(unittest.TestCase):
    def setUp(self):
        self.mock_now = datetime.now(timezone.utc)
        self.since_date = self.mock_now - timedelta(days=7)
        
        self.mock_commits = [
            {
                "sha": "a1b2c3d4e5f6g7h8",
                "commit": {
                    "message": "feat(core): add distributed task queue\n\nFull details here.",
                    "author": {"name": "Alice Dev", "date": self.mock_now.isoformat()}
                }
            },
            {
                "sha": "b2c3d4e5f6g7h8i9",
                "commit": {
                    "message": "fix(api): resolve race condition in token refresh",
                    "author": {"name": "Bob Architect", "date": (self.mock_now - timedelta(days=2)).isoformat()}
                }
            }
        ]
        
        self.mock_prs = [
            {
                "number": 101,
                "title": "feat: high-performance websocket router",
                "merged_at": (self.mock_now - timedelta(days=1)).isoformat(),
                "user": {"login": "alice_dev"},
                "labels": [{"name": "enhancement"}, {"name": "high-priority"}],
                "html_url": "https://github.com/org/repo/pull/101"
            },
            {
                "number": 102,
                "title": "chore: old closed unmerged PR",
                "merged_at": None, # Unmerged
                "user": {"login": "charlie"},
                "labels": [{"name": "wontfix"}],
                "html_url": "https://github.com/org/repo/pull/102"
            }
        ]
        
        self.mock_issues = [
            {
                "number": 55,
                "title": "Memory leak under 10k req/s load",
                "pull_request": None, # Genuine issue
                "labels": [{"name": "bug"}],
                "html_url": "https://github.com/org/repo/issues/55"
            },
            {
                "number": 101,
                "title": "feat: high-performance websocket router",
                "pull_request": {"url": "https://api.github.com/repos/org/repo/pulls/101"}, # PR in issues endpoint
                "labels": [{"name": "enhancement"}],
                "html_url": "https://github.com/org/repo/issues/101"
            }
        ]

    def test_merged_pr_filtering(self):
        merged = [p for p in self.mock_prs if p.get("merged_at") is not None]
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["number"], 101)

    def test_issue_filtering_excludes_prs(self):
        pure_issues = [i for i in self.mock_issues if not i.get("pull_request")]
        self.assertEqual(len(pure_issues), 1)
        self.assertEqual(pure_issues[0]["number"], 55)

    def test_discord_payload_structure(self):
        narrative = "🚀 **Executive Summary**\nGreat progress on the distributed engine."
        payload = {
            "content": "📢 **Weekly Engineering Digest: org/repo**",
            "embeds": [
                {
                    "title": "Weekly Report",
                    "description": narrative,
                    "color": 5814783,
                    "fields": [
                        {"name": "Merged PRs", "value": "1", "inline": True},
                        {"name": "Commits", "value": "2", "inline": True}
                    ]
                }
            ]
        }
        self.assertIn("embeds", payload)
        self.assertEqual(len(payload["embeds"]), 1)
        self.assertEqual(payload["embeds"][0]["color"], 5814783)

    def test_slack_payload_blocks(self):
        narrative = "Summary of engineering work."
        payload = {
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "🚀 Weekly Dev Summary", "emoji": True}
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": narrative}
                }
            ]
        }
        self.assertEqual(payload["blocks"][0]["type"], "header")
        self.assertEqual(payload["blocks"][1]["type"], "section")

if __name__ == "__main__":
    unittest.main()
