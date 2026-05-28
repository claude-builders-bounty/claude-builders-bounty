"""Analyze PR diff and generate structured review via DeepSeek API."""

import httpx


REVIEW_PROMPT = """You are a senior code reviewer. Analyze the following GitHub pull request and produce a structured review.

PR Title: {title}
PR Author: {author}
Files Changed: {files_changed}
+{additions} -{deletions}

PR Description:
{body}

## Diff:
```diff
{diff}
```

Output a structured review in this exact Markdown format:

### Summary
[2-3 sentences summarizing what this PR changes and why]

### Identified Risks
- [Risk 1: specific, with file reference if applicable]
- [Risk 2: ...]
(If no risks, write "None identified.")

### Improvement Suggestions
- [Suggestion 1: actionable, concrete]
- [Suggestion 2: ...]
(If no suggestions, write "None. The changes look solid.")

### Confidence Score
**[High / Medium / Low]** — [one sentence explaining the score]

Rules:
- Be specific. Reference actual file paths and line counts from the diff.
- Don't flag stylistic preferences — only real bugs, security issues, or maintainability problems.
- If the PR is small (< 50 lines changed), flag missing tests as a risk.
- Keep total output under 400 words."""

MAX_DIFF = 12000


class Reviewer:
    """Generates structured PR review using DeepSeek API."""

    def __init__(self, api_key: str, config: dict = None):
        self.api_key = api_key
        cfg = config or {}
        self.base_url = cfg.get("base_url", "https://api.deepseek.com/v1")
        self.model = cfg.get("model", "deepseek-chat")
        self.max_tokens = cfg.get("max_tokens", 800)

    def review(self, pr_data: dict) -> str:
        """Generate a structured review from PR data."""
        prompt = REVIEW_PROMPT.format(
            title=pr_data["title"],
            author=pr_data.get("author", "unknown"),
            files_changed=pr_data.get("files_changed", 0),
            additions=pr_data.get("additions", 0),
            deletions=pr_data.get("deletions", 0),
            body=pr_data.get("body", "")[:500],
            diff=pr_data.get("diff", "")[:MAX_DIFF],
        )

        try:
            resp = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": self.max_tokens,
                    "temperature": 0.3,
                },
                timeout=90,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        except (httpx.HTTPError, KeyError, IndexError) as e:
            return f"## Review Failed\n\nError calling DeepSeek API: {e}"
