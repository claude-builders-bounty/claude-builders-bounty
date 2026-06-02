import tempfile
import unittest
import importlib.util
import sys
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "generate-changelog"
    / "generate_changelog.py"
)
SPEC = importlib.util.spec_from_file_location("generate_changelog", SCRIPT_PATH)
generate_changelog = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules["generate_changelog"] = generate_changelog
SPEC.loader.exec_module(generate_changelog)


class GenerateChangelogTests(unittest.TestCase):
    def test_classifies_conventional_commit_sections(self):
        commits = [
            generate_changelog.Commit("a1b2c3d", "feat(api): add export endpoint"),
            generate_changelog.Commit("b2c3d4e", "fix: handle empty response"),
            generate_changelog.Commit("c3d4e5f", "refactor: simplify parser"),
            generate_changelog.Commit("d4e5f6a", "remove legacy flag"),
        ]

        with tempfile.TemporaryDirectory() as tmp:
            rendered = generate_changelog.render_changelog(commits, Path(tmp), "v1.0.0", "HEAD")

        self.assertIn("### Added\n- add export endpoint (a1b2c3d)", rendered)
        self.assertIn("### Fixed\n- handle empty response (b2c3d4e)", rendered)
        self.assertIn("### Changed\n- simplify parser (c3d4e5f)", rendered)
        self.assertIn("### Removed\n- remove legacy flag (d4e5f6a)", rendered)

    def test_keyword_fallback_for_non_conventional_subjects(self):
        self.assertEqual(generate_changelog.classify("Repair broken install docs"), "Fixed")
        self.assertEqual(generate_changelog.classify("Introduce theme switcher"), "Added")
        self.assertEqual(generate_changelog.classify("Delete obsolete fixtures"), "Removed")


if __name__ == "__main__":
    unittest.main()
