# Claude Code Subagent Compatibility

This package includes a file-based Claude Code subagent:

```text
.claude/agents/pr-reviewer.md
```

## Why this is a subagent, not only a heuristic analyzer

The CLI provides a deterministic local harness for fetching public PR metadata and producing the required review shape. The subagent file provides the Claude Code agent definition and review behavior:

- YAML frontmatter:
  - `name`
  - `description`
  - `tools`
  - `model`
- Dedicated system prompt for PR review.
- Required Markdown output contract.
- Review rules for risk, tests, confidence, and external posting.

## Project-level installation

Keep the file at:

```text
.claude/agents/pr-reviewer.md
```

When the project is opened in Claude Code, the agent can be selected or invoked for PR review workflows.

## User-level installation

Copy the file to:

```text
~/.claude/agents/pr-reviewer.md
```

## Local CLI Harness

Use the CLI to produce repeatable sample outputs:

```powershell
node bin\claude-review.mjs --pr https://github.com/owner/repo/pull/123 --out review.md
```

Or after linking:

```powershell
npm link
claude-review --pr https://github.com/owner/repo/pull/123 --out review.md
```

## Validation

The test suite verifies:

- review Markdown sections;
- changed-file listing;
- subagent frontmatter;
- required subagent prompt sections.

