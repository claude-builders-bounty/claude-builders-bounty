"""Validate the n8n weekly-dev-summary workflow JSON.

The tests check:
  * the file parses as JSON
  * it has the required top-level fields (name, nodes, connections)
  * every node has the required fields (id, name, type, typeVersion, position, parameters)
  * node types come from the supported n8n base set
  * every connection target references a real node name
  * the trigger node is a Schedule Trigger with a weekly cron expression
  * the workflow contains the expected logical nodes (GitHub fetch x3, Claude,
    merge, format, deliver) — case-insensitive substring match on name

Run with:  python3 -m unittest tests.test_workflow_json -v
or:        pytest tests/test_workflow_json.py -v
"""
from __future__ import annotations

import json
import os
import re
import sys
import unittest
from pathlib import Path

# Resolve the workflow file relative to this test file so it works no matter
# where pytest / unittest is invoked from.
HERE = Path(__file__).resolve().parent
WORKFLOW_PATH = HERE.parent / "weekly_summary_workflow.json"

# n8n built-in node types we use. See:
#   https://docs.n8n.io/integrations/builtin/
ALLOWED_NODE_TYPES = {
    "n8n-nodes-base.scheduleTrigger",
    "n8n-nodes-base.cron",
    "n8n-nodes-base.httpRequest",
    "n8n-nodes-base.code",
    "n8n-nodes-base.set",
    "n8n-nodes-base.if",
    "n8n-nodes-base.switch",
    "n8n-nodes-base.merge",
    "n8n-nodes-base.noOp",
    "n8n-nodes-base.emailSend",
    "n8n-nodes-base.discord",
    "n8n-nodes-base.slack",
}


class TestWorkflowJson(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not WORKFLOW_PATH.exists():
            raise unittest.SkipTest(f"Workflow JSON not found at {WORKFLOW_PATH}")
        with WORKFLOW_PATH.open() as f:
            cls.wf = json.load(f)

    # ---- Top-level structure ------------------------------------------------

    def test_parses_as_json(self) -> None:
        self.assertIsInstance(self.wf, dict)

    def test_required_top_level_fields(self) -> None:
        for field in ("name", "nodes", "connections"):
            self.assertIn(field, self.wf, f"missing top-level field: {field}")

    def test_nodes_is_list(self) -> None:
        self.assertIsInstance(self.wf["nodes"], list)
        self.assertGreater(len(self.wf["nodes"]), 0, "workflow has no nodes")

    def test_connections_is_dict(self) -> None:
        self.assertIsInstance(self.wf["connections"], dict)

    # ---- Per-node shape -----------------------------------------------------

    def test_every_node_has_required_fields(self) -> None:
        required = {"id", "name", "type", "typeVersion", "position", "parameters"}
        for n in self.wf["nodes"]:
            missing = required - n.keys()
            self.assertFalse(missing, f"node {n.get('name')!r} missing fields: {missing}")

    def test_node_types_are_supported(self) -> None:
        for n in self.wf["nodes"]:
            self.assertIn(
                n["type"], ALLOWED_NODE_TYPES,
                f"unsupported node type {n['type']!r} on node {n['name']!r}",
            )

    def test_node_ids_are_unique(self) -> None:
        ids = [n["id"] for n in self.wf["nodes"]]
        self.assertEqual(len(ids), len(set(ids)), "duplicate node ids")

    def test_node_names_are_unique(self) -> None:
        names = [n["name"] for n in self.wf["nodes"]]
        self.assertEqual(len(names), len(set(names)), "duplicate node names")

    def test_position_is_two_numbers(self) -> None:
        for n in self.wf["nodes"]:
            pos = n["position"]
            self.assertIsInstance(pos, list)
            self.assertEqual(len(pos), 2, f"node {n['name']!r}: position must be 2D")
            for coord in pos:
                self.assertIsInstance(coord, (int, float))

    # ---- Connections -------------------------------------------------------

    def test_all_connection_sources_are_node_names(self) -> None:
        names = {n["name"] for n in self.wf["nodes"]}
        for src in self.wf["connections"]:
            self.assertIn(src, names, f"connection from unknown source node: {src!r}")

    def test_all_connection_targets_are_node_names(self) -> None:
        names = {n["name"] for n in self.wf["nodes"]}
        for src, conn in self.wf["connections"].items():
            for branch in conn.get("main", []):
                for c in branch:
                    self.assertIn(c["node"], names,
                                  f"connection from {src!r} targets unknown node {c['node']!r}")
                    self.assertEqual(c["type"], "main")
                    self.assertIsInstance(c["index"], int)

    def test_workflow_is_connected(self) -> None:
        """Every non-trigger node should be reachable as a source, target, or both."""
        names = {n["name"] for n in self.wf["nodes"]}
        sources = set(self.wf["connections"].keys())
        targets: set[str] = set()
        for conn in self.wf["connections"].values():
            for branch in conn.get("main", []):
                for c in branch:
                    targets.add(c["node"])

        triggers = {n["name"] for n in self.wf["nodes"]
                    if n["type"] in ("n8n-nodes-base.scheduleTrigger", "n8n-nodes-base.cron")}
        reachable = sources | targets | triggers
        unreachable = names - reachable
        self.assertFalse(unreachable, f"unreachable nodes: {unreachable}")

    def test_workflow_has_no_orphan_edges(self) -> None:
        """Every non-trigger node should appear as a connection source (i.e. the graph
        has a clear start -> ... -> end path; terminal nodes are allowed to have no
        outgoing edges)."""
        sources = set(self.wf["connections"].keys())
        non_triggers = {n["name"] for n in self.wf["nodes"]
                        if n["type"] not in ("n8n-nodes-base.scheduleTrigger",
                                             "n8n-nodes-base.cron")}
        # Every non-trigger node should at least be a source, except the terminal one.
        targets: set[str] = set()
        for conn in self.wf["connections"].values():
            for branch in conn.get("main", []):
                for c in branch:
                    targets.add(c["node"])
        terminals = non_triggers - targets
        for t in terminals:
            self.assertIn(t, sources,
                          f"terminal node {t!r} is not a connection source")

    # ---- Trigger & cron ----------------------------------------------------

    def test_has_weekly_trigger(self) -> None:
        triggers = [n for n in self.wf["nodes"]
                    if n["type"] in ("n8n-nodes-base.scheduleTrigger", "n8n-nodes-base.cron")]
        self.assertTrue(triggers, "no schedule/cron trigger node found")

    def test_cron_expression_is_weekly(self) -> None:
        triggers = [n for n in self.wf["nodes"]
                    if n["type"] in ("n8n-nodes-base.scheduleTrigger", "n8n-nodes-base.cron")]
        expressions: list[str] = []
        for t in triggers:
            rule = t["parameters"].get("rule", {})
            for interval in rule.get("interval", []):
                if interval.get("field") == "cronExpression":
                    expressions.append(interval.get("expression", ""))
        self.assertTrue(expressions, "no cronExpression set on trigger")
        for expr in expressions:
            fields = expr.split()
            self.assertEqual(len(fields), 5, f"cron must have 5 fields, got {expr!r}")
            # 5 = Friday per standard cron (0 = Sun … 5 = Fri … 6 = Sat)
            self.assertEqual(fields[4], "5", f"cron {expr!r} is not on Friday")
            # 17 = 5pm
            self.assertEqual(fields[1], "17", f"cron {expr!r} is not at 17:xx")

    # ---- Logical completeness ---------------------------------------------

    def _node_names(self) -> list[str]:
        return [n["name"] for n in self.wf["nodes"]]

    def test_has_github_fetch_nodes(self) -> None:
        names = " ".join(self._node_names()).lower()
        for required in ("commit", "issue", "pr"):
            self.assertIn(required, names, f"no node covering GitHub {required!r} data")

    def test_has_claude_api_node(self) -> None:
        names = " ".join(self._node_names()).lower()
        self.assertTrue(
            "claude" in names or "anthropic" in names,
            "no node mentioning Claude / Anthropic",
        )

    def test_has_delivery_node(self) -> None:
        names = " ".join(self._node_names()).lower()
        delivered = any(k in names for k in ("discord", "slack", "email", "webhook", "send"))
        self.assertTrue(delivered, "no delivery (discord/slack/email/webhook) node")

    def test_uses_required_claude_model(self) -> None:
        """Search node params for the required claude-sonnet-4-20250514 string."""
        target = "claude-sonnet-4-20250514"
        for n in self.wf["nodes"]:
            params_blob = json.dumps(n.get("parameters", {}))
            if target in params_blob:
                return
        self.fail(f"no node references the required model {target!r}")


class TestDryRunScript(unittest.TestCase):
    """Smoke-test the dry_run.py helper without making any network calls."""

    def setUp(self) -> None:
        self.dry_run = HERE.parent / "dry_run.py"
        if not self.dry_run.exists():
            self.skipTest("dry_run.py not found")

    def test_dry_run_script_parses(self) -> None:
        import ast
        ast.parse(self.dry_run.read_text())

    def test_dry_run_help_runs(self) -> None:
        import subprocess
        out = subprocess.run(
            [sys.executable, str(self.dry_run), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(out.returncode, 0, msg=out.stderr)
        self.assertIn("Simulate", out.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
