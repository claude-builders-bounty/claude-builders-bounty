from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "changelog-generator" / "generate_changelog.py"

spec = importlib.util.spec_from_file_location("generate_changelog", SCRIPT)
module = importlib.util.module_from_spec(spec)
sys.modules["generate_changelog"] = module
assert spec.loader is not None
spec.loader.exec_module(module)


def test_categorize_conventional_commits() -> None:
    assert module.categorize("feat: add dashboard") == "Added"
    assert module.categorize("fix(auth): repair login") == "Fixed"
    assert module.categorize("docs: update readme") == "Documentation"
    assert module.categorize("plain commit") == "Other"


def test_render_changelog_groups_commits() -> None:
    commits = [
        module.Commit("abc1234", "feat: add dashboard"),
        module.Commit("def5678", "fix: repair login"),
        module.Commit("fed4321", "plain commit"),
    ]
    output = module.render_changelog(commits, "v1.0.0")

    assert "# Changelog" in output
    assert "Changes since `v1.0.0`" in output
    assert "### Added" in output
    assert "- add dashboard (abc1234)" in output
    assert "### Fixed" in output
    assert "### Other" in output
