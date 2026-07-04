# Claude Review CLI

`claude-review` fetches a public GitHub pull request diff and returns a
structured Markdown review comment.

## Setup

```bash
chmod +x claude-review
```

## Usage

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

The output includes:

- summary of changes;
- identified risks;
- improvement suggestions;
- confidence score: `Low`, `Medium`, or `High`.

The CLI does not post comments or mutate GitHub state. It only reads the public
`.diff` endpoint for the provided PR URL.
