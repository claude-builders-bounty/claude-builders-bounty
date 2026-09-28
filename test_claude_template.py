"""Static documentation regressions; not a Claude Code or application E2E test."""
import json
from pathlib import Path
import re
import unittest

TEXT=Path(__file__).with_name('CLAUDE.md').read_text(encoding='utf-8')

class TemplateTests(unittest.TestCase):
    def test_expected_sections(self):
        for section in ('Stack & Versions','Folder Structure','Naming Conventions','SQL & Database Migration Rules','Component & Architecture Patterns',"What We Don't Do (And Why)"):
            self.assertIn('## '+section,TEXT)
    def test_script_contract_is_valid_json(self):
        data=json.loads(re.search(r'```json\n(.*?)\n```',TEXT,re.S)[1])
        self.assertEqual(data['scripts']['build'],'next build')
        self.assertEqual(data['scripts']['typecheck'],'tsc --noEmit')
        self.assertEqual(data['scripts']['db:migrate'],'drizzle-kit migrate')
    def test_consistent_component_filename(self):
        self.assertIn('submit-button.tsx',TEXT);self.assertNotIn('SubmitButton.tsx',TEXT)
    def test_auth_and_tenant_boundaries(self):
        self.assertIn('database-backed sessions',TEXT)
        self.assertIn('inside every action',TEXT)
        self.assertIn('authenticated tenant',TEXT)
    def test_database_enforcement_and_runtime(self):
        self.assertIn('PRAGMA foreign_keys = ON',TEXT)
        self.assertIn('Node.js runtime',TEXT)
        self.assertIn('persistent writable volume',TEXT)
    def test_no_false_build_or_validation_claim(self):
        self.assertNotIn('runs typecheck + db:generate',TEXT)
        self.assertIn('not a claim that Claude Code was executed',TEXT)
    def test_paths_and_configuration_match(self):
        self.assertIn("schema: './src/db/schema.ts'",TEXT)
        self.assertIn("out: './drizzle'",TEXT)
        self.assertIn('same file path',TEXT)
    def test_invalid_typescript_example_removed(self):
        self.assertNotIn('interface BillingProps =',TEXT)
        self.assertIn('interface BillingProps { userId: string }',TEXT)

if __name__=='__main__':unittest.main(verbosity=2)
