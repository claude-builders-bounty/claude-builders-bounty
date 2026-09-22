## Summary
Adds `agents/claude-review`: a stdlib Python CLI + GitHub Action that reviews a PR and emits structured Markdown (summary, risks, suggestions, confidence).

Closes / targets Opire bounty **#4** ($150).

## Test plan
- [x] `python3 claude_review.py --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4402 --no-llm`
- [x] `python3 claude_review.py --pr https://github.com/expressjs/express/pull/7482 --no-llm`
- [x] Sample outputs committed under `examples/`
