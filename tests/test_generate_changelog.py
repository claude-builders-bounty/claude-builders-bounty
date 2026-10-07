import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from skills.generate_changelog.changelog import (
    categorize_commit,
    generate_changelog_markdown,
)


def test_categorize_commit_added():
    cat, msg = categorize_commit("feat(auth): add OAuth2 provider support")
    assert cat == "Added"
    assert msg == "Add OAuth2 provider support"


def test_categorize_commit_fixed():
    cat, msg = categorize_commit("fix(db): resolve connection pool memory leak")
    assert cat == "Fixed"
    assert msg == "Resolve connection pool memory leak"


def test_categorize_commit_removed():
    cat, msg = categorize_commit("remove deprecated legacy API endpoint")
    assert cat == "Removed"
    assert "deprecated legacy API" in msg


def test_categorize_commit_changed():
    cat, msg = categorize_commit("refactor: simplify user session handler")
    assert cat == "Changed"


def test_generate_changelog_markdown_output():
    commits = [
        "feat(core): add multi-language support",
        "fix(ui): fix modal positioning bug",
        "docs: update installation instructions",
        "remove legacy theme assets",
    ]

    output = generate_changelog_markdown(commits, tag="v1.0.0")

    assert "# CHANGELOG" in output
    assert "## Added" in output
    assert "## Fixed" in output
    assert "## Changed" in output
    assert "## Removed" in output
    assert "- Add multi-language support" in output
    assert "- Fix modal positioning bug" in output
