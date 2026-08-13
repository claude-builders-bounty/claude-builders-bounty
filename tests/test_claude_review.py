import importlib.machinery
import importlib.util
from pathlib import Path
import sys


SCRIPT = Path(__file__).parents[1] / "claude-review"
loader = importlib.machinery.SourceFileLoader("claude_review", str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
module = importlib.util.module_from_spec(spec)
sys.modules[loader.name] = module
loader.exec_module(module)


def test_parse_and_review_are_deterministic():
    diff = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1 +1 @@
-print('old')
+print('new')
diff --git a/tests/test_app.py b/tests/test_app.py
--- /dev/null
+++ b/tests/test_app.py
@@ -0,0 +1 @@
+assert True
"""
    stats = module.parse_diff(diff)
    output = module.review({"title": "Change output"}, stats)

    assert stats.files == ["app.py", "tests/test_app.py"]
    assert stats.additions == 2
    assert stats.deletions == 1
    assert "## Summary" in output
    assert "## Risks" in output
    assert "## Suggestions" in output
    assert "## Confidence\n\n**High**" in output
    assert output == module.review({"title": "Change output"}, stats)


def test_uncovered_large_diff_reports_risks():
    stats = module.DiffStats(files=["src/auth/session.py"], additions=501)
    output = module.review({"title": "Sessions"}, stats)

    assert "No test changes" in output
    assert "large patch size" in output
    assert "Security- or payment-sensitive" in output
    assert output.endswith("**Medium**\n")


def test_lockfile_migration_and_truncated_diff_are_flagged():
    diff = """diff --git a/package-lock.json b/package-lock.json
--- a/package-lock.json
+++ b/package-lock.json
@@ -1 +1 @@
-{}
+{"lockfileVersion": 3}
diff --git a/db/migrations/001_add_users.sql b/db/migrations/001_add_users.sql
--- /dev/null
+++ b/db/migrations/001_add_users.sql
@@ -0,0 +1 @@
+CREATE TABLE users(id INTEGER PRIMARY KEY);
"""
    stats = module.parse_diff(diff, truncated=True)
    output = module.review({"title": "Dependencies and schema"}, stats)

    assert stats.files == ["package-lock.json", "db/migrations/001_add_users.sql"]
    assert stats.truncated is True
    assert "diff exceeded 2 MB" in output
    assert "Dependency lockfiles changed" in output
    assert "Schema or migration changes" in output
    assert output.endswith("**Low**\n")


def test_pr_url_validation_accepts_only_public_pull_urls():
    assert module.PR_URL.fullmatch("https://github.com/owner-name/repo.name/pull/123")
    assert not module.PR_URL.fullmatch("https://github.com/owner/repo/issues/123")
    assert not module.PR_URL.fullmatch("https://github.com/owner/repo/pull/0")
    assert not module.PR_URL.fullmatch("https://evil.example/owner/repo/pull/123")
