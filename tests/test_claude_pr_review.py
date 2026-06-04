from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "agents" / "claude-pr-review" / "claude_review.py"
MOCK = json.dumps(
    {
        "summary": "This PR updates the greeting logic and adds a regression test for the changed behavior. The diff is small and easy to inspect, with no persistence or network changes.",
        "risks": ["The new behavior may affect callers that expected the previous greeting text."],
        "suggestions": ["Document the changed greeting contract in the README if it is user-visible."],
        "confidence": "High",
    }
)


def load_module() -> ModuleType:
    import importlib.util

    spec = importlib.util.spec_from_file_location("claude_review", CLI)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["claude_review"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(CLI), *args], text=True, capture_output=True, check=False)


def test_rejects_invalid_pr_url() -> None:
    result = run_cli("--pr", "https://example.com/not/a/pr", "--mock-review-json", MOCK)
    assert result.returncode == 1
    assert "PR URL must look like" in result.stderr


def test_renders_structured_markdown_with_mock(monkeypatch, capsys) -> None:
    module = load_module()

    monkeypatch.setattr(module, "fetch_pr_diff", lambda pr, token=None: "diff --git a/app.py b/app.py\n+print('hello')\n")
    rc = module.main([
        "--pr",
        "https://github.com/octocat/Hello-World/pull/1",
        "--mock-review-json",
        MOCK,
    ])
    assert rc == 0
    stdout = capsys.readouterr().out
    assert "## Claude PR Review" in stdout
    assert "### Summary" in stdout
    assert "### Identified risks" in stdout
    assert "### Improvement suggestions" in stdout
    assert "### Confidence score" in stdout
    assert "High" in stdout


def test_escapes_code_fences_in_diff() -> None:
    module = load_module()
    pr = module.parse_pr_url("https://github.com/octocat/Hello-World/pull/1")
    prompt = module.build_prompt(pr, "diff --git a/a b/a\n+```\n+malicious fence\n")
    assert "+`\u200b``" in prompt
    assert "+```\n+malicious" not in prompt


def test_output_file_written_with_mock(monkeypatch, tmp_path) -> None:
    module = load_module()

    monkeypatch.setattr(module, "fetch_pr_diff", lambda pr, token=None: "diff --git a/README.md b/README.md\n+hello\n")
    output = tmp_path / "review.md"
    rc = module.main([
        "--pr",
        "https://github.com/octocat/Hello-World/pull/1",
        "--mock-review-json",
        MOCK,
        "--output",
        str(output),
    ])
    assert rc == 0
    content = output.read_text(encoding="utf-8")
    assert "## Claude PR Review" in content
    assert "### Identified risks" in content
    assert "### Improvement suggestions" in content
    assert "### Confidence score" in content
    assert "High" in content
