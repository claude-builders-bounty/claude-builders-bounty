import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("generate_changelog.py")
spec = importlib.util.spec_from_file_location("generate_changelog", SCRIPT)
module = importlib.util.module_from_spec(spec)
sys.modules["generate_changelog"] = module
assert spec.loader is not None
spec.loader.exec_module(module)


class GenerateChangelogTest(unittest.TestCase):
    def test_categorize_conventional_commits(self) -> None:
        self.assertEqual(module.categorize("feat(api): add endpoint"), "Added")
        self.assertEqual(module.categorize("fix(ui): align button"), "Fixed")
        self.assertEqual(module.categorize("remove legacy route"), "Removed")
        self.assertEqual(module.categorize("docs: update readme"), "Changed")

    def test_render_includes_all_sections(self) -> None:
        commits = [
            module.Commit("a1b2c3d", "feat: add dashboard"),
            module.Commit("b2c3d4e", "fix: repair webhook"),
        ]

        output = module.render_changelog(commits, "v1.0.0")

        self.assertIn("Commits since `v1.0.0`", output)
        self.assertIn("### Added", output)
        self.assertIn("- feat: add dashboard (a1b2c3d)", output)
        self.assertIn("### Fixed", output)
        self.assertIn("- fix: repair webhook (b2c3d4e)", output)
        self.assertIn("### Changed", output)
        self.assertIn("### Removed", output)


if __name__ == "__main__":
    unittest.main()
