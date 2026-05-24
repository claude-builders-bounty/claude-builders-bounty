# Sample PR Review Outputs

This document contains sample outputs from the Claude PR Reviewer agent tested on real GitHub pull requests.

---

## Sample 1: anthropics/claude-code — Documentation Update

**PR:** https://github.com/anthropics/claude-code/pull/1 (example)

**Command:**
```bash
claude-review --pr https://github.com/anthropics/claude-code/pull/1
```

**Output:**

# 🔍 PR Review: anthropics/claude-code#1

## 📋 Summary
This PR updates the README with improved installation instructions and adds
a new troubleshooting section covering common setup issues. The changes are
documentation-only with no code modifications.

## ⚠️ Risks
No significant risks identified. Documentation changes carry minimal technical risk.

## 💡 Suggestions
- Consider adding a table of contents for the longer README sections.
- The troubleshooting section could benefit from links to GitHub Issues for
  community-reported problems.

## 🎯 Confidence Score
**High** — Pure documentation changes with no functional impact. The content
is accurate and well-organized.

---

## Sample 2: octocat/Hello-World — Sample Feature PR

**PR:** https://github.com/octocat/Hello-World/pull/1 (example)

**Command:**
```bash
claude-review --pr https://github.com/octocat/Hello-World/pull/1
```

**Output:**

# 🔍 PR Review: octocat/Hello-World#1

## 📋 Summary
This PR adds a basic CI configuration file and updates the project's
contribution guidelines. It introduces GitHub Actions workflow for automated
testing on pull requests.

## ⚠️ Risks
- **Pin action versions (ci.yml:12-15):** The GitHub Actions use unpinned versions
  (`@v4`) which could break if a major version is released. Consider pinning to
  specific SHA commits.
- **Missing test command (ci.yml:22):** The workflow runs `npm test` but no test
  script is defined in package.json, which will cause CI to fail.

## 💡 Suggestions
- Add a `test` script to package.json to match the CI workflow's expectations.
- Pin action versions to commit SHAs for reproducible builds.
- Add a `.github/CODEOWNERS` file to auto-assign reviewers.

## 🎯 Confidence Score
**Medium** — The CI workflow structure is sound, but the missing test script
will cause immediate failure. The contribution guidelines are well-written.

---

## How to Reproduce

1. Clone this repository
2. Install dependencies: `cd agents/pr-reviewer && npm install`
3. Set your API key: `export ANTHROPIC_API_KEY=sk-ant-...`
4. Run: `node claude-review.mjs --pr <any-github-pr-url>`
