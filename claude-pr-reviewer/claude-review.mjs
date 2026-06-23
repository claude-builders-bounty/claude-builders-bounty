#!/usr/bin/env node

/**
 * claude-review — Claude Code sub-agent for PR review
 *
 * Usage:
 *   GITHUB_TOKEN=xxx ./claude-review.mjs --pr https://github.com/owner/repo/pull/123
 *   GITHUB_TOKEN=xxx ./claude-review.mjs --pr https://github.com/owner/repo/pull/123 --output review.md
 *
 * Outputs structured Markdown with: summary, risks, improvements, confidence score.
 */

import { Octokit } from '@octokit/rest';
import { parseArgs } from 'node:util';
import { writeFileSync } from 'node:fs';

function parsePrUrl(url) {
  const m = url.match(/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/);
  if (!m) throw new Error(`Invalid PR URL: ${url}`);
  return { owner: m[1], repo: m[2], pull_number: parseInt(m[3]) };
}

async function getPrDiff(octokit, { owner, repo, pull_number }) {
  const { data } = await octokit.pulls.get({
    owner, repo, pull_number,
    mediaType: { format: 'diff' },
  });
  return data;
}

async function getPrMetadata(octokit, { owner, repo, pull_number }) {
  const { data } = await octokit.pulls.get({ owner, repo, pull_number });
  return {
    title: data.title,
    description: data.body || '(no description)',
    author: data.user?.login || 'unknown',
    base: data.base?.ref,
    head: data.head?.ref,
    files: data.changed_files,
    additions: data.additions,
    deletions: data.deletions,
  };
}

function generateSummary(diff, meta) {
  const lines = diff.split('\n');
  const fileHeaders = lines.filter(l => l.startsWith('diff --git'));
  const addedLines = lines.filter(l => l.startsWith('+') && !l.startsWith('+++')).length;
  const removedLines = lines.filter(l => l.startsWith('-') && !l.startsWith('---')).length;

  return [
    `**PR:** "${meta.title}" by @${meta.author}`,
    `**Branch:** \`${meta.head}\` → \`${meta.base}\``,
    `**Stats:** ${meta.files} files changed, +${meta.additions}/-${meta.deletions}`,
    ``,
    `This change modifies ${fileHeaders.length} file(s) with ${addedLines} additions and ${removedLines} deletions.`,
    `${meta.description ? `\n**Description from author:** ${meta.description.slice(0, 500)}` : ''}`,
  ].join('\n');
}

function identifyRisks(diff, meta) {
  const risks = [];
  const lines = diff.split('\n');

  // Check for risk patterns
  const filePaths = lines.filter(l => l.startsWith('+++') || l.startsWith('---'))
    .map(l => l.replace(/^[-+]{3} [ab]\//, ''));

  // Risk: Database schema changes
  if (filePaths.some(p => p.includes('migration') || p.includes('schema'))) {
    risks.push('⚠️ **Database schema change detected** — verify backward compatibility and rollback plan');
  }

  // Risk: Config changes
  if (filePaths.some(p => p.includes('.env') || p.includes('config') || p.includes('secret'))) {
    risks.push('⚠️ **Configuration change detected** — check for hardcoded secrets or environment-specific values');
  }

  // Risk: Dependency changes
  if (filePaths.some(p => p.includes('package.json') || p.includes('requirements.txt') || p.includes('go.mod'))) {
    risks.push('⚠️ **Dependency change detected** — verify transitive dependency updates and license compatibility');
  }

  // Risk: Large PR
  if (meta.additions + meta.deletions > 1000) {
    risks.push('⚠️ **Large PR** — consider splitting into smaller, focused changes');
  }

  // Risk: Deletion-heavy
  if (meta.deletions > meta.additions * 2 && meta.deletions > 100) {
    risks.push('⚠️ **Heavy deletion ratio** — verify no logic was removed that other parts of the system depend on');
  }

  // Risk: Security-sensitive patterns
  const suspiciousPatterns = [
    { pattern: /eval\(/, desc: 'use of eval()' },
    { pattern: /innerHTML/, desc: 'innerHTML assignment (XSS risk)' },
    { pattern: /\.env[^\.]/, desc: 'possible .env exposure' },
    { pattern: /password|secret|token|api.?key/i, desc: 'possible credential handling in diff' },
    { pattern: /curl|wget.*\||exec\(/, desc: 'command injection risk' },
  ];

  const addedLines = lines.filter(l => l.startsWith('+') && !l.startsWith('+++'));
  for (const { pattern, desc } of suspiciousPatterns) {
    if (addedLines.some(l => pattern.test(l))) {
      risks.push(`🔴 **Potential security concern:** ${desc}`);
    }
  }

  if (risks.length === 0) {
    risks.push('✅ No significant risks identified based on automated analysis');
  }

  return risks.join('\n');
}

function generateImprovements(diff, meta) {
  const suggestions = [];
  const lines = diff.split('\n');
  const addedLines = lines.filter(l => l.startsWith('+') && !l.startsWith('+++'));

  // Check for missing error handling
  const tryCatchCount = (diff.match(/try\s*\{/g) || []).length;
  const riskCount = (diff.match(/\.catch\s*\(/g) || []).length;
  if (tryCatchCount === 0 && riskCount === 0 && meta.additions > 50) {
    suggestions.push('Consider adding error handling (try/catch) for new async operations');
  }

  // Check for console.log in production code
  if (addedLines.some(l => l.includes('console.log') || l.includes('console.error'))) {
    suggestions.push('Remove `console.log` statements before merge (use proper logging)');
  }

  // Check for TODO/FIXME in added lines
  if (addedLines.some(l => l.includes('TODO') || l.includes('FIXME') || l.includes('HACK'))) {
    suggestions.push('Address or track TODO/FIXME/HACK comments before merge');
  }

  // Check for commented-out code
  if (addedLines.some(l => l.trimStart().startsWith('//') || l.trimStart().startsWith('#'))) {
    // Only flag if there are many comment-only additions
    const commentLines = addedLines.filter(l => /^\+\s*(\/\/|#|<!--|\*)/.test(l)).length;
    if (commentLines > meta.additions * 0.3) {
      suggestions.push('High comment-to-code ratio — consider if all comments are necessary');
    }
  }

  // Check test coverage
  const hasTests = filePaths => {
    if (!filePaths) return false;
    const sources = filePaths.filter(p => !p.includes('test') && !p.includes('spec') && !p.includes('__tests__'));
    const tests = filePaths.filter(p => p.includes('test') || p.includes('spec') || p.includes('__tests__'));
    return sources.length > 0 && tests.length === 0;
  };
  const filePaths = lines.filter(l => l.startsWith('+++'))
    .map(l => l.replace(/^\+{3} [ab]\//, ''));
  if (hasTests(filePaths)) {
    suggestions.push('Consider adding tests for the changes in this PR');
  }

  if (suggestions.length === 0) {
    suggestions.push('✅ No improvement suggestions from automated analysis');
  }

  return suggestions.map((s, i) => `${i+1}. ${s}`).join('\n');
}

function assessConfidence(diff, meta) {
  const lines = diff.split('\n');
  const filePaths = lines.filter(l => l.startsWith('+++') || l.startsWith('---'))
    .map(l => l.replace(/^[-+]{3} [ab]\//, ''));

  let score = 5; // start at medium

  // Small, focused PR = higher confidence
  if (meta.files <= 3 && meta.additions + meta.deletions < 200) score += 3;
  if (meta.files <= 5 && meta.additions + meta.deletions < 500) score += 2;

  // Has tests = higher confidence
  if (filePaths.some(p => p.includes('test') || p.includes('spec'))) score += 2;

  // Has description = higher confidence
  if (meta.description && meta.description.length > 20) score += 1;

  // Large PR = lower confidence
  if (meta.additions + meta.deletions > 1000) score -= 2;
  if (meta.additions + meta.deletions > 2000) score -= 2;

  // Security concerns = lower confidence
  if (identifyRisks(diff, meta).includes('🔴')) score -= 2;

  return score <= 3 ? 'Low' : score <= 5 ? 'Medium' : 'High';
}

function generateReview(diff, meta) {
  const summary = generateSummary(diff, meta);
  const risks = identifyRisks(diff, meta);
  const improvements = generateImprovements(diff, meta);
  const confidence = assessConfidence(diff, meta);

  return [
    '# 🔍 PR Review',
    '',
    '---',
    '',
    '## Summary',
    '',
    summary,
    '',
    '---',
    '',
    '## Identified Risks',
    '',
    risks,
    '',
    '---',
    '',
    '## Improvement Suggestions',
    '',
    improvements,
    '',
    '---',
    '',
    `## Confidence Score: **${confidence}**`,
    '',
    `*Automated review generated by claude-review — review manually before merging.*`,
  ].join('\n');
}

async function main() {
  const args = parseArgs({
    options: {
      pr: { type: 'string' },
      output: { type: 'string', default: '' },
    },
  });

  const prUrl = args.values.pr;
  if (!prUrl) {
    console.error('Usage: claude-review --pr <PR_URL> [--output <file>]');
    process.exit(1);
  }

  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    console.error('GITHUB_TOKEN environment variable required');
    process.exit(1);
  }

  const octokit = new Octokit({ auth: token });
  const prInfo = parsePrUrl(prUrl);

  console.error(`Fetching PR: ${prUrl}`);
  const [diff, meta] = await Promise.all([
    getPrDiff(octokit, prInfo),
    getPrMetadata(octokit, prInfo),
  ]);

  console.error(`Analyzing (${meta.files} files, +${meta.additions}/-${meta.deletions})...`);
  const review = generateReview(diff, meta);

  const outputPath = args.values.output;
  if (outputPath) {
    writeFileSync(outputPath, review, 'utf-8');
    console.error(`Review written to: ${outputPath}`);
  } else {
    console.log(review);
  }
}

main().catch(err => {
  console.error('Error:', err.message);
  process.exit(1);
});
