import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "claude_review.py"

spec = importlib.util.spec_from_file_location("claude_review", MODULE_PATH)
claude_review = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["claude_review"] = claude_review
spec.loader.exec_module(claude_review)
