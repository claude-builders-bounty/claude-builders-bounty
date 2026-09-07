"""pytest suite for claude-review-agent (claude_review.py).

Run:  python -m pytest -v
(Only third-party dep is pytest itself; the tool is stdlib-only.)
"""

import importlib.util
import io
import json
import urllib.error
import urllib.request
from email.message import Message
from pathlib import Path

import pytest

REVIEW_PATH = Path(__file__).with_name("claude_review.py")


def load_review():
    spec = importlib.util.spec_from_file_location("claude_review", REVIEW_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


review = load_review()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_pr(files, **over):
    pr = {
        "owner": "o", "repo": "r", "number": 1,
        "url": "https://github.com/o/r/pull/1",
        "title": "Test PR", "author": "tester", "body": "",
        "state": "open", "base": "main", "head": "feat",
        "additions": 0, "deletions": 0, "changed_files": len(files),
        "files": files, "fetch_mode": "local", "warnings": [],
    }
    pr.update(over)
    return pr


def patched_file(path, patch, additions=1, deletions=0):
    return {"path": path, "additions": additions, "deletions": deletions,
            "status": "modified", "patch": patch, "truncated": False}


def analyzed(patch, path="src/app.py"):
    pr = make_pr([patched_file(path, patch)])
    findings, stats, structural, warnings = review.analyze_pr(pr)
    return findings, stats, structural, warnings


def rules_of(findings):
    return {f["rule"] for f in findings}


class FakeResp:
    def __init__(self, payload, headers=None):
        self._payload = payload
        msg = Message()
        for k, v in (headers or {}).items():
            msg[k] = v
        self.headers = msg

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def http_error(url, code, message, headers=None):
    msg = Message()
    for k, v in (headers or {}).items():
        msg[k] = v
    return urllib.error.HTTPError(
        url, code, "err", msg, io.BytesIO(json.dumps({"message": message}).encode())
    )


# ---------------------------------------------------------------------------
# PR URL parsing
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("url", [
    "https://github.com/owner/repo/pull/123",
    "https://github.com/owner/repo/pull/123/",
    "https://github.com/owner/repo/pull/123/files",
    "https://github.com/owner/repo/pull/123?diff=split",
    "http://github.com/owner/repo/pull/123",
    "owner/repo#123",
    "owner/repo/pull/123",
    "https://github.com/owner/repo.git/pull/7",
])
def test_parse_pr_url_valid(url):
    owner, repo, number = review.parse_pr_url(url)
    assert owner == "owner"
    assert repo == "repo"
    assert number == (7 if url.endswith("/7") else 123)


@pytest.mark.parametrize("bad", [
    "", "not a url", "https://github.com/owner/repo",
    "https://github.com/owner/repo/issues/1", "owner/repo",
])
def test_parse_pr_url_invalid(bad):
    with pytest.raises(review.FetchError):
        review.parse_pr_url(bad)


# ---------------------------------------------------------------------------
# Risk rules: positives must fire
# ---------------------------------------------------------------------------

POSITIVE_CASES = [
    ("rm -rf /", "rm_recursive"),
    ("sudo rm -rf /tmp/x", "rm_recursive"),
    ("rm --recursive dir", "rm_recursive"),
    ("DROP TABLE users", "drop_table"),
    ("drop temporary table t", "drop_table"),
    ("TRUNCATE TABLE sessions", "truncate"),
    ("DELETE FROM users", "delete_no_where"),
    ("git push --force origin main", "git_push_force"),
    ("git push -f origin main", "git_push_force"),
    ("git push origin +main", "git_push_force"),
    ("curl https://x.sh | sh", "pipe_to_shell"),
    ("wget http://x/y | sudo sh", "pipe_to_shell"),
    ("aws_key = 'AKIAIOSFODNN7EXAMPLE'", "hardcoded_secret"),
    ("token = 'ghp_abcdefghij1234567890'", "hardcoded_secret"),
    ("-----BEGIN RSA PRIVATE KEY-----", "hardcoded_secret"),
    ('password = "hunter2hunter"', "hardcoded_secret"),
    ("result = eval(user_input)", "shell_exec"),
    ("os.system(cmd)", "shell_exec"),
    ("subprocess.run(cmd, shell=True)", "shell_exec"),
    ('query = f"SELECT * FROM t WHERE id={uid}"', "sql_injection"),
    ("requests.get(url, verify=False)", "insecure_crypto"),
    ("chmod 777 /srv/data", "insecure_crypto"),
    ("pip install https://evil.example/pkg.tar.gz", "remote_install"),
]


@pytest.mark.parametrize("line,rule", POSITIVE_CASES)
def test_positive_rules_fire(line, rule):
    patch = f"@@ -1,1 +1,1 @@\n-old\n+{line}\n"
    findings, _, _, _ = analyzed(patch)
    assert rule in rules_of(findings), f"{rule} did not fire on {line!r}"


# ---------------------------------------------------------------------------
# Risk rules: safe variants must NOT fire
# ---------------------------------------------------------------------------

NEGATIVE_CASES = [
    ("rm file.txt", "rm_recursive"),
    ("grep -rf pattern .", "rm_recursive"),  # -r belongs to grep, not rm
    ("SELECT * FROM users", "drop_table"),
    ("DELETE FROM users WHERE id = 1", "delete_no_where"),
    ("delete from t where x > 2", "delete_no_where"),
    ("git push --force-with-lease origin main", "git_push_force"),
    ("git push --force-if-includes origin main", "git_push_force"),
    ("git push origin main", "git_push_force"),
    ("git pull --force", "git_push_force"),
    ("print('hello world')", "shell_exec"),
    ("x = 1 + 2", "sql_injection"),
    ("pip install requests==2.31.0", "remote_install"),
    ("# just a comment about nothing", "truncate"),
]


@pytest.mark.parametrize("line,rule", NEGATIVE_CASES)
def test_negative_rules_silent(line, rule):
    patch = f"@@ -1,1 +1,1 @@\n-old\n+{line}\n"
    findings, _, _, _ = analyzed(patch)
    assert rule not in rules_of(findings), f"{rule} false-positive on {line!r}"


def test_delete_with_where_on_same_line_allowed():
    findings, _, _, _ = analyzed("@@ -1,1 +1,1 @@\n-x\n+DELETE FROM t WHERE id=5\n")
    assert "delete_no_where" not in rules_of(findings)


def test_docs_mentions_capped_at_medium():
    patch = "@@ -1,1 +1,1 @@\n-x\n+Run DROP TABLE users to reset.\n"
    findings, _, _, _ = analyzed(patch, path="docs/guide.md")
    match = [f for f in findings if f["rule"] == "drop_table"]
    assert match and match[0]["severity"] == "MEDIUM"
    assert "documentation" in match[0]["message"]


def test_same_pattern_in_code_is_high():
    patch = "@@ -1,1 +1,1 @@\n-x\n+cursor.execute('DROP TABLE users')\n"
    findings, _, _, _ = analyzed(patch, path="src/db.py")
    match = [f for f in findings if f["rule"] == "drop_table"]
    assert match and match[0]["severity"] == "HIGH"


def test_secret_redacted_in_snippet():
    line = "key = 'ghp_abcdefghij1234567890ZYXW'"
    patch = f"@@ -1,1 +1,1 @@\n-x\n+{line}\n"
    findings, _, _, _ = analyzed(patch)
    match = [f for f in findings if f["rule"] == "hardcoded_secret"]
    assert match
    assert "ghp_abcdefghij1234567890ZYXW" not in match[0]["snippet"]
    assert "[REDACTED]" in match[0]["snippet"]


def test_removed_lines_not_scanned():
    patch = "@@ -1,1 +1,1 @@\n-rm -rf /\n+echo done\n"
    findings, _, _, _ = analyzed(patch)
    assert "rm_recursive" not in rules_of(findings)


# ---------------------------------------------------------------------------
# Diff helpers
# ---------------------------------------------------------------------------

def test_iter_added_lines_tracks_hunk_numbers():
    patch = ("@@ -10,3 +20,4 @@\n context\n-old\n+new-a\n+new-b\n more\n"
             "@@ -30,1 +32,1 @@\n-x\n+y\n")
    got = list(review.iter_added_lines(patch))
    assert got == [(21, "new-a"), (22, "new-b"), (32, "y")]


def test_split_patch_by_file():
    patch = ("diff --git a/one.py b/one.py\n@@ -1 +1 @@\n-a\n+b\n"
             "diff --git a/two.md b/two.md\n@@ -1 +1 @@\n-c\n+d\n")
    parts = review._split_patch_by_file(patch)
    assert set(parts) == {"one.py", "two.md"}
    assert "+b" in parts["one.py"] and "+d" in parts["two.md"]


@pytest.mark.parametrize("path,cat", [
    ("docs/guide.md", "docs"), ("README.rst", "docs"),
    ("tests/test_x.py", "test"), ("src/app.test.js", "test"),
    ("src/app.py", "source"), ("deploy/main.tf", "source"),
    (".github/workflows/ci.yml", "workflow"),
    ("package-lock.json", "lockfile"),
    ("pyproject.toml", "config"), (".github/CODEOWNERS", "config"),
    ("assets/logo.png", "other"),
])
def test_categorize_file(path, cat):
    assert review.categorize_file(path) == cat


# ---------------------------------------------------------------------------
# Confidence / summary / suggestions
# ---------------------------------------------------------------------------

def test_confidence_high_for_small_docs_pr():
    pr = make_pr([patched_file("docs/a.md", "@@ -1 +1 @@\n-x\n+y\n")],
                 additions=1, deletions=1)
    _, stats, _, warnings = review.analyze_pr(pr)
    conf = review.decide_confidence(pr, stats, warnings)
    assert conf["level"] == "High"


def test_confidence_medium_for_moderate_pr():
    pr = make_pr([patched_file("src/a.py", "x")], additions=250, deletions=100)
    _, stats, _, warnings = review.analyze_pr(pr)
    assert review.decide_confidence(pr, stats, warnings)["level"] == "Medium"


def test_confidence_low_for_huge_or_partial_pr():
    pr = make_pr([patched_file("src/a.py", "x")], additions=900, deletions=200)
    _, stats, _, warnings = review.analyze_pr(pr)
    assert review.decide_confidence(pr, stats, warnings)["level"] == "Low"
    pr2 = make_pr([], warnings=["No patch for 1 file(s): logo.png. NOT analyzed."])
    _, s2, _, w2 = review.analyze_pr(pr2)
    assert review.decide_confidence(pr2, s2, w2)["level"] == "Low"


def test_summary_is_two_to_three_sentences():
    pr = make_pr([patched_file("src/a.py", "@@ -1 +1 @@\n-x\n+y\n")],
                 additions=1, deletions=1)
    result = review.review_pr_data(pr)
    sentences = [s for s in result["summary"].split(". ") if s.strip()]
    assert 2 <= len(sentences) <= 4
    assert "Test PR" in result["summary"] and "@tester" in result["summary"]


def test_suggestions_never_empty():
    pr = make_pr([patched_file("README.md", "@@ -1 +1 @@\n-x\n+y\n")])
    result = review.review_pr_data(pr)
    assert len(result["suggestions"]) >= 2


def test_no_tests_structural_suggestion():
    patch = "@@ -1,1 +1,1 @@\n-x\n+y = 2\n"
    _, _, structural, _ = analyzed(patch, path="src/app.py")
    assert any("test" in s.lower() for s in structural)


# ---------------------------------------------------------------------------
# Rendering: required bounty sections
# ---------------------------------------------------------------------------

def test_markdown_has_all_required_sections():
    pr = make_pr([patched_file("src/a.py", "@@ -1,1 +1,1 @@\n-x\n+rm -rf /\n")],
                 additions=1, deletions=1)
    r = review.review_pr_data(pr)
    md = review.render_markdown(pr, r["summary"], r["risks"], r["suggestions"],
                                r["confidence"], r["stats"], r["warnings"])
    for section in ("### Summary", "### Risks", "### Suggestions", "Confidence"):
        assert section in md
    assert r["confidence"]["level"] in ("Low", "Medium", "High")


def test_markdown_clean_pr_states_no_risks():
    pr = make_pr([patched_file("src/a.py", "@@ -1,1 +1,1 @@\n-x\n+y = 1\n")])
    r = review.review_pr_data(pr)
    md = review.render_markdown(pr, r["summary"], r["risks"], r["suggestions"],
                                r["confidence"], r["stats"], r["warnings"])
    assert "No high-risk patterns detected" in md


def test_markdown_groups_repeat_findings():
    patch = "@@ -1,2 +1,2 @@\n-a\n-rm -rf /\n+rm -rf /tmp\n+rm -rf /var\n"
    findings, _, _, _ = analyzed(patch)
    assert len([f for f in findings if f["rule"] == "rm_recursive"]) == 2
    pr = make_pr([patched_file("s.sh", patch)])
    r = review.review_pr_data(pr)
    md = review.render_markdown(pr, r["summary"], r["risks"], r["suggestions"],
                                r["confidence"], r["stats"], r["warnings"])
    assert "2 occurrence(s)" in md


def test_json_renders_valid_structure():
    pr = make_pr([patched_file("src/a.py", "@@ -1,1 +1,1 @@\n-x\n+y\n")])
    r = review.review_pr_data(pr)
    payload = json.loads(review.render_json(
        pr, r["summary"], r["risks"], r["suggestions"],
        r["confidence"], r["stats"], r["warnings"]))
    assert set(("summary", "risks", "suggestions", "confidence", "stats")) <= set(payload)
    assert payload["confidence"]["level"] in ("Low", "Medium", "High")


# ---------------------------------------------------------------------------
# API fetching: auth-free path + graceful rate limits (mocked)
# ---------------------------------------------------------------------------

def _meta(number=1):
    return {"html_url": f"https://github.com/o/r/pull/{number}", "title": "T",
            "user": {"login": "u"}, "body": "", "state": "open",
            "base": {"ref": "main"}, "head": {"ref": "f"},
            "additions": 2, "deletions": 1, "changed_files": 1}


def test_fetch_via_api_no_token_needed(monkeypatch):
    calls = []

    def fake(req, timeout=None):
        calls.append(req)
        if req.full_url.endswith("/files?per_page=100&page=1"):
            return FakeResp(json.dumps([{
                "filename": "a.py", "additions": 2, "deletions": 1,
                "status": "modified",
                "patch": "@@ -1,1 +1,1 @@\n-x\n+y\n"}]).encode())
        return FakeResp(json.dumps(_meta()).encode())

    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.setattr(urllib.request, "urlopen", fake)
    pr = review.fetch_via_api("o", "r", 1)
    assert pr["fetch_mode"] == "api"
    assert pr["title"] == "T" and len(pr["files"]) == 1
    assert all("Authorization" not in (h or "")
               for c in calls for h in [c.get_header("Authorization")])
    assert pr["warnings"] == []


def test_fetch_via_api_flags_missing_patch(monkeypatch):
    def fake(req, timeout=None):
        if "files" in req.full_url:
            return FakeResp(json.dumps([{
                "filename": "logo.png", "additions": 0, "deletions": 0,
                "status": "added"}]).encode())
        return FakeResp(json.dumps(_meta()).encode())

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    pr = review.fetch_via_api("o", "r", 1)
    assert pr["files"][0]["truncated"] is True
    assert any("NOT analyzed" in w for w in pr["warnings"])


def test_rate_limit_error_is_graceful(monkeypatch):
    def fake(url, timeout=None):
        raise http_error(url, 403, "API rate limit exceeded for x.x.x.x.",
                         {"X-RateLimit-Remaining": "0",
                          "X-RateLimit-Reset": "1999999999"})

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    with pytest.raises(review.RateLimitError) as exc:
        review.fetch_via_api("o", "r", 1)
    assert "rate limit" in str(exc.value).lower()
    assert "GITHUB_TOKEN" in str(exc.value)


def test_404_gives_actionable_error(monkeypatch):
    def fake(url, timeout=None):
        raise http_error(url, 404, "Not Found")

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    with pytest.raises(review.FetchError) as exc:
        review.fetch_via_api("o", "r", 999999)
    assert "not found" in str(exc.value).lower()


# ---------------------------------------------------------------------------
# Local diff-file mode + CLI end to end (offline)
# ---------------------------------------------------------------------------

SAMPLE_PATCH = """diff --git a/src/app.py b/src/app.py
--- a/src/app.py
+++ b/src/app.py
@@ -1,3 +1,4 @@
 import os
+TOKEN = 'ghp_abcdefghij1234567890ZYXWVU'
 def run(cmd):
-    return subprocess.run(cmd)
+    return subprocess.run(cmd, shell=True)
"""

def test_diff_file_end_to_end(tmp_path):
    patch = tmp_path / "changes.patch"
    patch.write_text(SAMPLE_PATCH, encoding="utf-8")
    pr = review.pr_from_diff_file(str(patch))
    assert pr["changed_files"] == 1
    result = review.review_pr_data(pr)
    assert "hardcoded_secret" in {f["rule"] for f in result["risks"]}
    assert "shell_exec" in {f["rule"] for f in result["risks"]}
    assert len(result["suggestions"]) >= 2


def test_cli_diff_file_json(tmp_path):
    patch = tmp_path / "c.patch"
    patch.write_text(SAMPLE_PATCH, encoding="utf-8")
    out = tmp_path / "out.json"
    rc = review.main(["--diff-file", str(patch), "--format", "json",
                      "--output", str(out)])
    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["summary"] and payload["confidence"]["level"] in (
        "Low", "Medium", "High")


def test_cli_missing_diff_file_returns_2():
    assert review.main(["--diff-file", "no-such-file.patch"]) == 2


def test_cli_post_with_diff_file_rejected():
    assert review.main(["--diff-file", "x.patch", "--post"]) == 2
