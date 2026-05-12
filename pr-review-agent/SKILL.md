# Claude Review Agent Skill

Use this skill when a maintainer wants a concise, structured review draft for a GitHub pull request.

## Command

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

## Behavior

- Fetch the PR metadata and diff with `gh`.
- Summarize the review surface in 2-3 sentences.
- Identify concrete risks from file paths, added lines, diff size, and test presence.
- Suggest follow-up checks or improvements.
- Report confidence as Low, Medium, or High.

## Boundaries

- Do not approve or reject automatically.
- Do not use paid APIs.
- Do not request or store tokens.
- Treat the generated Markdown as a review draft for a human maintainer.
