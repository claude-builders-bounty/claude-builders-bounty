import { execSync } from 'child_process';
import { readFileSync } from 'fs';

/**
 * Parse a PR URL to extract owner, repo, and PR number
 */
function parsePRUrl(prUrl) {
  const match = prUrl.match(/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/);
  if (!match) {
    throw new Error('Invalid PR URL format. Expected: https://github.com/owner/repo/pull/123');
  }
  return {
    owner: match[1],
    repo: match[2],
    prNumber: match[3]
  };
}

/**
 * Fetch PR details using gh CLI
 */
function getPRDetails(owner, repo, prNumber) {
  const details = JSON.parse(
    execSync(`gh pr view ${prNumber} --repo ${owner}/${repo} --json title,body,state,author,additions,deletions,changedFiles,url`, {
      encoding: 'utf-8'
    })
  );
  return details;
}

/**
 * Fetch the PR diff
 */
function getPRDiff(owner, repo, prNumber) {
  return execSync(`gh pr diff ${prNumber} --repo ${owner}/${repo}`, {
    encoding: 'utf-8'
  });
}

/**
 * Fetch recent commits for context
 */
function getPRCommits(owner, repo, prNumber) {
  return JSON.parse(
    execSync(`gh api repos/${owner}/${repo}/pulls/${prNumber}/commits -q '.[] | {sha: .sha, message: .commit.message}'`, {
      encoding: 'utf-8'
    })
  );
}

/**
 * Generate review using Claude via OpenAI-compatible API
 */
async function generateReview({ diff, prDetails, commits, model }) {
  const apiKey = process.env.ANTHROPIC_KEY || process.env.OPENAI_API_KEY;
  
  if (!apiKey) {
    // Fall back to a template-based review if no API key
    return generateTemplateReview(diff, prDetails, commits);
  }

  // Try Anthropic API first (Claude)
  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: model || 'claude-3-5-sonnet-20241022',
        max_tokens: 4096,
        messages: [{
          role: 'user',
          content: `You are an expert code reviewer. Analyze the following PR and provide a structured review.

PR Title: ${prDetails.title}
PR Description: ${prDetails.body || 'No description provided'}
Author: ${prDetails.author?.login || 'Unknown'}
URL: ${prDetails.url}

Changed Files: ${prDetails.changedFiles}
Additions: +${prDetails.additions}
Deletions: -${prDetails.deletions}

Commits:
${commits.map(c => `- ${c.message}`).join('\n')}

DIFF:
${diff.slice(0, 80000)}

Provide a structured code review in Markdown format with:
1. **Summary** (2-3 sentences describing what this PR does)
2. **Risks** (potential issues, bugs, security concerns)
3. **Suggestions** (improvement recommendations)
4. **Confidence Score** (Low/Medium/High based on code quality and testing)

Be thorough and specific. Reference actual code from the diff when possible.`
        }]
      })
    });

    if (response.ok) {
      const data = await response.json();
      return data.content[0].text;
    }
  } catch (e) {
    console.error('Anthropic API error:', e.message);
  }

  // Fall back to template review
  return generateTemplateReview(diff, prDetails, commits);
}

/**
 * Generate a template-based review when no API key is available
 */
function generateTemplateReview(diff, prDetails, commits) {
  const lines = diff.split('\n');
  const files = [];
  let currentFile = null;
  
  for (const line of lines) {
    if (line.startsWith('diff --git')) {
      const match = line.match(/diff --git a\/(.+?) b\/(.+)/);
      if (match) {
        currentFile = { file: match[2], additions: 0, deletions: 0, changes: [] };
      }
    } else if (line.startsWith('+') && !line.startsWith('+++')) {
      if (currentFile) currentFile.additions++;
    } else if (line.startsWith('-') && !line.startsWith('---')) {
      if (currentFile) currentFile.deletions++;
    }
    if (currentFile) {
      currentFile.changes.push(line);
    }
  }
  if (currentFile) files.push(currentFile);

  const fileCount = files.length;
  const additions = prDetails.additions || 0;
  const deletions = prDetails.deletions || 0;

  // Analyze risks based on diff patterns
  const risks = [];
  const suggestions = [];
  
  // Check for common issues
  const diffText = diff.toLowerCase();
  
  if (diffText.includes('password') || diffText.includes('secret') || diffText.includes('api_key')) {
    risks.push('Potential hardcoded secrets or credentials detected');
  }
  if (diffText.includes('eval(') || diffText.includes('exec(')) {
    risks.push('Dynamic code execution detected - potential security risk');
  }
  if (diffText.includes('todo') || diffText.includes('fixme')) {
    suggestions.push('Address TODO/FIXME comments before merging');
  }
  if (diffText.includes('.env')) {
    risks.push('Environment file changes detected - ensure no secrets are exposed');
  }
  if (diffText.includes('sql') && diffText.includes('select') && diffText.includes('where')) {
    suggestions.push('Verify SQL queries use parameterized statements to prevent injection');
  }
  
  // Check for test coverage
  const hasTests = diffText.includes('test') || diffText.includes('.spec.') || diffText.includes('.test.');
  if (!hasTests && fileCount > 2) {
    suggestions.push('Consider adding tests for new functionality');
  }

  // Determine confidence based on various factors
  let confidence = 'Medium';
  if (risks.length === 0 && hasTests && fileCount <= 5) {
    confidence = 'High';
  } else if (risks.length > 2 || (!hasTests && fileCount > 10)) {
    confidence = 'Low';
  }

  return `## PR Review: ${prDetails.title}

### Summary
${prDetails.body || 'No description provided.'}

This PR modifies ${fileCount} file(s), adding ${additions} lines and removing ${deletions} lines. The changes are authored by ${prDetails.author?.login || 'unknown'}.

### Identified Risks
${risks.length > 0 ? risks.map(r => `- ⚠️ ${r}`).join('\n') : '✅ No obvious risks detected'}

### Improvement Suggestions
${suggestions.length > 0 ? suggestions.map(s => `- 💡 ${s}`).join('\n') : '✅ Code looks good overall'}

### Confidence Score: ${confidence}

---
*Note: This review was generated using template-based analysis. For more detailed reviews, set ANTHROPIC_KEY environment variable.*`;
}

/**
 * Post review comment to GitHub
 */
function postReviewComment(owner, repo, prNumber, comment) {
  execSync(`gh pr comment ${prNumber} --repo ${owner}/${repo} --body '${comment.replace(/'/g, "'\"'\"'")}'`, {
    encoding: 'utf-8'
  });
}

/**
 * Main review function
 */
export async function reviewPR({ prUrl, githubToken, model, postComment = false }) {
  const { owner, repo, prNumber } = parsePRUrl(prUrl);
  
  // Set GitHub token if provided
  if (githubToken) {
    process.env.GITHUB_TOKEN = githubToken;
  }

  // Fetch PR data
  const prDetails = getPRDetails(owner, repo, prNumber);
  const diff = getPRDiff(owner, repo, prNumber);
  let commits = [];
  try {
    commits = getPRCommits(owner, repo, prNumber);
  } catch (e) {
    // Commits are nice-to-have
  }

  // Generate review
  const review = await generateReview({
    diff,
    prDetails,
    commits,
    model
  });

  // Post comment if requested
  if (postComment) {
    postReviewComment(owner, repo, prNumber, review);
  }

  return review;
}
