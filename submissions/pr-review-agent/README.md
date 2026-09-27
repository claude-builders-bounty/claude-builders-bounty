# 🤖 Claude PR Reviewer

[![npm version](https://badge.fury.io/js/claude-pr-reviewer.svg)](https://badge.fury.io/js/claude-pr-reviewer)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![TypeScript](https://img.shields.io/badge/TypeScript-Ready-blue.svg)](https://www.typescriptlang.org/)
[![Node.js](https://img.shields.io/badge/Node.js-%3E%3D18-green.svg)](https://nodejs.org/)

A powerful, production-quality CLI tool and GitHub Action that uses Anthropic's Claude Sonnet 4 to automatically review GitHub Pull Requests.

## ✨ Features

- **🧠 Intelligent Analysis**: Leverages Claude Sonnet 4 for deep, context-aware code reviews.
- **🛡️ Risk Identification**: Automatically flags security vulnerabilities, performance bottlenecks, and architectural risks.
- **💡 Actionable Suggestions**: Provides specific, prioritized suggestions for code improvement.
- **🎛️ Configurable Depth**: Choose between `quick`, `standard`, and `deep` review modes.
- **📊 Multiple Formats**: Output to beautifully styled console, Markdown, or JSON.
- **🤖 GitHub Action Ready**: Easily integrate into your CI/CD pipeline to comment directly on PRs.

## 🚀 Quick Start

\`\`\`bash
npx claude-pr-reviewer --pr https://github.com/owner/repo/pull/123
\`\`\`

## 📦 Installation

\`\`\`bash
# Install globally
npm install -g claude-pr-reviewer

# Or install locally in your project
npm install --save-dev claude-pr-reviewer
\`\`\`

## ⚙️ Configuration

You need to provide API keys for both GitHub and Anthropic. Set them as environment variables:

\`\`\`bash
export GITHUB_TOKEN="your_github_personal_access_token"
export ANTHROPIC_API_KEY="your_anthropic_api_key"
\`\`\`

Alternatively, you can create a `.env` file in your project root:

\`\`\`env
GITHUB_TOKEN=ghp_...
ANTHROPIC_API_KEY=sk-ant-...
\`\`\`

## 📖 Usage

### Basic CLI Usage

Review a PR and print the styled output to the console:
\`\`\`bash
claude-review --pr https://github.com/owner/repo/pull/123
\`\`\`

### Review Depth Levels

You can control how deeply Claude analyzes the code:
- \`quick\`: Fast review focusing on summary and major risks.
- \`standard\` (default): Full review with risks, suggestions, and security notes.
- \`deep\`: Thorough analysis including line-by-line review and code snippets.

\`\`\`bash
claude-review --pr https://github.com/owner/repo/pull/123 --depth deep
\`\`\`

### Output Formats

Choose how the output is formatted:
\`\`\`bash
# Console (default) - styled with colors
claude-review --pr https://github.com/owner/repo/pull/123 --format console

# Markdown - great for documentation
claude-review --pr https://github.com/owner/repo/pull/123 --format markdown

# JSON - ideal for programmatic consumption
claude-review --pr https://github.com/owner/repo/pull/123 --format json
\`\`\`

### Post Comment to GitHub PR

Automatically post the generated Markdown review directly to the PR:
\`\`\`bash
claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
\`\`\`

### Save Output to File

\`\`\`bash
claude-review --pr https://github.com/owner/repo/pull/123 --format markdown --output review.md
\`\`\`

## 🔄 GitHub Action Setup

You can easily integrate this tool into your GitHub workflow to automatically review PRs as they are opened.

Create a file at \`.github/workflows/pr-review.yml\`:

\`\`\`yaml
name: Claude PR Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm run build
      - name: Run Claude PR Review
        env:
          GITHUB_TOKEN: \${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: \${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          npx claude-review --pr \${{ github.event.pull_request.html_url }} --post-comment --format markdown
\`\`\`

## 🏗️ Architecture

The codebase is structured logically to ensure maintainability:
- \`src/cli.ts\`: Entry point, parses command-line arguments using Commander.
- \`src/github.ts\`: Manages GitHub API communication (fetching PR metadata, diffs, posting comments).
- \`src/analyzer.ts\`: Interfaces with the Anthropic API to generate structured PR reviews.
- \`src/formatter.ts\`: Transforms raw analysis data into nicely formatted console text, Markdown, or JSON.
- \`src/types.ts\`: Shared TypeScript interfaces.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
1. Fork the project
2. Create your feature branch (\`git checkout -b feature/AmazingFeature\`)
3. Commit your changes (\`git commit -m 'Add some AmazingFeature'\`)
4. Push to the branch (\`git push origin feature/AmazingFeature\`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
