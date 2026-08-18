import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from template_validator import validate_claude_md

class TestClaudeTemplateValidator(unittest.TestCase):
    def test_validates_production_claude_md(self):
        claude_md_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'CLAUDE.md'))
        res = validate_claude_md(claude_md_path)
        self.assertTrue(res["success"], f"Validation failed: {res}")
        self.assertEqual(len(res["missing_sections"]), 0)
        self.assertEqual(len(res["missing_keywords"]), 0)

    def test_fails_on_missing_sections(self):
        res = validate_claude_md("non_existent_file.md")
        self.assertFalse(res["success"])

if __name__ == "__main__":
    unittest.main()
