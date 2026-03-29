# Sample Outputs

Below are examples of `claude-review.py` generating structured code reviews from real GitHub Pull Requests.

## Sample 1: Analyzing PR #204 (Changelog Generator)
**Command:** `./claude-review.py --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/204`

**Output:**
```markdown
## Summary of changes
This PR introduces a Bash script (`changelog.sh`) and an associated Claude `SKILL.md` to automatically generate a structured `CHANGELOG.md` from the project's Git commit history. It parses commits since the last tag and categorizes them into Added, Fixed, Removed, and Changed based on semantic keywords.

## Identified risks
- If a project has a massive history with no tags, `git log` could pull thousands of commits and cause performance or memory issues when storing the results in Bash variables.
- The categorization logic uses a case-insensitive regex check on the commit message, which might miscategorize commits if standard conventional commit formats aren't strictly followed (e.g. a commit starting with "newly added..." goes to `Added`).
- Empty lines or malformed commit messages containing special characters could potentially disrupt the string parsing.

## Improvement suggestions
- Consider using `--max-count` or limiting the `git log` output to avoid hanging on very large repositories without tags.
- Instead of keeping raw newlines in string variables (`ADDED="${ADDED}- ${msg}\n"`), it might be safer to accumulate them into arrays and then join them, ensuring no unintended string escapes are processed.
- The regex `^(feat|add|new|create|implement)` is somewhat broad; enforcing a stricter conventional commits pattern might yield more reliable categorizations.

## Confidence score
High
```

## Sample 2: Analyzing PR #207 (Next.js Template)
**Command:** `./claude-review.py --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/207`

**Output:**
```markdown
## Summary of changes
This PR adds an opinionated `CLAUDE.md` template file targeted at Next.js 15 (App Router) projects utilizing SQLite and Drizzle ORM. The template explicitly defines strict architectural rules, data fetching paradigms, SQL table structures, and notes several forbidden anti-patterns (such as using Prisma or barrel files).

## Identified risks
- No major risks identified. Since these are documentation files, they present zero operational risk to a runtime environment.
- The strict architectural constraints (e.g., banning all barrel files or enforcing integer timestamps) might conflict with teams using certain specialized tooling or other established Next.js structures, but this is clearly labeled as an "opinionated" template.

## Improvement suggestions
- Add a brief instruction on where exactly `CLAUDE.md` should be placed (e.g., project root) inside the `CLAUDE.md` file itself, not just in the `README.md`.
- Consider adding a section regarding Environment Variable validation (e.g. using `zod` and `t3-env`), as the document mentions `env.mjs` but doesn't elaborate.

## Confidence score
High
```