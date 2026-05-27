import importlib.util
import sys
from pathlib import Path


_module_path = Path(__file__).resolve().parent / "pr-reviewer" / "claude_review.py"
_spec = importlib.util.spec_from_file_location("claude_review", _module_path)
claude_review = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
sys.modules["claude_review"] = claude_review
_spec.loader.exec_module(claude_review)
