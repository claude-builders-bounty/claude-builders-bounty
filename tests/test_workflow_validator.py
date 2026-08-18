import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from workflow_validator import validate_n8n_workflow

class TestN8nWorkflowValidator(unittest.TestCase):
    def test_validates_production_n8n_workflow(self):
        workflow_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'n8n_weekly_dev_summary.json'))
        res = validate_n8n_workflow(workflow_path)
        self.assertTrue(res["success"], f"Validation failed: {res}")
        self.assertEqual(len(res["missing_nodes"]), 0)
        self.assertTrue(res["has_claude_model"])

    def test_fails_on_invalid_filepath(self):
        res = validate_n8n_workflow("non_existent_workflow.json")
        self.assertFalse(res["success"])

if __name__ == "__main__":
    unittest.main()
