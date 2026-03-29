#!/usr/bin/env node
/**
 * claude-review — Claude-powered PR reviewer
 * Usage: node claude-review.js --pr https://github.com/owner/repo/pull/123
 * 
 * Requires: ANTHROPIC_API_KEY and GITHUB_TOKEN environment variables
 */

const https = require('https');
const { URL } = require('url');

// --- Config ---
const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY;
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const MODEL = 'claude-sonnet-4-20250514';

// --- Parse args ---
function parseArgs() {
  const args = process.argv.slice(2);
  let prUrl = '';
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--pr' && args[i + 1]) {
      prUrl = args[i + 1];
      break;
    }
  }
  if (!prUrl) {
    console.error('Usage: claude-review --pr <github-pr-url>');
    process.exit(1);
  }
  const match = prUrl.match(/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/);
  if (!match) {
    console.error('Invalid PR URL. Expected: https://github.com/owner/repo/pull/123');
    process.exit(1);
  }
  return { owner: match[1], repo: match[2], number: parseInt(match[3]) };
}

// --- HTTP helpers ---
function httpGet(url, headers = {}) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const opts = {
      hostname: u.hostname,
      path: u.pathname + u.search,
      method: 'GET',
      headers: { 'User-Agent': 'claude-pr-reviewer/1.0', ...headers }
    };
    const req = https.request(opts, res => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); } catch { resolve(data); }
      });
    });
    req.on('error', reject);
    req.end();
  });
}

function httpPost(url, body, headers = {}) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const payload = JSON.stringify(body);
    const opts = {
      hostname: u.hostname,
      path: u.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload),
        'User-Agent': 'claude-pr-reviewer/1.0',
        ...headers
      }
    };
    const req = https.request(opts, res => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); } catch { resolve(data); }
      });
    });
    req.on('error', reject);
    req.write(payload);
    req.end();
  });
}

// --- GitHub API ---
async function fetchPR(owner, repo, number) {
  const ghHeaders = GITHUB_TOKEN
    ? { Authorization: `token ${GITHUB_TOKEN}`, Accept: 'application/vnd.github.v3+json' }
    : { Accept: 'application/vnd.github.v3+json' };
  
  const [pr, diff] = await Promise.all([
    httpGet(`https://api.github.com/repos/${owner}/${repo}/pulls/${number}`, ghHeaders),
    httpGet(`https://api.github.com/repos/${owner}/${repo}/pulls/${number}`, {
      ...ghHeaders,
      Accept: 'application/vnd.github.v3.diff'
    })
  ]);
  
  return { pr, diff: typeof diff === 'string' ? diff : JSON.stringify(diff) };
}

// --- Claude API ---
async function reviewWithClaude(pr, diff) {
  const truncatedDiff = diff.length > 15000 ? diff.slice(0, 15000) + '\n\n[... diff truncated at 15000 chars ...]' : diff;
  
  const prompt = `You are an expert code reviewer. Review this GitHub Pull Request and provide a structured analysis.

## PR Information
- **Title:** ${pr.title}
- **Author:** ${pr.user?.login || 'unknown'}
- **Base:** ${pr.base?.ref || 'main'} ← ${pr.head?.ref || 'feature'}
- **Description:** ${pr.body || 'No description provided'}
- **Files Changed:** ${pr.changed_files || '?'}
- **Additions:** +${pr.additions || '?'} / Deletions: -${pr.deletions || '?'}

## Diff
\`\`\`diff
${truncatedDiff}
\`\`\`

Provide your review in this exact Markdown format:

## 📝 Summary
(2-3 sentences describing what this PR does and its purpose)

## ⚠️ Identified Risks
(Bulleted list of potential risks, edge cases, or concerns. If none, say "No significant risks identified.")

## 💡 Improvement Suggestions
(Bulleted list of actionable suggestions to improve the code. If none, say "Code looks good as-is.")

## 🎯 Confidence Score
(One of: **Low** / **Medium** / **High** — how confident you are in the review quality based on the diff provided)

Be specific, reference file names and line numbers where possible.`;

  const response = await httpPost('https://api.anthropic.com/v1/messages', {
    model: MODEL,
    max_tokens: 2048,
    messages: [{ role: 'user', content: prompt }]
  }, {
    'x-api-key': ANTHROPIC_API_KEY,
    'anthropic-version': '2023-06-01'
  });

  if (response.content && response.content[0]) {
    return response.content[0].text;
  }
  throw new Error('Claude API error: ' + JSON.stringify(response));
}

// --- Main ---
async function main() {
  if (!ANTHROPIC_API_KEY) {
    console.error('Error: ANTHROPIC_API_KEY environment variable required');
    process.exit(1);
  }

  const { owner, repo, number } = parseArgs();
  console.error(`🔍 Reviewing ${owner}/${repo}#${number}...`);

  const { pr, diff } = await fetchPR(owner, repo, number);
  
  if (pr.message === 'Not Found') {
    console.error(`Error: PR #${number} not found in ${owner}/${repo}`);
    process.exit(1);
  }

  console.error(`📋 "${pr.title}" by ${pr.user?.login}`);
  console.error(`   ${pr.changed_files} files, +${pr.additions}/-${pr.deletions}`);
  console.error(`🤖 Calling Claude ${MODEL}...`);

  const review = await reviewWithClaude(pr, diff);
  
  // Output the review to stdout
  const header = `# 🤖 Claude PR Review: ${owner}/${repo}#${number}\n\n**PR:** ${pr.title}  \n**Author:** @${pr.user?.login}  \n**Review Date:** ${new Date().toISOString().split('T')[0]}\n\n---\n\n`;
  
  console.log(header + review);
}

main().catch(err => {
  console.error('Fatal error:', err.message);
  process.exit(1);
});
