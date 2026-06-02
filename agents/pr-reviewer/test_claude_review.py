#!/usr/bin/env python3
"""Smoke tests for the PR reviewer parser and heuristics."""

from __future__ import annotations

import io
import urllib.error

import claude_review as review


SAMPLE_DIFF = """diff --git a/src/old name.py b/src/new name.py
similarity index 87%
rename from src/old name.py
rename to src/new name.py
index 1111111..2222222 100644
--- a/src/old name.py
+++ b/src/new name.py
@@ -1,3 +1,4 @@
 context
-old line
+new line
+print("contest should not count as tests")
\\ No newline at end of file
diff --git a/tests/test_new_name.py b/tests/test_new_name.py
new file mode 100644
index 0000000..3333333
--- /dev/null
+++ b/tests/test_new_name.py
@@ -0,0 +1,2 @@
+def test_new_name():
+    assert True
diff --git a/src/delete_me.py b/src/delete_me.py
deleted file mode 100644
index 4444444..0000000
--- a/src/delete_me.py
+++ /dev/null
@@ -1,2 +0,0 @@
-removed
-content
diff --git a/src/old report.md b/src/old report.md
deleted file mode 100644
index 5555555..0000000
--- a/src/old report.md
+++ /dev/null
@@ -1 +0,0 @@
-legacy note
"""


def pr_for(files, added_lines=()):
    return review.PullRequestDiff(
        owner="owner",
        repo="repo",
        number="99",
        title="owner/repo#99",
        files=tuple(files),
        added_lines=tuple(added_lines),
        raw_diff="",
    )


def test_parse_paths_and_counts() -> None:
    parsed = review.parse_diff("owner", "repo", "1", SAMPLE_DIFF)
    assert [file.path for file in parsed.files] == [
        "src/new name.py",
        "tests/test_new_name.py",
        "src/delete_me.py",
        "src/old report.md",
    ]
    assert [(file.added, file.deleted) for file in parsed.files] == [(2, 1), (2, 0), (0, 2), (0, 1)]
    assert "\\ No newline at end of file" not in parsed.added_lines


def test_hunk_marker_like_content_is_counted() -> None:
    raw = """diff --git a/docs/example.md b/docs/example.md
index 1111111..2222222 100644
--- a/docs/example.md
+++ b/docs/example.md
@@ -1,2 +1,2 @@
--- old markdown fence
+++ new markdown fence
"""
    parsed = review.parse_diff("owner", "repo", "8", raw)
    assert parsed.files == (review.ChangedFile("docs/example.md", 1, 1),)
    assert parsed.added_lines == ("++ new markdown fence",)


def test_path_from_diff_header_uses_first_separator() -> None:
    assert (
        review.path_from_diff_header("diff --git a/src/old name.py b/src/new b name.py")
        == "src/new b name.py"
    )
    assert (
        review.path_from_diff_header('diff --git "a/src/old name.py" "b/src/new name.py"')
        == "src/new name.py"
    )
    assert review.path_from_diff_header("not a diff header") is None


def test_test_detection_uses_paths_only() -> None:
    parsed = review.parse_diff("owner", "repo", "1", SAMPLE_DIFF)
    assert review.has_test_file(parsed)

    no_test = review.PullRequestDiff(
        owner="owner",
        repo="repo",
        number="2",
        title="owner/repo#2",
        files=(review.ChangedFile("src/latest.py", 1, 0),),
        added_lines=("contest attestation",),
        raw_diff="",
    )
    assert not review.has_test_file(no_test)
    assert review.has_test_file(
        review.PullRequestDiff(
            owner="owner",
            repo="repo",
            number="4",
            title="owner/repo#4",
            files=(review.ChangedFile("hooks/destructive-bash-guard/test_block_destructive_bash.py", 1, 0),),
            added_lines=(),
            raw_diff="",
        )
    )
    assert review.has_test_file(
        review.PullRequestDiff(
            owner="owner",
            repo="repo",
            number="5",
            title="owner/repo#5",
            files=(
                review.ChangedFile("src/component.test.js", 1, 0),
                review.ChangedFile("src/component.spec.ts", 1, 0),
            ),
            added_lines=(),
            raw_diff="",
        )
    )
    assert not review.has_test_file(
        review.PullRequestDiff(
            owner="owner",
            repo="repo",
            number="6",
            title="owner/repo#6",
            files=(review.ChangedFile("docs/foo.specification.md", 1, 0),),
            added_lines=(),
            raw_diff="",
        )
    )


def test_risks_use_added_lines_not_removed_lines() -> None:
    raw = """diff --git a/app.py b/app.py
index 1111111..2222222 100644
--- a/app.py
+++ b/app.py
@@ -1,2 +1,2 @@
-os.system("rm -rf build")
+print("safe replacement")
"""
    parsed = review.parse_diff("owner", "repo", "3", raw)
    assert not any("destructive shell" in risk for risk in review.detect_risks(parsed))


def test_missing_test_risk_mentions_test_files_only() -> None:
    parsed = review.PullRequestDiff(
        owner="owner",
        repo="repo",
        number="7",
        title="owner/repo#7",
        files=(review.ChangedFile("src/app.py", 1, 0),),
        added_lines=("print('hello')",),
        raw_diff="",
    )
    risks = "\n".join(review.detect_risks(parsed))
    assert "No test file change is visible" in risks
    assert "test command" not in risks


def test_risk_detection_catches_shell_variants() -> None:
    raw = """diff --git a/deploy.sh b/deploy.sh
index 1111111..2222222 100644
--- a/deploy.sh
+++ b/deploy.sh
@@ -0,0 +1,3 @@
+rm -r -f build
+rm --recursive --force dist
+git push --force origin main
"""
    parsed = review.parse_diff("owner", "repo", "6", raw)
    assert any("destructive shell" in risk for risk in review.detect_risks(parsed))


def test_suggestions_cover_each_heuristic_branch() -> None:
    no_test = pr_for((review.ChangedFile("src/app.py", 1, 0),), ("print('hello')",))
    assert any("Add a small focused test" in item for item in review.suggestions(no_test))

    cli = pr_for(
        (review.ChangedFile("tests/test_cli.py", 1, 0), review.ChangedFile("src/cli.py", 1, 0)),
        ("parser = argparse.ArgumentParser()",),
    )
    assert any("exact CLI invocation" in item for item in review.suggestions(cli))

    sql = pr_for(
        (review.ChangedFile("tests/test_sql.py", 1, 0), review.ChangedFile("src/db.py", 1, 0)),
        ("cursor.execute('DELETE FROM users')",),
    )
    assert any("quoted SQL" in item for item in review.suggestions(sql))

    shell = pr_for(
        (review.ChangedFile("tests/test_hook.py", 1, 0), review.ChangedFile("hooks/bash_guard.py", 1, 0)),
        ("shell = 'bash'",),
    )
    assert any("allowed and one denied shell example" in item for item in review.suggestions(shell))

    fallback = pr_for((review.ChangedFile("tests/test_models.py", 1, 0), review.ChangedFile("src/models.py", 1, 0)))
    assert review.suggestions(fallback) == [
        "- Keep the PR scoped to the current behavior and add a regression example if a bug motivated it."
    ]


def test_confidence_boundaries() -> None:
    assert review.confidence(pr_for(())) == "Low - The diff did not expose changed files."
    assert review.confidence(pr_for((review.ChangedFile("src/app.py", 600, 0),))).startswith("High -")
    assert review.confidence(pr_for((review.ChangedFile("src/app.py", 601, 0),))).startswith("Medium -")


def test_validate_diff_response_rejects_json_payload() -> None:
    try:
        review.validate_diff_response('{"message":"API rate limit exceeded"}')
    except SystemExit as exc:
        assert "API rate limit exceeded" in str(exc)
        assert str(exc).endswith(".")
    else:
        raise AssertionError("Expected JSON API payload to be rejected")


def test_validate_diff_response_explains_json_without_message() -> None:
    try:
        review.validate_diff_response('{"errors":["missing"]}')
    except SystemExit as exc:
        assert "message field" in str(exc)
        assert "authentication" in str(exc)
    else:
        raise AssertionError("Expected JSON API payload without message to be rejected")


def test_parse_pr_url_includes_invalid_input() -> None:
    try:
        review.parse_pr_url("https://github.com/owner/repo/issues/123\n")
    except SystemExit as exc:
        assert "issues/123" in str(exc)
    else:
        raise AssertionError("Expected invalid PR URL to be rejected")


def test_http_error_includes_github_message() -> None:
    error = urllib.error.HTTPError(
        url="https://api.github.test/repos/o/r/pulls/1",
        code=403,
        msg="Forbidden",
        hdrs=None,
        fp=io.BytesIO(b'{"message":"API rate limit exceeded"}'),
    )
    formatted = review.format_http_error(error, error.url)
    assert "HTTP 403" in formatted
    assert "API rate limit exceeded" in formatted
    assert ". URL: https://api.github.test/repos/o/r/pulls/1" in formatted


def test_http_error_explains_json_without_message() -> None:
    error = urllib.error.HTTPError(
        url="https://api.github.test/repos/o/r/pulls/1",
        code=404,
        msg="Not Found",
        hdrs=None,
        fp=io.BytesIO(b'{"errors":["missing"]}'),
    )
    formatted = review.format_http_error(error, error.url)
    assert "message field" in formatted
    assert "PR visibility" in formatted


def test_github_headers_use_classic_token_scheme() -> None:
    previous = review.os.environ.get("GITHUB_TOKEN")
    review.os.environ["GITHUB_TOKEN"] = "example-token"
    try:
        assert review.github_headers()["Authorization"] == "token example-token"
    finally:
        if previous is None:
            review.os.environ.pop("GITHUB_TOKEN", None)
        else:
            review.os.environ["GITHUB_TOKEN"] = previous


def main() -> int:
    test_parse_paths_and_counts()
    test_hunk_marker_like_content_is_counted()
    test_path_from_diff_header_uses_first_separator()
    test_test_detection_uses_paths_only()
    test_risks_use_added_lines_not_removed_lines()
    test_missing_test_risk_mentions_test_files_only()
    test_risk_detection_catches_shell_variants()
    test_suggestions_cover_each_heuristic_branch()
    test_confidence_boundaries()
    test_validate_diff_response_rejects_json_payload()
    test_validate_diff_response_explains_json_without_message()
    test_parse_pr_url_includes_invalid_input()
    test_http_error_includes_github_message()
    test_http_error_explains_json_without_message()
    test_github_headers_use_classic_token_scheme()
    print("All PR reviewer checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
