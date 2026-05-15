# claude-review — PR Reviewer Agent

## Setup (3 commands)

```bash
cp claude-review.py /usr/local/bin/claude-review
chmod +x /usr/local/bin/claude-review
echo ''export GITHUB_TOKEN=ghp_xxxx'' >> ~/.bashrc
```

## Usage

```bash
# Review a PR (saves to review-{owner}-{repo}-{number}.md)
claude-review --pr https://github.com/owner/repo/pull/123

# Print to stdout
claude-review --pr https://github.com/owner/repo/pull/123 --stdout
```

## Requirements

- Python 3.8+
- GitHub token in `GITHUB_TOKEN` env var (or `export GITHUB_TOKEN=...`)
- Network access to api.github.com

## Sample Output

See `sample-reviews/` for example outputs on real PRs.