"""Local checks for the reviewer. No network access or model required."""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import types
import unittest
from unittest.mock import patch

loader = importlib.machinery.SourceFileLoader("reviewer", str(Path(__file__).resolve().parents[1] / "claude-review"))
spec = importlib.util.spec_from_loader(loader.name, loader)
reviewer = importlib.util.module_from_spec(spec)
loader.exec_module(reviewer)


class ReviewTests(unittest.TestCase):
    def test_render_and_escape(self):
        review = reviewer.static_facts("diff --git a/a b/a\n@@ -1 +1 @@\n")
        review["risks"] = ["<tag> @user"]
        text = reviewer.markdown(review)
        for heading in ("Summary", "Identified risks", "Improvement suggestions", "Confidence"):
            self.assertIn("## " + heading, text)
        self.assertIn("&lt;tag&gt; &#64;user", text)
        self.assertIn("1 text hunk", text)

    def test_bad_output_rejected(self):
        with self.assertRaises(ValueError):
            reviewer.markdown({"summary": ["missing fields"]})
        review = reviewer.static_facts("")
        review["confidence"] = "Always"
        with self.assertRaises(ValueError):
            reviewer.markdown(review)

    def test_revision_change_rejected(self):
        with patch.object(reviewer, "revisions", side_effect=[("a", "b"), ("a", "c")]), \
             patch.object(reviewer, "request", return_value=b"diff --git a/x b/x\n"):
            with self.assertRaisesRegex(ValueError, "changed"):
                reviewer.snapshot("unused")

    def test_agent_arguments_without_credentials(self):
        payload = reviewer.static_facts("")
        proc = types.SimpleNamespace(returncode=0, stdout=json.dumps({"structured_output": payload}))
        with patch.dict(os.environ, {"GITHUB_TOKEN":"fake-data", "GH_TOKEN":"fake-data"}), \
             patch.object(reviewer.subprocess, "run", return_value=proc) as run:
            self.assertEqual(reviewer.run_agent("example diff"), payload)
        argv = run.call_args.args[0]
        self.assertEqual(argv[argv.index("--tools") + 1], "")
        self.assertEqual(argv[argv.index("--agent") + 1], "diff-reviewer")
        self.assertIn("--restricted", argv)
        self.assertNotIn("GITHUB_TOKEN", run.call_args.kwargs["env"])
        self.assertNotIn("GH_TOKEN", run.call_args.kwargs["env"])
        self.assertEqual(run.call_args.kwargs["input"], "example diff")

    def test_sequential_repost_reuses_existing_comment(self):
        comments = [{"user": {"id": 7}, "body": "review\n<!-- claude-review:a:b -->", "html_url": "receipt"}]
        responses = [b'{"id":7}', json.dumps(comments).encode()]
        with patch.object(reviewer, "request", side_effect=responses) as req:
            self.assertEqual(reviewer.publish("unused", 10, ("a", "b"), "review", "fake"), "receipt")
            self.assertEqual(req.call_count, 2)

    def test_publish_refuses_a_new_revision(self):
        with patch.object(reviewer, "request", side_effect=[b'{"id":7}', b'[]']) as req, \
             patch.object(reviewer, "revisions", return_value=("a", "new")):
            with self.assertRaisesRegex(ValueError, "changed"):
                reviewer.publish("unused", 10, ("a", "b"), "review", "fake")
            self.assertEqual(req.call_count, 2)


if __name__ == "__main__":
    unittest.main()
