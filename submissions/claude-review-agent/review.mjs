// Core review logic — runs Claude Code to analyze PR diff
// This module can be used standalone or via CLI

import { execSync } from 'child_process';
import { writeFileSync, mkdirSync } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/**
 * Review a PR diff and return structured Markdown
 * @param {string} diff - The git diff content
 * @param {string} prUrl - Optional PR URL for context
 * @returns {Promise<string>} Structured Markdown review
 */
export async function reviewPR(diff, prUrl = '') {
  // Truncate diff if too large (Claude context limits)
  const MAX_DIFF_LENGTH = 50000;
  let truncatedDiff = diff;
  if (diff.length > MAX_DIFF_LENGTH) {
    const lines = diff.split('\n');
    truncatedDiff = lines.slice(0, 500).join('\n');
    truncatedDiff += `\n\n... (${lines.length - 500} more lines truncated)`;
  }

  // Build the review prompt
  const prompt = buildReviewPrompt(truncatedDiff, prUrl);

  // Run via Claude Code CLI
  try {
    const review = runClaudeCode(prompt);
    return formatOutput(review, prUrl);
  } catch (err) {
    // Fallback: generate review without Claude if CLI unavailable
    return generateFallbackReview(truncatedDiff, prUrl);
  }
}

function buildReviewPrompt(diff, prUrl) {
  return `You are a senior software engineer conducting a code review.

Review the following PR diff and output a structured review in Markdown.

${prUrl ? `PR: ${prUrl}\n` : ''}

## Requirements for your review:

1. **Summary**: 2-3 sentences describing what this PR does
2. **Identified Risks**: List potential issues (bugs, security, performance, breaking changes)
3. **Improvement Suggestions**: Actionable suggestions for better code quality
4. **Confidence Score**: Low / Medium / High (how confident are you in this review)

Format your response EXACTLY as follows:

## 📋 Summary
[2-3 sentences]

## ⚠️ Identified Risks
- [risk 1]
- [risk 2]

## 💡 Improvement Suggestions
- [suggestion 1]
- [suggestion 2]

## 🎯 Confidence: [Low/Medium/High]

---

Here is the PR diff:

\`\`\`diff
${diff}
\`\`\`

Now output your structured review:`;
}

function runClaudeCode(prompt) {
  // Try to use Claude Code CLI if available
  const workDir = path.join(__dirname, 'work');
  mkdirSync(workDir, { recursive: true });
  
  const promptFile = path.join(workDir, 'review-prompt.txt');
  writeFileSync(promptFile, prompt);

  try {
    // Use claude command if installed
    const result = execSync(`cat "${promptFile}" | claude --print --output-format text 2>/dev/null || echo "CLAUDE_NOT_FOUND"`, {
      encoding: 'utf-8',
      timeout: 120000,
      maxBuffer: 10 * 1024 * 1024
    });
    
    if (result.includes('CLAUDE_NOT_FOUND')) {
      throw new Error('Claude CLI not available');
    }
    
    return result.trim();
  } catch (err) {
    throw err;
  }
}

function generateFallbackReview(diff, prUrl) {
  // Analyze diff statically for a basic review
  const stats = analyzeDiff(diff);
  
  return `## 📋 Summary
${prUrl ? `This PR (${prUrl}) ` : 'This change '}modifies ${stats.fileCount} file(s) with ${stats.additions} additions and ${stats.deletions} deletions. ${stats.summary}

## ⚠️ Identified Risks
${stats.risks.length > 0 ? stats.risks.map(r => `- ${r}`).join('\n') : '- No obvious risks detected from static analysis'}

## 💡 Improvement Suggestions
${stats.suggestions.length > 0 ? stats.suggestions.map(s => `- ${s}`).join('\n') : '- Consider adding/updating tests for changed code\n- Ensure documentation is updated if API surface changed'}

## 🎯 Confidence: Medium

> ℹ️ This review was generated via static analysis (Claude Code not detected in environment). For a more thorough review, install Claude Code and set ANTHROPIC_API_KEY.`;
}

function analyzeDiff(diff) {
  const lines = diff.split('\n');
  let additions = 0;
  let deletions = 0;
  const files = new Set();
  const risks = [];
  const suggestions = [];
  let currentFile = '';

  for (const line of lines) {
    if (line.startsWith('diff --git')) {
      const match = line.match(/b\/(.+)/);
      if (match) {
        currentFile = match[1];
        files.add(currentFile);
      }
    }
    
    if (line.startsWith('+') && !line.startsWith('+++')) {
      additions++;
      
      // Detect potential issues
      if (line.includes('console.log') || line.includes('console.debug')) {
        if (!suggestions.find(s => s.includes('console.log'))) {
          suggestions.push('Found debug logging (console.log/debug) — consider removing before merge');
        }
      }
      if (line.includes('TODO') || line.includes('FIXME') || line.includes('HACK')) {
        risks.push(`Found TODO/FIXME/HACK in ${currentFile} — ensure these are tracked`);
      }
      if (line.includes('password') || line.includes('secret') || line.includes('api_key') || line.includes('token')) {
        risks.push(`⚠️ Potential hardcoded credential in ${currentFile} — use environment variables instead`);
      }
    }
    
    if (line.startsWith('-') && !line.startsWith('---')) {
      deletions++;
    }

    // Check for deleted tests
    if (line.startsWith('-') && (currentFile.includes('.test.') || currentFile.includes('.spec.') || currentFile.includes('__tests__'))) {
      risks.push(`Test file modified: ${currentFile} — ensure test coverage is maintained`);
    }

    // Check for large file changes
    if (line.startsWith('+') && line.length > 200) {
      suggestions.push(`Long line detected in ${currentFile} — consider breaking into multiple lines`);
    }
  }

  const fileTypes = new Set();
  for (const f of files) {
    const ext = path.extname(f).toLowerCase();
    if (ext) fileTypes.add(ext);
  }

  // Build summary
  let summary = '';
  if (files.size === 0) {
    summary = 'No file changes detected.';
  } else if (files.size === 1) {
    const file = [...files][0];
    summary = `Single file change in \`${file}\`.`;
  } else {
    const fileList = [...files].slice(0, 3).map(f => `\`${f}\``).join(', ');
    summary = `Changes span ${files.size} files including ${fileList}${files.size > 3 ? `, and ${files.size - 3} more` : ''}.`;
  }

  // Contextual suggestions
  const hasTests = [...files].some(f => f.includes('.test.') || f.includes('.spec.') || f.includes('__tests__'));
  if (!hasTests && files.size > 0) {
    suggestions.push('No test files changed — consider adding tests for modified logic');
  }

  if (fileTypes.has('.md') || fileTypes.has('.mdx')) {
    // Docs change — fewer risks
  } else if (files.size > 5) {
    risks.push(`Large PR: ${files.size} files changed — consider splitting into smaller PRs`);
  }

  // Deduplicate
  const uniqueRisks = [...new Set(risks)].slice(0, 5);
  const uniqueSuggestions = [...new Set(suggestions)].slice(0, 5);

  return {
    fileCount: files.size,
    additions,
    deletions,
    summary,
    risks: uniqueRisks,
    suggestions: uniqueSuggestions
  };
}

function formatOutput(review, prUrl) {
  return review;
}
