#!/usr/bin/env node
"use strict";
/**
 * CLI entry point for pr-review-agent
 */
Object.defineProperty(exports, "__esModule", { value: true });
const review_1 = require("./review");
function parseArgs(args) {
    const result = {};
    for (let i = 0; i < args.length; i++) {
        const arg = args[i];
        if (arg === '--help' || arg === '-h') {
            result.help = true;
        }
        else if (arg === '--pr' || arg === '-p') {
            result.pr = args[++i];
        }
        else if (arg === '--token' || arg === '-t') {
            result.token = args[++i];
        }
        else if (arg === '--model' || arg === '-m') {
            result.model = args[++i];
        }
        else if (arg === '--max-tokens' || arg === '-c') {
            result['max-tokens'] = args[++i];
        }
    }
    return result;
}
function showHelp() {
    console.log(`
claude-review — AI-powered PR review agent

USAGE
  claude-review --pr <url> [options]

OPTIONS
  --pr, -p <url>       GitHub PR URL (required)
  --token, -t <token>  GitHub token (or GITHUB_TOKEN env)
  --model, -m <model>  Claude model (default: claude-sonnet-4-20250514)
  --max-tokens, -c <n> Max response tokens (default: 4096)
  --help, -h           Show this help

EXAMPLES
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review -p https://github.com/owner/repo/pull/123 -t ghp_xxx

OUTPUT FORMAT
  Markdown report with sections:
  - Summary
  - Risks
  - Suggestions
  - Confidence
`);
}
const args = parseArgs(process.argv.slice(2));
if (args.help) {
    showHelp();
    process.exit(0);
}
const prUrl = args.pr;
if (!prUrl) {
    console.error('Error: --pr <url> is required\n');
    console.error('Run: claude-review --help');
    process.exit(1);
}
const config = {
    githubToken: args.token || process.env.GITHUB_TOKEN || '',
    model: args.model || 'claude-sonnet-4-20250514',
    maxTokens: parseInt(String(args['max-tokens'] || '4096'), 10),
};
async function main() {
    if (!prUrl) {
        console.error('Error: --pr <url> is required\n');
        console.error('Run: claude-review --help');
        process.exit(1);
    }
    try {
        const report = await (0, review_1.reviewPR)(prUrl, config);
        console.log(report);
    }
    catch (err) {
        console.error('Review failed:', err instanceof Error ? err.message : err);
        process.exit(1);
    }
}
main();
