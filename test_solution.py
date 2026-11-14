import unittest
from solution import parse_commits, generate_markdown

class TestChangelogGenerator(unittest.TestCase):
    def test_parse_commits(self):
        sample = [
            "feat: add export feature",
            "fix: handle null inputs"
        ]
        res = parse_commits(sample)
        self.assertIn("feat: add export feature", res["Added"])
        self.assertIn("fix: handle null inputs", res["Fixed"])

    def test_generate_markdown(self):
        cats = {"Added": ["feat: initial release"], "Fixed": [], "Changed": [], "Security": [], "Other": []}
        md = generate_markdown("1.0.0", cats, release_date="2026-11-13")
        self.assertIn("## [1.0.0] - 2026-11-13", md)
        self.assertIn("### Added", md)
        self.assertIn("- feat: initial release", md)

if __name__ == "__main__":
    unittest.main()
