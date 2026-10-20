# Claude Code PR Review Sub-Agent (`claude-review` — Bounty #4)

CLI & GitHub Action sub-agent that fetches any GitHub PR diff and outputs a structured Markdown review (Summary, Identified Risks, Improvement Suggestions, Confidence Score).

## Usage
```bash
python3 agents/claude-review/claude_review.py --pr https://github.com/trovu/trovu/pull/722
```

## Sample Tested Outputs (2 Real GitHub PRs)

### Sample 1: `https://github.com/trovu/trovu/pull/722`
- **Summary of Changes**: Modifies 1 file (`+24` / `-2` lines) in `src/js/helpers/pwa.js` to open resolved shortcut URLs in the system default browser when running as an installed standalone PWA.
- **Identified Risks**: Low surface risk; browser `window.open(..., "_blank", "noopener,noreferrer")` fallback preserves current tab safety.
- **Improvement Suggestions**: Add Playwright standalone display-mode test case.
- **Confidence Score**: **High**

### Sample 2: `https://github.com/seveibar/pgstrap/pull/101`
- **Summary of Changes**: Modifies 2 files (`+16` / `-1` lines) across `src/get-pg-client.ts` and `src/MigratePlugin.ts` to add native `pglite://` and `memory://` in-process Postgres support.
- **Identified Risks**: Optional peer dependency `@electric-sql/pglite` is dynamically imported; ensure clear error message when not installed.
- **Improvement Suggestions**: Add unit test exercising `pglite://memory` migration lifecycle.
- **Confidence Score**: **High**
