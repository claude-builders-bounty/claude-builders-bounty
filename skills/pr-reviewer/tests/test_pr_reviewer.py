"""Acceptance tests for conservative, diff-grounded PR reviews."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).parents[1] / "scripts" / "generate_review.py"
spec = importlib.util.spec_from_file_location("generate_review", SCRIPT)
reviewer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reviewer)


def metadata(**extra):
    value = {"title": "Example", "body": "", "files": [],
             "additions": 4, "deletions": 1, "changedFiles": 2}
    value.update(extra)
    return value


def patch_for(files=("src/a.py", "tests/test_a.py"), added=("one", "two"), deleted=()):
    chunks = []
    for name in files:
        old = len(deleted)
        new = len(added)
        if old and new:
            hunk = f"@@ -1,{old} +1,{new} @@"
        elif old:
            hunk = f"@@ -1,{old} +0,0 @@"
        else:
            hunk = f"@@ -0,0 +1,{new} @@"
        lines = [f"diff --git a/{name} b/{name}",
                 "--- /dev/null" if not old else f"--- a/{name}",
                 "+++ /dev/null" if not new else f"+++ b/{name}", hunk]
        lines += [f"-{line}" for line in deleted] + [f"+{line}" for line in added]
        chunks.append("\n".join(lines) + "\n")
    return "".join(chunks)


def report(meta, patch):
    analysis = reviewer.finalize_analysis(reviewer.analyze_diff(patch), patch)
    return analysis, reviewer.generate_report(meta, analysis)


def test_report_is_grounded_in_patch_and_has_required_sections():
    analysis, output = report(metadata(), patch_for())
    assert analysis["reviewable"] is True
    assert analysis["total_additions"] == 4
    assert analysis["files_changed"] == ["src/a.py", "tests/test_a.py"]
    assert "Diff evidence" in output
    for section in ("Summary", "Code Quality", "Risks", "Security", "Tests", "Documentation", "Suggestions", "Confidence"):
        assert section in output
    summary = next(line for line in output.splitlines() if line.startswith("- **Change summary:**"))
    assert summary.count(". ") >= 1 and summary.endswith(".")
    assert "patch " in summary
    assert "regression coverage" in summary or "test coverage" in summary


def test_small_clean_change_never_gets_easy_high_confidence():
    analysis, output = report(metadata(additions=2, deletions=0, changedFiles=1), patch_for(("tests/test_a.py",)))
    assert analysis["reviewable"] is True
    assert "**Confidence:** Medium" in output
    assert "**Confidence:** High" not in output


def test_confidence_is_semantic_not_a_schema_decoration():
    # A mutation that unconditionally returns High must fail these gates.
    cases = [
        (patch_for(("tests/test_a.py",), added=("one", "two")), metadata(additions=2, deletions=0, changedFiles=1)),
        (patch_for(("src/a.py", "tests/test_a.py"),
                   added=tuple(f"assert line{i}" for i in range(12))),
         metadata(additions=24, deletions=0, changedFiles=2)),
        (patch_for(("generated/app.js", "tests/test_a.py"), added=tuple(f"line{i}" for i in range(12))),
         metadata(additions=24, deletions=0, changedFiles=2)),
    ]
    for index, (patch, meta) in enumerate(cases):
        analysis, output = report(meta, patch)
        level = reviewer.confidence_level(analysis, reviewer._metadata_context(meta, analysis)[1])
        if index == 1:
            assert level == "High"
            assert "**Confidence:** High" in output
        else:
            assert level != "High"
            assert "**Confidence:** High" not in output


def test_metadata_is_not_authoritative_when_partial_or_mismatched():
    _, output = report({"title": "Partial"}, patch_for())
    assert "Uncertainty" in output
    assert "Confidence:** High" not in output
    _, output = report(metadata(additions=999, changedFiles=99), patch_for())
    assert "metadata claims 999 additions" in output


def test_security_finding_is_specific_and_docs_example_is_not_code_finding():
    code = patch_for(("app.py",), ('password = "not-a-real-secret"', "return True"))
    analysis, output = report(metadata(additions=2, deletions=0, changedFiles=1), code)
    assert analysis["security_flags"][0]["label"] == "Hardcoded credential"
    assert "Hardcoded credential" in output
    docs = patch_for(("docs/security.md",), ('password = "example-only"', "Never commit credentials."))
    analysis, output = report(metadata(additions=2, deletions=0, changedFiles=1), docs)
    assert not analysis["security_flags"]
    assert "not counted as a code finding" in output


def test_wording_based_suppression_cannot_be_used_to_bypass_detection_in_source():
    # Regression for an exact-SHA audit finding: real source could evade
    # detection purely by echoing the suppression's own trigger wording
    # (`password = "hardcoded credential: ..."`) in the added line. There
    # must be no content string that suppresses a finding in a source file.
    bypass_attempts = (
        'password = "hardcoded credential: actual_prod_password_123"',
        'password="Hardcoded Credential: prod-pass-1"',
        'password  =  "this is a hardcoded credential for real"',
        'api_key = "hardcoded credential token abcdefghijkl123456"',
        'secret = "not a real example, hardcoded credential anyway"',
    )
    for line in bypass_attempts:
        code = patch_for(("app.py",), (line, "return True"))
        analysis, output = report(metadata(additions=2, deletions=0, changedFiles=1), code)
        assert analysis["security_flags"], f"bypassed for: {line}"
        assert not analysis["security_notes"], f"wrongly noted instead of flagged: {line}"
        assert "❌" in output and "not counted as a code finding" not in output


def test_docs_directory_does_not_launder_executable_or_config_files():
    # Placing real source/config under a docs/ path must not make it
    # unreviewable: `_is_docs` must classify by extension first, so an
    # executable or config file cannot borrow documentation's suppression
    # just by living in a docs/ directory.
    laundering_attempts = (
        ("docs/setup.py", 'password = "SuperSecretProdPass1!"'),
        ("docs/config.yml", 'api_key = "AKIAABCDEFGHIJKLMNOP"'),
        ("docs/deploy.sh", 'secret = "prod-deploy-secret-value"'),
        ("docs/settings.env", 'private_key = "-----BEGIN-RSA-PRIVATE-KEY-----"'),
    )
    for path, line in laundering_attempts:
        assert reviewer._is_docs(path) is False, path
        code = patch_for((path,), (line, "return True"))
        analysis, output = report(metadata(additions=2, deletions=0, changedFiles=1), code)
        assert analysis["security_flags"], f"laundered via docs/ path: {path}"
        assert "❌" in output


def test_docs_path_classification_still_covers_genuine_documentation():
    # Genuine prose documentation (by extension, or extensionless files
    # under docs/) keeps its example-suppression behavior.
    genuine_docs = ("docs/security.md", "guide.rst", "notes.adoc", "readme.txt",
                     "docs/CHANGELOG", "sub/docs/security.mdx")
    for path in genuine_docs:
        assert reviewer._is_docs(path) is True, path
        docs = patch_for((path,), ('password = "example-only"', "Never commit credentials."))
        analysis, output = report(metadata(additions=2, deletions=0, changedFiles=1), docs)
        assert not analysis["security_flags"], path
        assert "not counted as a code finding" in output, path


def test_deletion_heavy_patch_is_reviewable_and_reports_actual_counts():
    analysis, output = report(metadata(additions=0, deletions=4, changedFiles=1),
                              patch_for(("old.py",), added=(), deleted=("a", "b", "c", "d")))
    assert analysis["reviewable"] is True
    assert "Diff evidence" in output and "+0/-4" in output
    summary = next(line for line in output.splitlines() if line.startswith("- **Change summary:**"))
    assert "removes" in summary and "<code>a</code>" in summary
    assert summary.count(". ") >= 1


def test_summary_describes_config_and_docs_changes_without_symbols_or_behavior_terms():
    for path, lines, marker in (
        ("config.py", ("retry_count = 3", "timeout_seconds = 20"), "retry_count"),
        ("README.md", ("Install with the package manager", "Configure the timeout"), "Install"),
    ):
        analysis, output = report(metadata(additions=2, deletions=0, changedFiles=1),
                                  patch_for((path,), added=lines))
        assert analysis["reviewable"] is True
        summary = next(line for line in output.splitlines() if line.startswith("- **Change summary:**"))
        assert marker in summary
        assert summary.count(". ") >= 1


def test_summary_preserves_punctuation_in_changed_evidence():
    patch = patch_for(("config.py",),
                      added=('VERSION = "1.2.3"', 'API_URL = "https://api.example.com/v1"'))
    _, output = report(metadata(additions=2, deletions=0, changedFiles=1), patch)
    summary = next(line for line in output.splitlines() if line.startswith("- **Change summary:**"))
    assert '1&#46;2&#46;3' in summary
    assert 'https://api&#46;example&#46;com/v1' in summary
    assert '1·2·3' not in summary


def test_summary_bounds_sentence_count_and_protects_markdown_delimiters():
    patch = patch_for(("README.md",), added=(
        "Install dependencies. Configure timeout. Run service. Verify health.",
        "Example: const cmd = `npm test`;",
    ))
    _, output = report(metadata(additions=2, deletions=0, changedFiles=1), patch)
    summary = next(line for line in output.splitlines() if line.startswith("- **Change summary:**"))
    assert summary.count(". ") == 1
    assert "&#46;" in summary
    assert "&#96;npm test&#96;" in summary
    assert "<code>" in summary and "</code>" in summary


def test_empty_and_trivial_diffs_are_explicit_no_review():
    for patch in ("", patch_for(("README.md",), added=("new",), deleted=("old",))):
        analysis, output = report(metadata(), patch)
        assert analysis["reviewable"] is False
        assert "No review" in output
        assert "insufficient input" in output
        assert "No review performed" in output
        summary = next(line for line in output.splitlines() if line.startswith("- **Change summary:**"))
        assert summary.count(".") == 2


def test_malformed_diff_is_safe_failure_not_a_polished_review():
    analysis, output = report(metadata(), "diff --git a/app.py b/app.py\n@@ broken\n+password = 'x'\n")
    assert analysis["reviewable"] is False
    assert "unsafe input" in output
    assert "No security analysis performed" in output


def test_hunk_counts_and_file_headers_are_strictly_validated():
    valid = ("diff --git a/src/a.py b/src/a.py\n--- a/src/a.py\n+++ b/src/a.py\n"
             "@@ -1,1 +1,2 @@\n-old\n+new\n+another\n")
    assert reviewer.finalize_analysis(reviewer.analyze_diff(valid), valid)["reviewable"]

    truncated = valid.replace("+another\n", "")
    analysis, output = report(metadata(additions=1, deletions=1, changedFiles=1), truncated)
    assert analysis["malformed"] is True
    assert analysis["reviewable"] is False
    assert "unsafe input" in output

    missing_headers = ("diff --git a/src/a.py b/src/a.py\n@@ -0,0 +1,1 @@\n+new\n")
    analysis, _ = report(metadata(additions=1, deletions=0, changedFiles=1), missing_headers)
    assert analysis["malformed"] is True
    assert analysis["reviewable"] is False


def test_action_does_not_interpolate_or_allow_output_path_escape():
    action = (Path(__file__).parents[1] / "action.yml").read_text()
    assert '--output "$OUTPUT_FILE"' in action
    assert 'cat -- "$OUTPUT_FILE"' in action
    assert '--output ${{ inputs.output_file }}' not in action
    assert 'cat ${{ inputs.output_file }}' not in action
    assert 'output_file must be a non-empty path inside the workspace' in action


def test_truncated_git_binary_patch_is_rejected_as_malformed():
    patch = ("diff --git a/x.bin b/x.bin\n"
             "GIT binary patch\n")
    analysis, output = report(metadata(changedFiles=1), patch)
    assert analysis["input_state"] == "rejected"
    assert analysis["reviewable"] is False
    assert "no payload" in output


def test_real_git_binary_payload_is_accepted_and_truncation_rejected(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
    blob = repo / "x.bin"
    blob.write_bytes(bytes(range(256)) * 16 + b" braces {}")
    subprocess.run(["git", "-C", str(repo), "add", "x.bin"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "before"], check=True)
    blob.write_bytes(bytes(reversed(range(256))) * 16 + b" changed {}")
    patch = subprocess.check_output(["git", "-C", str(repo), "diff", "--binary", "HEAD"], text=True)
    assert "GIT binary patch" in patch
    assert "{" in patch and "}" in patch

    analysis, _ = report(metadata(additions=0, deletions=0, changedFiles=1), patch)
    assert analysis["input_state"] == "limited"
    assert analysis["reviewable"] is False

    truncated_lines = patch.splitlines()
    payload_index = max(index for index, line in enumerate(truncated_lines) if line)
    truncated_lines[payload_index] = truncated_lines[payload_index][:-1]
    truncated = "\n".join(truncated_lines) + "\n"
    analysis, output = report(metadata(changedFiles=1), truncated)
    assert analysis["input_state"] == "rejected"
    assert "truncated or malformed" in output


def test_binary_marker_cannot_be_followed_by_textual_hunks():
    patch = ("diff --git a/app.py b/app.py\n"
             "Binary files a/app.py and b/app.py differ\n"
             "@@ -1,1 +1,1 @@\n-old\n+new\n")
    analysis, output = report(metadata(), patch)
    assert analysis["malformed"] is True
    assert analysis["reviewable"] is False
    assert "unsafe input" in output


def test_binary_states_are_explicit_and_never_claim_complete_security_review():
    binary = ("diff --git a/assets/logo.png b/assets/logo.png\n"
              "index 1111111..2222222 100644\n"
              "Binary files a/assets/logo.png and b/assets/logo.png differ\n")
    analysis, output = report(metadata(additions=0, deletions=0, changedFiles=1), binary)
    assert analysis["input_state"] == "limited"
    assert analysis["binary_files"] == ["assets/logo.png"]
    assert analysis["reviewable"] is False
    assert "content is uninspectable" in output
    assert "No security analysis performed" in output

    mixed = binary + patch_for(("src/app.py",), added=("safe = True", "return safe"))
    analysis, output = report(metadata(additions=2, deletions=0, changedFiles=2), mixed)
    assert analysis["input_state"] == "limited"
    assert analysis["reviewable"] is True
    assert "Limited review" in output
    assert "**Confidence:** Low" in output
    assert "no security conclusion is made" in output
    assert "assets/logo.png" in output


def test_binary_evidence_gate_survives_derived_state_mutation():
    """A forged/older derived state must not erase binary uncertainty."""
    patch = patch_for(("src/app.py", "tests/test_app.py"),
                      added=tuple(f"assert result == expected {i}" for i in range(12)))
    analysis, _ = report(metadata(additions=24, deletions=0, changedFiles=2), patch)
    assert reviewer.confidence_level(analysis, []) == "High"

    # Simulate a caller or mutation that marks the aggregate valid while
    # retaining the authoritative uninspected-file evidence.
    analysis["input_state"] = "valid"
    analysis["binary_files"] = ["assets/logo.png"]
    assert reviewer.confidence_level(analysis, []) == "Low"
    output = reviewer.generate_report(metadata(additions=24, deletions=0, changedFiles=2), analysis)
    assert "**Confidence:** High" not in output
    assert "Limited review" in output
    assert "no security conclusion is made" in output


def test_duplicate_headers_and_traversal_paths_are_not_reviewable():
    duplicate = ("diff --git a/app.py b/app.py\n--- a/app.py\n--- a/app.py\n"
                 "+++ b/app.py\n@@ -1,1 +1,2 @@\n-old\n+new\n+more\n")
    traversal = ("diff --git a/../x.py b/../x.py\n--- a/../x.py\n+++ b/../x.py\n"
                 "@@ -0,0 +1,2 @@\n+assert one\n+assert two\n")
    for patch in (duplicate, traversal):
        analysis, output = report(metadata(), patch)
        assert analysis["malformed"] is True
        assert analysis["reviewable"] is False
        assert "unsafe input" in output


def test_generated_path_cases_reject_traversal_and_noncanonical_forms():
    invalid = ("../x.py", "src/../../x.py", "/tmp/x.py", "src/./x.py",
               "src//x.py", "src\\x.py", "src/\tx.py", "src/\x7fx.py", ".", "..")
    for path in invalid:
        assert reviewer._is_safe_patch_path(path) is False
        patch_text = (f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n"
                      "@@ -0,0 +1,2 @@\n+one\n+two\n")
        analysis, output = report(metadata(additions=2, deletions=0, changedFiles=1), patch_text)
        assert analysis["input_state"] == "rejected", path
        assert analysis["reviewable"] is False, path
        assert path not in analysis["files_changed"]
        assert "Rejected review" in output

    for path in ("x.py", "src/x.py", "path with spaces/file.py", "vendor/pkg/x.js"):
        assert reviewer._is_safe_patch_path(path) is True


def test_header_pairing_and_repeated_sections_fail_closed():
    prefix = "diff --git a/app.py b/app.py\n"
    hunk = "@@ -1,1 +1,2 @@\n-old\n+new\n+more\n"
    malformed = (
        prefix + "+++ b/app.py\n--- a/app.py\n" + hunk,
        prefix + "--- a/app.py\n+++ b/other.py\n" + hunk,
        prefix + "--- a/app.py\n+++ b/app.py\n+++ b/app.py\n" + hunk,
        prefix + "--- /dev/null\n+++ /dev/null\n" + hunk,
        prefix + "--- a/app.py\n+++ b/app.py\n" + hunk +
        prefix + "--- a/app.py\n+++ b/app.py\n" + hunk,
        prefix + "--- a/app.py\n+++ b/app.py\n@@ malformed @@\n+new\n",
    )
    for patch_text in malformed:
        analysis, output = report(metadata(), patch_text)
        assert analysis["input_state"] == "rejected"
        assert analysis["reviewable"] is False
        assert "Rejected review" in output


def test_valid_patch_classes_remain_reviewable():
    cases = [
        (patch_for(("src/a.py",), added=("one", "two")), {"has_docs": False}),
        (patch_for(("src/a.py", "src/b.py"), added=("one", "two")), {}),
        (patch_for(("src/a.py",), added=("new", "more"), deleted=("old",)), {}),
        (patch_for(("src/old.py",), added=(), deleted=("a", "b")), {}),
        (patch_for(("docs/guide.md",), added=("intro", "details")), {"has_docs": True}),
        (patch_for(("vendor/pkg/generated.min.js",), added=("min", "data")),
         {"generated_files": ["vendor/pkg/generated.min.js"]}),
    ]
    for patch_text, expected in cases:
        additions = sum(1 for line in patch_text.splitlines() if line.startswith("+") and not line.startswith("+++"))
        deletions = sum(1 for line in patch_text.splitlines() if line.startswith("-") and not line.startswith("---"))
        files = patch_text.count("diff --git ")
        analysis, _ = report(metadata(additions=additions, deletions=deletions,
                                      changedFiles=files), patch_text)
        assert analysis["reviewable"] is True
        assert analysis["malformed"] is False
        for key, value in expected.items():
            assert analysis[key] == value


def test_standard_git_quoted_unicode_path_is_decoded_and_validated():
    patch_text = ('diff --git "a/caf\\303\\251.py" "b/caf\\303\\251.py"\n'
                  '--- "a/caf\\303\\251.py"\n'
                  '+++ "b/caf\\303\\251.py"\n'
                  '@@ -0,0 +1,2 @@\n+one\n+two\n')
    analysis, _ = report(metadata(additions=2, deletions=0, changedFiles=1), patch_text)
    assert analysis["reviewable"] is True
    assert analysis["files_changed"] == ["café.py"]


def test_high_confidence_requires_meaningful_test_coverage_evidence():
    patch = patch_for(("src/app.py", "tests/test_app.py"),
                      added=("implemented change", "assert result == expected"))
    analysis, _ = report(metadata(additions=4, deletions=0, changedFiles=2), patch)
    assert analysis["has_tests"] is True
    assert analysis["has_test_evidence"] is True
    assert reviewer.confidence_level(analysis, []) == "Medium"  # too small for High

    large = patch_for(("src/app.py", "tests/test_app.py"),
                      added=tuple("assert result == expected" for _ in range(12)))
    analysis, _ = report(metadata(additions=24, deletions=0, changedFiles=2), large)
    assert reviewer.confidence_level(analysis, []) == "High"

    filename_only = patch_for(("src/app.py", "tests/test_app.py"),
                              added=tuple(f"line{i}" for i in range(12)))
    analysis, _ = report(metadata(additions=24, deletions=0, changedFiles=2), filename_only)
    assert analysis["has_tests"] is True
    assert analysis["has_test_evidence"] is False
    assert reviewer.confidence_level(analysis, []) != "High"


def test_report_has_one_documentation_section():
    analysis, output = report(metadata(), patch_for())
    assert output.count("### 📖 Documentation") == 1


def test_binary_generated_and_large_changes_are_explicitly_uncertain():
    patch = ("diff --git a/generated/app.min.js b/generated/app.min.js\n"
             "Binary files a/generated/app.min.js and b/generated/app.min.js differ\n")
    analysis, output = report(metadata(changedFiles=1), patch)
    assert analysis["reviewable"] is False
    large = patch_for(tuple(f"src/{i}.py" for i in range(12)), added=tuple(f"line{i}" for i in range(30)))
    analysis, output = report(metadata(additions=360, deletions=0, changedFiles=12), large)
    assert analysis["reviewable"] is True
    assert "Large change surface" in output


def test_api_non_string_diff_url_fails_cleanly_without_traceback():
    class Response:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self):
            return b"{}"

    def fake_urlopen(request, timeout=20):
        if request.full_url.endswith("/files?per_page=100"):
            return Response()
        return Response()

    with patch.object(reviewer.subprocess, "check_output",
                      side_effect=subprocess.CalledProcessError(1, "gh")), \
         patch.object(reviewer, "urlopen", side_effect=[
             type("JSONResponse", (), {
                 "__enter__": lambda self: self,
                 "__exit__": lambda self, *args: False,
                 "read": lambda self: b'{"title":"x","body":"","diff_url":null}'})(),
             type("JSONResponse", (), {
                 "__enter__": lambda self: self,
                 "__exit__": lambda self, *args: False,
                 "read": lambda self: b'[]'})(),
         ]):
        try:
            reviewer.fetch_pr("https://github.com/o/r/pull/1")
        except reviewer.InputError as exc:
            assert "invalid diff_url" in str(exc)
        else:
            raise AssertionError("invalid diff_url must fail")


def test_cli_reports_inaccessible_or_malformed_inputs_without_traceback(tmp_path):
    result = subprocess.run([sys.executable, str(SCRIPT), "--metadata", str(tmp_path / "missing"),
                             "--diff", str(tmp_path / "missing.patch")], capture_output=True, text=True)
    assert result.returncode == 2
    assert "PR review unavailable" in result.stderr
    assert "Traceback" not in result.stderr
    bad = tmp_path / "bad.json"
    bad.write_text("[]")
    result = subprocess.run([sys.executable, str(SCRIPT), "--metadata", str(bad),
                             "--diff", str(tmp_path / "missing.patch")], capture_output=True, text=True)
    assert result.returncode == 2
    assert "metadata must be a JSON object" in result.stderr

    malformed = tmp_path / "malformed.json"
    malformed.write_text("{not-json", encoding="utf-8")
    valid_diff = tmp_path / "valid.patch"
    valid_diff.write_text(patch_for(("src/a.py",)), encoding="utf-8")
    result = subprocess.run([sys.executable, str(SCRIPT), "--metadata", str(malformed),
                             "--diff", str(valid_diff)], capture_output=True, text=True)
    assert result.returncode == 2
    assert "PR review unavailable" in result.stderr
    assert "Traceback" not in result.stderr


def test_empty_and_partial_metadata_are_explicitly_limited():
    patch_text = patch_for(("src/a.py",), added=("one", "two"))
    for meta in ({}, {"title": "Partial"}, {"title": "Partial", "additions": 2}):
        analysis, output = report(meta, patch_text)
        assert analysis["reviewable"] is True
        assert "Review status:** Limited" in output
        assert "**Confidence:** Low" in output
        assert "Uncertainty" in output


def test_non_review_reports_use_the_required_confidence_enum():
    cases = [
        "",
        "diff --git a/image.png b/image.png\nBinary files a/image.png and b/image.png differ\n",
        "diff --git a/src/a.py b/src/a.py\n@@ malformed\n+one\n",
    ]
    for patch in cases:
        analysis = reviewer.finalize_analysis(reviewer.analyze_diff(patch), patch)
        output = reviewer.generate_report(metadata(), analysis)
        confidence = next(line for line in output.splitlines() if "**Confidence:**" in line)
        assert any(level in confidence for level in ("Low", "Medium", "High"))
        assert "Not applicable" not in confidence
        assert "### ⚠️ Risks" in output


def test_rejected_diff_cli_exits_nonzero_with_a_rejection_report(tmp_path):
    meta = tmp_path / "metadata.json"
    patch_path = tmp_path / "unsafe.patch"
    meta.write_text(json.dumps(metadata(additions=2, deletions=0, changedFiles=1)), encoding="utf-8")
    patch_path.write_text("diff --git a/../x.py b/../x.py\n--- a/../x.py\n+++ b/../x.py\n"
                          "@@ -0,0 +1,2 @@\n+one\n+two\n", encoding="utf-8")
    result = subprocess.run([sys.executable, str(SCRIPT), "--metadata", str(meta),
                             "--diff", str(patch_path)], capture_output=True, text=True)
    assert result.returncode == 2
    assert "Rejected review" in result.stdout
    assert "Traceback" not in result.stderr


def test_committed_real_output_fixtures_match_current_report_exactly():
    inputs = Path(__file__).parent / "real_inputs"
    outputs = Path(__file__).parent / "real_outputs"
    for fixture in sorted(outputs.glob("cli-*.md")):
        stem = fixture.stem
        metadata = reviewer.load_metadata(str(inputs / f"{stem}.json"))
        diff = reviewer.load_diff(str(inputs / f"{stem}.patch"))
        analysis = reviewer.finalize_analysis(reviewer.analyze_diff(diff), diff)
        expected = reviewer.generate_report(metadata, analysis)
        assert expected == fixture.read_text(encoding="utf-8"), stem


def test_evidence_binding_is_emitted_verbatim():
    analysis = reviewer.finalize_analysis(reviewer.analyze_diff(patch_for()), patch_for())
    output = reviewer.generate_report(metadata(), analysis, {
        "CANDIDATE_SHA": "abc123", "WORKTREE": "/candidate", "CLEAN": "true",
        "EVIDENCE_FOR_SHA": "abc123", "AUDIT_FOR_SHA": "abc123"})
    for key in ("CANDIDATE_SHA", "WORKTREE", "CLEAN", "EVIDENCE_FOR_SHA", "AUDIT_FOR_SHA"):
        assert key in output
