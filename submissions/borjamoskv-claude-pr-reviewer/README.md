# Claude PR Reviewer (CORTEX Sub-Agent) 🤖🔍

*High-exergy autonomous PR reviewer integrating Anthropic's Claude 3.5 Sonnet directly into your `gh` CLI workflow.*

Built for the **Claude Builders Bounty (#4)**.

## Features
- **Zero Git Auth Overhead:** Leverages your native macOS/Linux `gh` CLI authentication. If `gh` works, this agent works.
- **Cognitive Evaluation:** Bypasses simple linting to detect race conditions, state management anti-patterns, and logic faults.
- **Immediate Injection:** Automatically comments its structured markdown review directly onto the GitHub Pull Request timeline.
- **MICA Noir Aesthetic:** CLI logging structured for absolute clarity.

## Installation 

1. Clone or download this directory.
2. Install dependencies:
```bash
npm install
```
3. Link the package globally so you can use it anywhere:
```bash
npm link
```
4. Set up your environment variables. Ensure you have your Anthropic API Key exported in your shell, or place it in a `.env` file in the same directory:
```bash
export ANTHROPIC_API_KEY="sk-ant-xxx..."
```

## Usage

Simply run the agent by passing any open GitHub Pull Request URL:
```bash
claude-pr-reviewer https://github.com/owner/repo/pull/123
```

Watch as the agent fetches the diff, cognitively analyzes it via Claude 3.5 Sonnet, and injects the review directly into the PR.

## Architecture & Sovereignty Check
- **Language:** Node.js
- **Brain:** `@anthropic-ai/sdk` (Claude 3.5 Sonnet)
- **Hands:** GitHub CLI (`gh pr diff` & `gh pr review`)
- **Cost:** ~0.007c per average PR (depending on token size).
