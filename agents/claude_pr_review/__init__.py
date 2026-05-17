"""Import shim for tests.

The runnable agent lives in agents/claude-pr-review so the directory name
matches the CLI package shown in the README. Python imports cannot contain a
hyphen, so tests load it through this small shim.
"""

import sys
from importlib import util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "claude-pr-review" / "claude_review.py"
spec = util.spec_from_file_location("claude_review", MODULE_PATH)
if spec is None or spec.loader is None:
    raise ImportError(f"Cannot load claude_review from {MODULE_PATH}")

claude_review = util.module_from_spec(spec)
sys.modules[spec.name] = claude_review
spec.loader.exec_module(claude_review)
