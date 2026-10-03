import importlib.util, os, pathlib, stat, tempfile

P = pathlib.Path(__file__).parents[1] / "claude_review.py"
s = importlib.util.spec_from_file_location("review", P)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)


def test_parse():
    assert m.parse_pr("https://github.com/o/r/pull/12") == ("o", "r", "12")


def test_output_shape():
    out = m.fallback_review("diff --git a/a.py b/a.py\n+def x(): return 1\n")
    for h in ["## Summary", "## Risks", "## Improvement suggestions", "## Confidence"]:
        assert h in out


def test_claude_binary_path_is_used(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        fake = pathlib.Path(tmp) / "claude"
        fake.write_text(
            "#!/usr/bin/env python3\n"
            "import sys\n"
            "assert sys.argv[1] == '-p'\n"
            "print('## Summary\\nTwo sentences. Second sentence.\\n\\n## Risks\\n- None identified.\\n\\n## Improvement suggestions\\n- None.\\n\\n## Confidence\\nHigh')\n",
            encoding="utf-8",
        )
        fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
        monkeypatch.setenv("CLAUDE_BIN", str(fake))
        out = m.review_with_claude("diff --git a/a b/a\n+safe change\n")
        assert out is not None
        assert "## Summary" in out
        assert "## Confidence\nHigh" in out

def test_invalid_claude_output_falls_back(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        fake = pathlib.Path(tmp) / 'claude'
        fake.write_text(
            '#!/usr/bin/env python3\n'
            "print('unstructured answer')\n",
            encoding='utf-8',
        )
        fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
        monkeypatch.setenv('CLAUDE_BIN', str(fake))
        assert m.review_with_claude('diff --git a/a b/a\n+safe change\n') is None


def test_valid_review_contract():
    good = '''## Summary
Two sentences. Second sentence.

## Risks
- None identified.

## Improvement suggestions
- None.

## Confidence
High
'''
    assert m.valid_review(good)
    assert not m.valid_review(good.replace('High', 'Very High'))
    assert not m.valid_review('## Summary\nOnly one section\n')

def test_fallback_does_not_count_unified_diff_headers():
    diff = "diff --git a/test.txt b/test.txt\n--- a/test.txt\n+++ b/test.txt\n@@ -1 +1 @@\n-old\n+new\n"
    assert "1 added and 1 removed lines" in m.fallback_review(diff)


def test_empty_sections_are_rejected():
    good = m.fallback_review("diff --git a/test.txt b/test.txt\n+new\n")
    for heading, next_heading in [
        ("Summary", "Risks"),
        ("Risks", "Improvement suggestions"),
        ("Improvement suggestions", "Confidence"),
    ]:
        start = good.index("## " + heading) + len("## " + heading)
        end = good.index("## " + next_heading)
        assert not m.valid_review(good[:start] + "\n\n" + good[end:])


def test_risk_and_suggestion_sections_require_lists():
    good = m.fallback_review("diff --git a/test.txt b/test.txt\n+new\n")
    assert not m.valid_review(good.replace("- No high-signal", "No high-signal"))
    assert not m.valid_review(good.replace("- Keep the regression", "Keep the regression"))


def test_reordered_or_duplicate_headings_are_rejected():
    good = m.fallback_review("diff --git a/test.txt b/test.txt\n+new\n")
    swapped = good.replace("## Risks", "## TEMP").replace("## Improvement suggestions", "## Risks").replace("## TEMP", "## Improvement suggestions")
    assert not m.valid_review(swapped)
    assert not m.valid_review(good.replace("## Risks", "## Risks\n- First list.\n\n## Risks"))


def test_confidence_cannot_have_trailing_unstructured_output():
    good = m.fallback_review("diff --git a/test.txt b/test.txt\n+new\n")
    assert not m.valid_review(good + "\nUnstructured trailing answer.\n")


def test_claude_timeout_or_launch_error_returns_fallback_signal(monkeypatch):
    monkeypatch.setattr(m.shutil, "which", lambda _: "/test/claude")
    for error in [m.subprocess.TimeoutExpired("claude", 120), OSError("binary disappeared")]:
        def fail(*args, **kwargs):
            raise error
        monkeypatch.setattr(m.subprocess, "run", fail)
        assert m.review_with_claude("diff --git a/test.txt b/test.txt\n+new\n") is None


def test_claude_receives_the_standalone_output_contract(monkeypatch):
    monkeypatch.setattr(m.shutil, "which", lambda _: "/test/claude")
    observed = {}
    good = m.fallback_review("diff --git a/test.txt b/test.txt\n+new\n")
    def run(args, **kwargs):
        observed["prompt"] = args[2]
        observed["timeout"] = kwargs["timeout"]
        return m.subprocess.CompletedProcess(args, 0, stdout=good, stderr="")
    monkeypatch.setattr(m.subprocess, "run", run)
    assert m.review_with_claude("diff --git a/test.txt b/test.txt\n+new\n") is not None
    assert "## Summary, ## Risks, ## Improvement suggestions, ## Confidence" in observed["prompt"]
    assert "non-empty bullet lists" in observed["prompt"]
    assert observed["timeout"] == 120
