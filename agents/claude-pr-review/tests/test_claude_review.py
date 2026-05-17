import textwrap
import unittest

from agents.claude_pr_review import claude_review


SAMPLE_DIFF = textwrap.dedent(
    """\
    diff --git a/app.py b/app.py
    index 1111111..2222222 100644
    --- a/app.py
    +++ b/app.py
    @@ -1,2 +1,6 @@
    +API_SECRET = "1234567890abcdef"
    +def run(user_input):
    +    eval(user_input)
    +    except Exception:
    +        pass
     print("hello")
    diff --git a/tests/test_app.py b/tests/test_app.py
    index 3333333..4444444 100644
    --- a/tests/test_app.py
    +++ b/tests/test_app.py
    @@ -0,0 +1,2 @@
    +def test_run():
    +    assert True
    """
)


class ClaudeReviewTests(unittest.TestCase):
    def test_parse_pr_url(self):
        ref = claude_review.parse_pr_reference("https://github.com/openai/openai-python/pull/123", None)
        self.assertEqual(ref.owner, "openai")
        self.assertEqual(ref.repo, "openai-python")
        self.assertEqual(ref.number, 123)

    def test_parse_numeric_pr_with_repo(self):
        ref = claude_review.parse_pr_reference("42", "owner/repo")
        self.assertEqual(ref.repo_full_name, "owner/repo")
        self.assertEqual(ref.number, 42)

    def test_analyze_diff_finds_required_sections_and_risks(self):
        review = claude_review.analyze_diff(
            SAMPLE_DIFF,
            pr_title="Sample",
            pr_url="https://github.com/example/repo/pull/1",
        )
        markdown = review.to_markdown()
        self.assertIn("### Summary of Changes", markdown)
        self.assertIn("### Identified Risks", markdown)
        self.assertIn("### Improvement Suggestions", markdown)
        self.assertIn("### Confidence Score:", markdown)
        self.assertTrue(any(risk.title == "Possible hardcoded secret" for risk in review.risks))
        self.assertTrue(any(risk.title == "Dynamic code execution" for risk in review.risks))

    def test_missing_tests_lowers_confidence(self):
        diff = textwrap.dedent(
            """\
            diff --git a/src/service.py b/src/service.py
            index 1111111..2222222 100644
            --- a/src/service.py
            +++ b/src/service.py
            @@ -1,0 +1,45 @@
            """
        ) + "\n".join(f"+print({index})" for index in range(45))
        review = claude_review.analyze_diff(diff, pr_title="No tests", pr_url="local")
        self.assertEqual(review.confidence, "Medium")
        self.assertTrue(any(risk.title == "No tests changed with code" for risk in review.risks))


if __name__ == "__main__":
    unittest.main()
