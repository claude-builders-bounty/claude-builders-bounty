"""Synthetic unit fixtures for the evidence checker, never live-run evidence."""
import copy
import json
from pathlib import Path
import unittest
from check_execution_evidence import check


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.workflow = json.loads(Path(__file__).with_name(
            "weekly-github-claude-summary.workflow.json").read_text(encoding="utf-8"))
        runs = {node["name"]: [{"executionStatus": "success", "data": {"main": [[]]}}]
                for node in self.workflow["nodes"]}
        runs["Generate Claude Summary"][0]["data"]["main"] = [[
            {"json": {"content": [{"type": "text", "text": "SYNTHETIC summary"}]}}]]
        runs["Prepare Discord Message"][0]["data"]["main"] = [[
            {"json": {"message": "SYNTHETIC delivery"}}]]
        self.execution = {"status": "success", "finished": True,
                          "startedAt": "2026-01-01T00:00:00Z",
                          "stoppedAt": "2026-01-01T00:00:01Z", "data": {
                              "workflowData": copy.deepcopy(self.workflow),
                              "resultData": {"runData": runs}}}

    def reject(self):
        with self.assertRaises(ValueError):
            check(self.execution, self.workflow)

    def test_matching_structure(self):
        self.assertIn("owner must attest", check(self.execution, self.workflow))

    def test_failed_execution(self):
        self.execution["status"] = "error"
        self.reject()

    def test_unfinished(self):
        self.execution["finished"] = False
        self.reject()

    def test_missing_node(self):
        del self.execution["data"]["resultData"]["runData"]["Send Discord Summary"]
        self.reject()

    def test_node_error(self):
        self.execution["data"]["resultData"]["runData"]["Get Commits"][0]["error"] = {"message": "failed"}
        self.reject()

    def test_changed_endpoint(self):
        self.execution["data"]["workflowData"]["nodes"][6]["parameters"]["url"] = "http://localhost/mock"
        self.reject()

    def test_changed_execution_flags(self):
        for field, value in (("disabled", True), ("continueOnFail", True),
                             ("onError", "continueRegularOutput")):
            with self.subTest(field=field):
                changed = copy.deepcopy(self.execution)
                changed["data"]["workflowData"]["nodes"][-1][field] = value
                with self.assertRaises(ValueError):
                    check(changed, self.workflow)

    def test_explicit_default_execution_flags(self):
        for node in self.execution["data"]["workflowData"]["nodes"]:
            node.update(disabled=False, continueOnFail=False, onError="stopWorkflow")
        self.assertIn("owner must attest", check(self.execution, self.workflow))

    def test_missing_model_text(self):
        self.execution["data"]["resultData"]["runData"]["Generate Claude Summary"][0]["data"]["main"] = [[]]
        self.reject()

    def test_oversized_delivery(self):
        self.execution["data"]["resultData"]["runData"]["Prepare Discord Message"][0]["data"]["main"][0][0]["json"]["message"] = "x" * 1901
        self.reject()


if __name__ == "__main__":
    unittest.main()
