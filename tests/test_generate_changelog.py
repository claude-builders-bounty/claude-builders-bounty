from scripts.generate_changelog import classify, render


def test_classify_conventional_commit_types():
    assert classify("feat(parser): add sections") == "Features"
    assert classify("fix: handle empty log") == "Fixes"
    assert classify("docs: update readme") == "Documentation"
    assert classify("unknown message") == "Other"


def test_render_groups_commits():
    markdown = render([("abc1234", "feat: add cli"), ("def5678", "fix: empty output")], "v1..HEAD")
    assert "## v1..HEAD" in markdown
    assert "### Features" in markdown
    assert "- `abc1234` feat: add cli" in markdown
    assert "### Fixes" in markdown
