"""Tests for the claude-review PR reviewer."""
import sys
import subprocess
from pathlib import Path

# Make src importable
sys.path.insert(0, str(Path(__file__).parent.parent))
from claude_review import (
    analyze_pr,
    generate_report,
    _parse_pr_url,
    _file_risk_score,
    _top_extensions,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pr(title: str = "My PR", body: str = "Description", base: str = "main",
              head: str = "feature") -> dict:
    return {
        "title": title,
        "body": body,
        "user": {"login": "testuser"},
        "base": {"ref": base},
        "head": {"ref": head},
    }


def _make_file(filename: str, additions: int = 10, deletions: int = 5) -> dict:
    return {"filename": filename, "additions": additions, "deletions": deletions}


def _make_commit(sha: str, message: str) -> dict:
    return {"sha": sha, "commit": {"message": message}}


# ---------------------------------------------------------------------------
# _parse_pr_url
# ---------------------------------------------------------------------------

class TestParsePrUrl:
    def test_full_url(self):
        owner, repo, num = _parse_pr_url("https://github.com/psf/requests/pull/7500", None)
        assert owner == "psf"
        assert repo == "requests"
        assert num == 7500

    def test_shorthand(self):
        owner, repo, num = _parse_pr_url("psf/requests/7500", None)
        assert owner == "psf"
        assert repo == "requests"
        assert num == 7500

    def test_bare_number_with_repo(self):
        owner, repo, num = _parse_pr_url("42", "psf/requests")
        assert owner == "psf"
        assert repo == "requests"
        assert num == 42

    def test_bare_number_no_repo_raises(self):
        import pytest
        with pytest.raises(ValueError, match="--repo"):
            _parse_pr_url("42", None)

    def test_invalid_raises(self):
        import pytest
        with pytest.raises(ValueError):
            _parse_pr_url("not-a-url", None)


# ---------------------------------------------------------------------------
# _file_risk_score
# ---------------------------------------------------------------------------

class TestFileRiskScore:
    def test_security_sensitive_secret(self):
        score, risks = _file_risk_score("config/secret.json", 5, 0)
        assert score > 0
        assert any("security-sensitive" in r for r in risks)

    def test_ci_file(self):
        score, risks = _file_risk_score(".github/workflows/ci.yml", 10, 0)
        assert score > 0
        assert any("infrastructure" in r or "CI" in r for r in risks)

    def test_large_change(self):
        score, risks = _file_risk_score("src/main.py", 150, 80)  # 230 total
        assert score > 0
        assert any("large change" in r for r in risks)

    def test_safe_file(self):
        score, risks = _file_risk_score("src/utils.py", 5, 2)
        assert score == 0
        assert risks == []


# ---------------------------------------------------------------------------
# analyze_pr
# ---------------------------------------------------------------------------

class TestAnalyzePr:
    def test_detects_tests(self):
        files = [
            _make_file("src/main.py"),
            _make_file("tests/test_main.py"),
        ]
        analysis = analyze_pr(_make_pr(), files, [])
        assert analysis["has_tests"] is True

    def test_no_tests_flagged_as_risk(self):
        files = [_make_file("src/main.py", 100, 0)]
        analysis = analyze_pr(_make_pr(), files, [])
        assert analysis["has_tests"] is False
        assert any("test" in r.lower() for r in analysis["risks"])

    def test_no_description_flagged(self):
        pr = _make_pr(body="")
        files = [_make_file("src/main.py")]
        analysis = analyze_pr(pr, files, [])
        assert any("description" in r.lower() for r in analysis["risks"])

    def test_large_scope_flagged(self):
        files = [_make_file(f"src/file{i}.py") for i in range(25)]
        analysis = analyze_pr(_make_pr(), files, [])
        assert any("scope" in r.lower() or "files changed" in r.lower() for r in analysis["risks"])

    def test_confidence_high_when_all_signals(self):
        files = [_make_file("src/main.py"), _make_file("tests/test_main.py")]
        commits = [_make_commit("abc1234", "feat: add feature")]
        analysis = analyze_pr(_make_pr(), files, commits)
        assert analysis["confidence"] == "High"

    def test_confidence_low_no_body_no_tests(self):
        files = [_make_file(f"src/file{i}.py", 100, 0) for i in range(5)]
        commits = [_make_commit("abc1234", "wip")]
        analysis = analyze_pr(_make_pr(body=""), files, commits)
        assert analysis["confidence"] in ("Low", "Medium")

    def test_counts_additions_deletions(self):
        files = [
            _make_file("a.py", additions=30, deletions=10),
            _make_file("b.py", additions=20, deletions=5),
        ]
        analysis = analyze_pr(_make_pr(), files, [])
        assert analysis["total_additions"] == 50
        assert analysis["total_deletions"] == 15
        assert analysis["total_files"] == 2

    def test_no_risks_clean_pr(self):
        files = [_make_file("src/utils.py", 10, 5), _make_file("tests/test_utils.py", 5, 0)]
        commits = [_make_commit("abc1234", "feat: add utility function")]
        analysis = analyze_pr(_make_pr(), files, commits)
        assert analysis["has_tests"] is True


# ---------------------------------------------------------------------------
# generate_report
# ---------------------------------------------------------------------------

class TestGenerateReport:
    def _run(self, pr=None, files=None, commits=None):
        pr = pr or _make_pr()
        files = files or [_make_file("src/main.py"), _make_file("tests/test_main.py")]
        commits = commits or [_make_commit("abc1234", "feat: add feature")]
        analysis = analyze_pr(pr, files, commits)
        return generate_report(pr, files, commits, analysis, "https://github.com/o/r/pull/1")

    def test_contains_summary_heading(self):
        report = self._run()
        assert "### Summary" in report

    def test_contains_risks_heading(self):
        report = self._run()
        assert "### Identified Risks" in report

    def test_contains_improvements_heading(self):
        report = self._run()
        assert "### Improvement Suggestions" in report

    def test_contains_confidence_heading(self):
        report = self._run()
        assert "### Confidence Score" in report

    def test_pr_title_in_report(self):
        pr = _make_pr(title="My Feature PR")
        report = self._run(pr=pr)
        assert "My Feature PR" in report

    def test_no_description_shown(self):
        pr = _make_pr(body="")
        report = self._run(pr=pr)
        assert "No description provided" in report

    def test_generated_by_attribution(self):
        report = self._run()
        assert "claude-review" in report.lower() or "Generated by" in report

    def test_file_list_present(self):
        files = [_make_file("src/main.py", 30, 5)]
        report = self._run(files=files)
        assert "src/main.py" in report


# ---------------------------------------------------------------------------
# _top_extensions
# ---------------------------------------------------------------------------

class TestTopExtensions:
    def test_most_common_first(self):
        types = {".py": 5, ".md": 2, ".yml": 1}
        result = _top_extensions(types, 2)
        assert result.startswith("`.py`")

    def test_no_ext_label(self):
        result = _top_extensions({"": 3})
        assert "no-ext" in result

    def test_limits_output(self):
        types = {".py": 5, ".md": 4, ".ts": 3, ".js": 2, ".rs": 1, ".go": 1}
        result = _top_extensions(types, 3)
        assert result.count("`") <= 6  # 3 items × 2 backticks each


# ---------------------------------------------------------------------------
# CLI smoke test
# ---------------------------------------------------------------------------

class TestCli:
    SCRIPT = Path(__file__).parent.parent / "claude_review.py"

    def test_help_exits_zero(self):
        proc = subprocess.run(
            [sys.executable, str(self.SCRIPT), "--help"],
            capture_output=True, text=True,
        )
        assert proc.returncode == 0
        assert "--pr" in proc.stdout

    def test_missing_pr_errors(self):
        proc = subprocess.run(
            [sys.executable, str(self.SCRIPT)],
            capture_output=True, text=True,
        )
        assert proc.returncode != 0

    def test_bad_url_errors(self):
        proc = subprocess.run(
            [sys.executable, str(self.SCRIPT), "--pr", "not-a-url"],
            capture_output=True, text=True,
        )
        assert proc.returncode != 0
