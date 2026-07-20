# CLAUDE.md

This file guides Claude Code (claude.ai/code) through the repository structure, conventions, and rules.

## Project Overview

This is a Claude Code skill/bounty repository for the claude-builders-bounty project.

## Repository Structure

```
├── README.md          # Main documentation
├── LICENSE            # MIT License
├── package.json       # Node.js dependencies
├── src/               # Source code
├── test-output/       # Test output samples
├── .gitignore         # Git ignore rules
└── .github/           # GitHub workflows
```

## Conventions

- Use TypeScript for all new code
- Follow existing file naming: kebab-case for files, PascalCase for components
- Write tests alongside features
- Keep PRs focused on one change
- Document public APIs with JSDoc comments

## Commands

```bash
npm install    # Install dependencies
npm test       # Run tests
npm run build  # Build project
```

## Rules

- Do not push to remote repositories without explicit permission
- Always check git status before committing
- Use conventional commits format
- Review PR descriptions for completeness
