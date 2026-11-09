#!/usr/bin/env python3
"""Verification for the CLAUDE.md template (issue #2).

Two layers:
  A. Template self-checks: required sections, the issue's "Expected
     Sections", opinionated rules that each carry a reason, commands,
     pinned versions, and no leftover placeholders (usable unmodified).
  B. Greenfield consistency: against a real create-next-app scaffold
     (path passed as argv[1], default the saved test project), every
     directory in the template's folder structure must exist, and the
     core commands (dev/build/start/lint/typecheck) must exist in the
     scaffold's package.json.

Run: python3 tests/verify_template.py [path-to-scaffold]
"""

import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "CLAUDE.md")
SCAFFOLD = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
    "~/workspace/goals/weekly-automated-income-runs/hidden_files/"
    "greenfield-test")

with open(TEMPLATE, encoding="utf-8") as fh:
    TEXT = fh.read()


class TemplateSelfChecks(unittest.TestCase):
    def test_issue_expected_sections(self):
        for needle in ("Stack & versions", "Folder structure",
                       "migration", "Component", "What we don't do"):
            self.assertIn(needle.lower(), TEXT.lower(), needle)

    def test_acceptance_topics_covered(self):
        low = TEXT.lower()
        for needle in ("project structure", "naming conventions",
                       "migration rules", "dev commands", "patterns",
                       "anti-pattern"):
            # "folder structure"/"what we don't do" are the same topics
            # under the headings the issue itself suggested
            if needle == "project structure":
                needle = "folder structure"
            if needle == "anti-pattern":
                needle = "what we don't do"
            self.assertIn(needle, low, needle)

    def test_stack_is_pinned(self):
        for needle in ("Next.js", "15.x", "React", "19", "Node.js", "20",
                       "better-sqlite3", "TypeScript"):
            self.assertIn(needle, TEXT, needle)

    def test_dev_commands_present(self):
        for cmd in ("npm run dev", "npm run build", "npm run lint",
                    "npm run typecheck", "npm run test",
                    "npm run db:migrate"):
            self.assertIn(cmd, TEXT, cmd)

    def test_every_dont_has_a_reason(self):
        section = TEXT.split("## What we don't do")[1]
        # Bullets wrap across lines: group each "- **" start with its
        # continuation lines before checking for the reason clause.
        blocks, current = [], None
        for ln in section.splitlines():
            if ln.startswith("- **"):
                if current:
                    blocks.append(current)
                current = ln
            elif current and ln.startswith("  "):
                current += " " + ln.strip()
        if current:
            blocks.append(current)
        bullets = blocks
        self.assertGreaterEqual(len(bullets), 8)
        for bullet in bullets:
            self.assertTrue(
                "— because" in bullet or "—" in bullet and "because" in bullet,
                f"anti-pattern without a reason: {bullet[:60]}")

    def test_key_rules_carry_reasons(self):
        # The opinionated core: each rule's because-clause must exist.
        for phrase in ("Never edit, rename, or delete a migration",
                       "Prepared statements only",
                       "No ORM",
                       "database-backed",
                       "Server Components by default"):
            self.assertIn(phrase, TEXT, phrase)
        self.assertGreaterEqual(TEXT.lower().count("because"), 15)

    def test_no_placeholders(self):
        for bad in ("TODO", "FIXME", "Lorem", "{{", "<project",
                    "your-project", "XXX"):
            self.assertNotIn(bad, TEXT, bad)

    def test_sqlite_specifics(self):
        for needle in ("WAL", "foreign_keys", "server-only",
                       "runtime = \"nodejs\"", "unix milliseconds",
                       "_migrations"):
            self.assertIn(needle, TEXT, needle)


@unittest.skipUnless(os.path.isdir(SCAFFOLD), "scaffold not present")
class GreenfieldConsistency(unittest.TestCase):
    def test_template_copied_in_unmodified(self):
        with open(os.path.join(SCAFFOLD, "CLAUDE.md"),
                  encoding="utf-8") as fh:
            self.assertEqual(fh.read(), TEXT)

    def test_prescribed_directories_exist(self):
        for rel in ("src/app/(marketing)", "src/app/(app)", "src/app/api",
                    "src/features", "src/components/ui", "src/lib/db",
                    "src/lib/db/migrations"):
            self.assertTrue(os.path.isdir(os.path.join(SCAFFOLD, rel)),
                            rel)

    def test_core_commands_exist_in_package_json(self):
        with open(os.path.join(SCAFFOLD, "package.json")) as fh:
            scripts = json.load(fh)["scripts"]
        for cmd in ("dev", "build", "start", "lint", "typecheck"):
            self.assertIn(cmd, scripts, cmd)

    def test_scaffold_stack_matches_template(self):
        with open(os.path.join(SCAFFOLD, "package.json")) as fh:
            pkg = json.load(fh)
        self.assertTrue(pkg["dependencies"]["next"].startswith("15."),
                        pkg["dependencies"]["next"])
        self.assertTrue(pkg["dependencies"]["react"].startswith("19."),
                        pkg["dependencies"]["react"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
