# claude-review

A CLI tool that reviews GitHub PRs and outputs structured Markdown feedback.

## Setup

```bash
chmod +x claude-review.sh
```

Requires: [GitHub CLI](https://cli.github.com) (`gh`) authenticated.

## Usage

```bash
# Review a PR (output to stdout)
bash claude-review.sh --pr https://github.com/owner/repo/pull/123

# Save review to file
bash claude-review.sh --pr https://github.com/owner/repo/pull/123 --output review.md
```

## Output Structure

- **Summary** — 2-3 sentence overview of changes
- **Changed Files** — List of modified files
- **Identified Risks** — Security concerns, credential exposure, incomplete code
- **Improvement Suggestions** — Code quality recommendations
- **Confidence Score** — High / Medium / Low based on diff size and complexity
- **Checklist** — Tests, docs, security, error handling

## Risk Detection

Automatically flags:
- Hardcoded passwords/secrets/API keys
- TODO/FIXME/HACK markers
- `eval()`/`exec()`/`dangerouslySetInnerHTML` usage
- Empty catch blocks
- TypeScript `any` types
- Sensitive file references (.env, .pem, .key)
- Large PRs (300+ lines)

## Sample Outputs

See `sample-output-1.md` and `sample-output-2.md` for real PR reviews.
