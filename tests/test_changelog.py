import unittest
import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "skills" / "generate-changelog" / "changelog.py"
SPEC = importlib.util.spec_from_file_location("changelog", MODULE_PATH)
changelog = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = changelog
SPEC.loader.exec_module(changelog)

Commit = changelog.Commit
categorize = changelog.categorize
render_changelog = changelog.render_changelog


class ChangelogTests(unittest.TestCase):
    def test_categorizes_common_commit_shapes(self):
        self.assertEqual(categorize("feat: add export button"), "Added")
        self.assertEqual(categorize("fix: prevent crash"), "Fixed")
        self.assertEqual(categorize("remove deprecated option"), "Removed")
        self.assertEqual(categorize("docs: update setup"), "Changed")

    def test_renders_grouped_changelog(self):
        markdown = render_changelog(
            [
                Commit("abc123456", "feat: add export button"),
                Commit("def123456", "fix: prevent crash"),
            ]
        )
        self.assertIn("### Added", markdown)
        self.assertIn("- Add export button (abc1234)", markdown)
        self.assertIn("### Fixed", markdown)
        self.assertIn("- Prevent crash (def1234)", markdown)


if __name__ == "__main__":
    unittest.main()
