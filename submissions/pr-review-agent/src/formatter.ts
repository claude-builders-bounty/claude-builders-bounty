import chalk from 'chalk';
import { PRInfo, PRDiff, ReviewResult, ReviewConfig } from './types.js';

export function formatReview(
  pr: PRInfo,
  diff: PRDiff,
  review: ReviewResult,
  config: ReviewConfig
): string {
  if (config.format === 'json') {
    return JSON.stringify({ pr, diff, review }, null, 2);
  }

  if (config.format === 'markdown') {
    return generateMarkdown(pr, diff, review);
  }

  return generateConsoleOutput(pr, diff, review);
}

function generateMarkdown(pr: PRInfo, diff: PRDiff, review: ReviewResult): string {
  let md = `## 🤖 Claude PR Review\n\n`;
  md += `> **PR**: #${pr.number} — ${pr.title}\n`;
  md += `> **Author**: @${pr.author} | **Branch**: ${pr.headBranch} → ${pr.baseBranch}\n`;
  md += `> **Files Changed**: ${diff.files} | **Additions**: +${diff.additions} | **Deletions**: -${diff.deletions}\n\n`;
  md += `---\n\n`;
  
  md += `### 📋 Summary\n${review.summary}\n\n`;

  if (review.risks.length > 0) {
    md += `### ⚠️ Identified Risks\n`;
    md += `| # | Risk | Severity | Details |\n`;
    md += `|---|------|----------|---------|\n`;
    review.risks.forEach((risk, i) => {
      const details = [risk.file, risk.line ? `L${risk.line}` : null].filter(Boolean).join(':');
      md += `| ${i + 1} | ${risk.description} | ${capitalize(risk.severity)} | ${details || 'General'} |\n`;
    });
    md += `\n`;
  }

  if (review.suggestions.length > 0) {
    md += `### 💡 Improvement Suggestions\n`;
    md += `| # | Suggestion | Priority | File |\n`;
    md += `|---|------------|----------|------|\n`;
    review.suggestions.forEach((sug, i) => {
      md += `| ${i + 1} | ${sug.description} | ${capitalize(sug.priority)} | ${sug.file ? '`' + sug.file + '`' : 'General'} |\n`;
    });
    md += `\n`;
  }

  if (review.securityNotes.length > 0) {
    md += `### 🔒 Security Notes\n`;
    review.securityNotes.forEach(note => {
      md += `- ${note}\n`;
    });
    md += `\n`;
  }

  md += `### ✅ Confidence: **${review.confidence}**\n\n`;
  md += `---\n`;
  md += `*Reviewed by [claude-pr-reviewer](https://github.com/claude-builders-bounty/claude-builders-bounty) • Powered by Claude Sonnet*\n`;

  return md;
}

function generateConsoleOutput(pr: PRInfo, diff: PRDiff, review: ReviewResult): string {
  let out = chalk.bold.cyan(`\n🤖 Claude PR Review\n`);
  out += chalk.gray(`PR: #${pr.number} — ${pr.title}\n`);
  out += chalk.gray(`Author: @${pr.author} | Branch: ${pr.headBranch} → ${pr.baseBranch}\n`);
  out += chalk.gray(`Files Changed: ${diff.files} | Additions: +${diff.additions} | Deletions: -${diff.deletions}\n\n`);
  
  out += chalk.bold.blue(`📋 Summary\n`);
  out += `${review.summary}\n\n`;

  if (review.risks.length > 0) {
    out += chalk.bold.yellow(`⚠️ Identified Risks\n`);
    review.risks.forEach((risk, i) => {
      const color = risk.severity === 'critical' ? chalk.red.bold : 
                    risk.severity === 'high' ? chalk.red : 
                    risk.severity === 'medium' ? chalk.yellow : chalk.green;
      out += `${i + 1}. [${color(risk.severity.toUpperCase())}] ${risk.description}\n`;
      if (risk.file) out += chalk.gray(`   File: ${risk.file}${risk.line ? `:${risk.line}` : ''}\n`);
    });
    out += `\n`;
  }

  if (review.suggestions.length > 0) {
    out += chalk.bold.green(`💡 Improvement Suggestions\n`);
    review.suggestions.forEach((sug, i) => {
      const color = sug.priority === 'high' ? chalk.red : 
                    sug.priority === 'medium' ? chalk.yellow : chalk.green;
      out += `${i + 1}. [${color(sug.priority.toUpperCase())}] ${sug.description}\n`;
      if (sug.file) out += chalk.gray(`   File: ${sug.file}\n`);
    });
    out += `\n`;
  }

  if (review.securityNotes.length > 0) {
    out += chalk.bold.magenta(`🔒 Security Notes\n`);
    review.securityNotes.forEach(note => {
      out += `- ${note}\n`;
    });
    out += `\n`;
  }

  out += chalk.bold(`Confidence: ${review.confidence}\n`);

  return out;
}

function capitalize(str: string): string {
  if (!str) return str;
  return str.charAt(0).toUpperCase() + str.slice(1);
}
