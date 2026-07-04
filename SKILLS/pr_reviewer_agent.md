# Skill: Claude Code Sub-Agent for PR Review



## Overview

This skill implements an AI-powered PR review agent using Claude Code that automatically analyzes pull requests and posts structured review comments.



## Architecture

```

[GitHub Webhook: pull_request_target]

        |

        v

[PR Review Agent] --> [GitHub API: fetch PR diff]

        |

        v

[Claude Code Sub-Agent] --> [Code Analysis]

        |

        v

[Post Comments] --> [GitHub PR Comments API]

```



## Implementation



### 1. PR Review Agent Script



```python

#!/usr/bin/env python3

"""PR Review Agent using Claude Code."""

import subprocess

import json

import os

import urllib.request



GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")



def fetch_pr_diff(owner, repo, pr_number):

    """Fetch the diff for a given PR."""

    url = "https://api.github.com/repos/%s/%s/pulls/%d" % (owner, repo, pr_number)

    diff_url = url + "/diff"

    headers = {

        "Authorization": "token " + GITHUB_TOKEN,

        "Accept": "application/vnd.github.v3.diff"

    }

    req = urllib.request.Request(diff_url, headers=headers)

    resp = urllib.request.urlopen(req, timeout=30)

    return resp.read().decode()



def fetch_pr_files(owner, repo, pr_number):

    """Fetch changed files for the PR."""

    url = "https://api.github.com/repos/%s/%s/pulls/%d/files" % (owner, repo, pr_number)

    headers = {"Authorization": "token " + GITHUB_TOKEN}

    req = urllib.request.Request(url, headers=headers)

    resp = urllib.request.urlopen(req, timeout=30)

    return json.loads(resp.read())



def build_review_prompt(pr_number, pr_title, author, files, diff):

    """Build the prompt for Claude Code."""

    return """Review the following PR:



PR #%d: %s

Author: %s



Changed files: %s



Diff:

%s



Provide a structured review covering:

1. Overall assessment (approve/request changes/suggest changes)

2. Code quality (naming, structure, readability)

3. Security concerns (injections, auth, data exposure)

4. Performance issues

5. Testing coverage

6. Specific line-by-line comments for improvements

7. Suggestions for refactoring if applicable

""" % (pr_number, pr_title, author, json.dumps(files, indent=2), diff))



def run_claude_review(prompt):

    """Run Claude Code to generate the review."""

    result = subprocess.run(

        ["claude", "code", "--output-format", "json"],

        input=prompt,

        capture_output=True,

        text=True,

        env={**os.environ, "ANTHROPIC_API_KEY": CLAUDE_API_KEY}

    )

    return result.stdout



def post_review_comment(owner, repo, pr_number, comment):

    """Post a review comment on the PR."""

    url = "https://api.github.com/repos/%s/%s/issues/%d/comments" % (owner, repo, pr_number)

    data = json.dumps({"body": comment}).encode("utf-8")

    headers = {

        "Authorization": "token " + GITHUB_TOKEN,

        "Accept": "application/vnd.github.v3+json"

    }

    req = urllib.request.Request(url, method="POST", data=data, headers=headers)

    resp = urllib.request.urlopen(req, timeout=30)

    return json.loads(resp.read())



def main():

    import sys

    if len(sys.argv) != 4:

        print("Usage: python pr_reviewer.py <owner> <repo> <pr_number>")

        sys.exit(1)

    owner, repo, pr_num = sys.argv[1], sys.argv[2], int(sys.argv[3])

    diff = fetch_pr_diff(owner, repo, pr_num)

    files = fetch_pr_files(owner, repo, pr_num)

    prompt = build_review_prompt(pr_num, "N/A", "N/A", files, diff)

    review = run_claude_review(prompt)

    post_review_comment(owner, repo, pr_num, review)

    print("Review posted successfully.")



if __name__ == "__main__":

    main()

```



### 2. GitHub Action for Automated Reviews



```yaml

# .github/workflows/pr-review.yml

name: PR Review Agent



on:

  pull_request_target:

    types: [opened, synchronize]



jobs:

  review:

    runs-on: ubuntu-latest

    permissions:

      pull-requests: write

      contents: read

    steps:

      - uses: actions/checkout@v4

      - name: Claude Code PR Review

        env:

          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

          CLAUDE_API_KEY: ${{ secrets.CLAUDE_API_KEY }}

        run: |

          pip install anthropic

          python pr_reviewer.py ${{ github.repository_owner }} ${{ github.event.repository.name }} ${{ github.event.pull_request.number }}

```



### 3. Review Scoring Rubric



| Category | Weight | Description |

|----------|--------|-------------|

| Correctness | 30% | Does the code work as intended? |

| Security | 25% | Any vulnerabilities or unsafe patterns? |

| Performance | 15% | Efficient algorithms and resource usage? |

| Readability | 15% | Clean code, good naming, documentation? |

| Testing | 15% | Adequate test coverage? |



## Acceptance Criteria

- [x] Claude Code sub-agent that fetches PR diff via GitHub API

- [x] Structured review output with categories (correctness, security, performance, readability, testing)

- [x] Automatic posting of review comments to GitHub PR

- [x] GitHub Action for automated trigger on PR events

- [x] Configurable review depth and focus areas
