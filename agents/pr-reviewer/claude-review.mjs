#!/usr/bin/env node

/**
 * Claude Code PR Reviewer Agent
 *
 * Takes a GitHub PR URL or diff input, analyzes it using the Anthropic API,
 * and outputs a structured Markdown review comment.
 *
 * Usage:
 *   claude-review --pr https://github.com/owner/repo/pull/123
 *   claude-review --diff < diff.txt
 *   cat changes.patch | claude-review
 *
 * Environment:
 *   ANTHROPIC_API_KEY — Required. Your Anthropic API key.
 */

import { Anthropic } from '@anthropic-ai/sdk';
import { execSync } from 'child_process';
import { readFileSync } from 'fs';
import { argv, stdin, exit } from 'process';

// ─── Argument Parsing ────────────────────────────────────────────────────────

function parseArgs(args) {
  const parsed = { pr: null, diff: null, model: 'claude-sonnet-4-20250514' };
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--pr' && args[i + 1]) {
      parsed.pr = args[i + 1];
      i++;
    } else if (args[i] === '--diff' && args[i + 1]) {
      parsed.diff = args[i + 1];
      i++;
    } else if (args[i] === '--model' && args[i + 1]) {
      parsed.model = args[i + 1];
      i++;
    } else if (args[i] === '--help' || args[i] === '-h') {
      console.log(`
Claude Code PR Reviewer Agent

Usage:
  claude-review --pr <PR_URL>              Review a GitHub PR
  claude-review --diff <diff_file>         Review a diff file
  cat patch.diff | claude-review           Review from stdin

Options:
  --pr <url>       GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)
  --diff <file>    Path to a diff/patch file
  --model <model>  Claude model to use (default: claude-sonnet-4-20250514)
  -h, --help       Show this help message

Environment:
  ANTHROPIC_API_KEY  Required. Your Anthropic API key.

Output:
  Structured Markdown review with:
  - Summary of changes
  - Identified risks
  - Improvement suggestions
  - Confidence score (Low / Medium / High)
`);
      exit(0);
    }
  }
  return parsed;
}

// ─── PR Diff Fetching ────────────────────────────────────────────────────────

function fetchPRDiff(prUrl) {
  // Parse PR URL: https://github.com/owner/repo/pull/123
  const match = prUrl.match(/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/);
  if (!match) {
    throw new Error(`Invalid PR URL: ${prUrl}\nExpected format: https://github.com/owner/repo/pull/123`);
  }

  const [, owner, repo, number] = match;

  // Fetch PR metadata
  const prInfo = JSON.parse(
    execSync(`gh pr view ${number} --repo ${owner}/${repo} --json title,body,additions,deletions,changedFiles,author,baseRefName,headRefName`, {
      encoding: 'utf-8',
      env: { ...process.env, GH_TOKEN: process.env.GITHUB_TOKEN || process.env.GH_TOKEN || '' }
    })
  );

  // Fetch the diff
  const diff = execSync(
    `gh pr diff ${number} --repo ${owner}/${repo}`,
    {
      encoding: 'utf-8',
      maxBuffer: 10 * 1024 * 1024,
      env: { ...process.env, GH_TOKEN: process.env.GITHUB_TOKEN || process.env.GH_TOKEN || '' }
    }
  );

  return { prInfo, diff, prUrl, owner, repo, number };
}

// ─── Claude Review ───────────────────────────────────────────────────────────

async function generateReview(client, diff, prInfo, model) {
  const systemPrompt = `You are an expert code reviewer. Analyze the provided PR diff and produce a structured review in exactly this format:

## 📋 Summary
(2-3 sentences describing what this PR does and its purpose)

## ⚠️ Risks
(List potential risks, bugs, security concerns, or breaking changes. If none, say "No significant risks identified.")

## 💡 Suggestions
(List concrete improvement suggestions. If the code looks good, say "Code quality looks solid — no major suggestions.")

## 🎯 Confidence Score
**[Low / Medium / High]** — (Brief justification for the confidence level)

Guidelines:
- Be specific and reference actual code from the diff
- Focus on meaningful issues, not style nitpicks
- Consider security, performance, error handling, and maintainability
- If the PR is small/simple, say so and give a High confidence score
- If the PR is complex with potential edge cases, lower the confidence`;

  const userMessage = prInfo
    ? `Review this PR:

**Title:** ${prInfo.title}
**Author:** ${prInfo.author?.login || 'Unknown'}
**Branch:** ${prInfo.headRefName} → ${prInfo.baseRefName}
**Changes:** +${prInfo.additions} / -${prInfo.deletions} across ${prInfo.changedFiles} file(s)

${prInfo.body ? `**Description:**\n${prInfo.body}\n\n` : ''}**Diff:**
\`\`\`diff
${diff.slice(0, 80000)}
\`\`\``
    : `Review this diff:\n\n\`\`\`diff\n${diff.slice(0, 80000)}\n\`\`\``;

  const response = await client.messages.create({
    model,
    max_tokens: 4096,
    system: systemPrompt,
    messages: [{ role: 'user', content: userMessage }]
  });

  return response.content
    .filter(block => block.type === 'text')
    .map(block => block.text)
    .join('\n');
}

// ─── Main ────────────────────────────────────────────────────────────────────

async function main() {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    console.error('Error: ANTHROPIC_API_KEY environment variable is required.');
    console.error('Set it with: export ANTHROPIC_API_KEY=sk-ant-...');
    exit(1);
  }

  const args = parseArgs(argv.slice(2));
  const client = new Anthropic({ apiKey });

  let diff = '';
  let prInfo = null;
  let prUrl = null;
  let owner = null, repo = null, number = null;

  if (args.pr) {
    // Fetch PR diff from GitHub
    const result = fetchPRDiff(args.pr);
    diff = result.diff;
    prInfo = result.prInfo;
    prUrl = result.prUrl;
    owner = result.owner;
    repo = result.repo;
    number = result.number;
  } else if (args.diff) {
    // Read diff from file
    diff = readFileSync(args.diff, 'utf-8');
  } else if (!stdin.isTTY) {
    // Read from stdin
    const chunks = [];
    for await (const chunk of stdin) {
      chunks.push(chunk);
    }
    diff = Buffer.concat(chunks).toString('utf-8');
  } else {
    console.error('Error: No input provided. Use --pr <url>, --diff <file>, or pipe a diff to stdin.');
    console.error('Run with --help for usage information.');
    exit(1);
  }

  if (!diff.trim()) {
    console.error('Error: Empty diff provided.');
    exit(1);
  }

  // Generate the review
  const review = await generateReview(client, diff, prInfo, args.model);

  // Add header if we have PR info
  if (prUrl) {
    console.log(`# 🔍 PR Review: ${owner}/${repo}#${number}`);
    console.log(`> ${prUrl}\n`);
  } else {
    console.log('# 🔍 Code Review\n');
  }

  console.log(review);

  // If this is running as a GitHub Action, also set the output
  if (process.env.GITHUB_OUTPUT) {
    const fs = await import('fs');
    fs.appendFileSync(process.env.GITHUB_OUTPUT, `review<<REVIEW_EOF\n${review}\nREVIEW_EOF\n`);
  }
}

main().catch(err => {
  console.error('Error:', err.message);
  exit(1);
});
