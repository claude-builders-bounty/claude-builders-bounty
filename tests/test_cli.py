import os
import tempfile
from claude_review.cli import main, build_parser


def test_cli_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["--pr", "https://github.com/fastapi/fastapi/pull/100"])
    assert args.pr_url == "https://github.com/fastapi/fastapi/pull/100"
    assert args.diff_file is None
    assert args.output_file is None
    assert not args.post_comment


def test_cli_execution_with_local_diff():
    diff_content = """diff --git a/hello.py b/hello.py
new file mode 100644
index 0000000..1111111
--- /dev/null
+++ b/hello.py
@@ -0,0 +1,3 @@
+def greet():
+    print("Hello world")
+"""
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".diff") as diff_f:
        diff_f.write(diff_content)
        diff_path = diff_f.name

    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md") as out_f:
        out_path = out_f.name

    try:
        ret = main(["--diff-file", diff_path, "--output", out_path])
        assert ret == 0

        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "## 🤖 Claude Code PR Review" in content
        assert "### 📝 Summary of Changes" in content
        assert "### ⚠️ Identified Risks" in content
        assert "### 💡 Improvement Suggestions" in content
        assert "### 📊 Confidence Score" in content
    finally:
        if os.path.exists(diff_path):
            os.remove(diff_path)
        if os.path.exists(out_path):
            os.remove(out_path)
