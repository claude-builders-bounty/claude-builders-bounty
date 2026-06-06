/**
 * PR Reviewer — Core logic
 * 
 * Fetches a PR diff, analyzes changes, and returns a structured review.
 * Uses pattern matching and static analysis — no external LLM required.
 */

import fs from 'fs';
import https from 'https';

/**
 * Parse a GitHub PR URL to extract owner, repo, and PR number
 */
function parsePRUrl(url) {
  const match = url.match(/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/);
  if (!match) throw new Error(`Invalid GitHub PR URL: ${url}`);
  return { owner: match[1], repo: match[2], pr: parseInt(match[3]) };
}

/**
 * Fetch PR data from GitHub API
 */
function githubFetch(path) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'api.github.com',
      path: path,
      headers: {
        'User-Agent': 'claude-review/1.0',
        'Accept': 'application/vnd.github.v3.diff',
        ...(process.env.GITHUB_TOKEN ? { 'Authorization': `Bearer ${process.env.GITHUB_TOKEN}` } : {})
      }
    };
    
    https.get(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode === 404) reject(new Error(`Resource not found: ${path}`));
        else if (res.statusCode === 403) reject(new Error(`Rate limited. Set GITHUB_TOKEN.`));
        else if (res.statusCode >= 400) reject(new Error(`HTTP ${res.statusCode}: ${data.slice(0,200)}`));
        else resolve(data);
      });
    }).on('error', reject);
  });
}

/**
 * Fetch PR diff from GitHub
 */
async function fetchDiff(owner, repo, pr) {
  const diff = await githubFetch(`/repos/${owner}/${repo}/pulls/${pr}`);
  return diff;
}

/**
 * Fetch PR metadata
 */
async function fetchPRMetadata(owner, repo, pr) {
  const patch = await githubFetch(`/repos/${owner}/${repo}/pulls/${pr}`);
  // Re-fetch with JSON accept header for metadata
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'api.github.com',
      path: `/repos/${owner}/${repo}/pulls/${pr}`,
      headers: {
        'User-Agent': 'claude-review/1.0',
        'Accept': 'application/json',
        ...(process.env.GITHUB_TOKEN ? { 'Authorization': `Bearer ${process.env.GITHUB_TOKEN}` } : {})
      }
    };
    
    https.get(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); }
        catch(e) { reject(new Error('Failed to parse PR metadata')); }
      });
    }).on('error', reject);
  });
}

/**
 * Parse diff into structured file changes
 */
function parseDiff(diff) {
  const files = [];
  const fileBlocks = diff.split(/\ndiff --git /);
  
  for (const block of fileBlocks) {
    if (!block.trim()) continue;
    
    // Extract filename from "diff --git a/file b/file"
    const fileMatch = block.match(/a\/(.+?)\s+b\/(.+?)(?:\n|$)/);
    if (!fileMatch) continue;
    
    const filename = fileMatch[2];
    const header = block.split(/\n@@/)[0];
    
    // Count added/removed lines
    const addedLines = (block.match(/\n\+[^+]/g) || []).length;
    const removedLines = (block.match(/\n\-[^-]/g) || []).length;
    
    // Count total hunks
    const hunks = (block.match(/@@ /g) || []).length;
    
    // Detect file type
    const ext = filename.split('.').pop();
    const languageMap = {
      'js': 'JavaScript', 'ts': 'TypeScript', 'tsx': 'TypeScript React',
      'jsx': 'JavaScript React', 'py': 'Python', 'rs': 'Rust',
      'go': 'Go', 'java': 'Java', 'rb': 'Ruby', 'php': 'PHP',
      'css': 'CSS', 'html': 'HTML', 'json': 'JSON', 'md': 'Markdown',
      'yaml': 'YAML', 'yml': 'YAML', 'toml': 'TOML', 'sh': 'Shell',
      'sql': 'SQL', 'graphql': 'GraphQL', 'proto': 'Protobuf',
    };
    
    files.push({
      filename,
      extension: ext,
      language: languageMap[ext] || ext.toUpperCase(),
      addedLines,
      removedLines,
      totalChanges: addedLines + removedLines,
      hunks,
      diff: `diff --git ${block}`
    });
  }
  
  return files;
}

/**
 * Analyze a single diff block for risks and issues
 */
function analyzeDiffBlock(file) {
  const risks = [];
  const suggestions = [];
  const diff = file.diff;
  
  // Risk: Console.log statements
  if (/console\.(log|debug|warn|error)\(/.test(diff)) {
    risks.push('Console statement found — remove or replace with proper logging before merge');
  }
  
  // Risk: TODO/FIXME comments
  const todos = diff.match(/(TODO|FIXME|HACK|XXX|BUG):?\s*.+/g);
  if (todos) {
    risks.push(`${todos.length} unresolved TODO/FIXME markers present`);
  }
  
  // Risk: Hardcoded secrets
  const secretPatterns = [
    /(?:api[_-]?key|secret|password|token|credential)\s*[=:]\s*['"][^'"]+['"]/i,
    /(?:sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{36,}|AKIA[0-9A-Z]{16})/,
  ];
  for (const pattern of secretPatterns) {
    if (pattern.test(diff)) {
      risks.push('⚠️ POTENTIAL SECRET LEAK — hardcoded credential detected');
      break;
    }
  }
  
  // Risk: Large file changes
  if (file.totalChanges > 200) {
    risks.push(`Large file change (${file.totalChanges} lines) — consider breaking into smaller PRs`);
  }
  
  // Risk: Direct eval or dangerous functions
  if (/\beval\s*\(/.test(diff)) risks.push('`eval()` usage — security risk');
  if (/innerHTML\s*=/.test(diff)) suggestions.push('Prefer `textContent` or DOM methods over `innerHTML` to avoid XSS');
  
  // Suggestion: Missing error handling
  if (/\.then\(/.test(diff) && !/\.catch\(/.test(diff) && !/try\s*\{/.test(diff)) {
    suggestions.push('Promise chain without `.catch()` — add error handling');
  }
  
  // Suggestion: Type safety
  if (file.extension === 'ts' || file.extension === 'tsx') {
    const anyCount = (diff.match(/: any/g) || []).length;
    if (anyCount > 2) {
      suggestions.push(`Consider replacing \`any\` types (${anyCount} occurrences) with proper types`);
    }
  }
  
  // Suggestion: Magic numbers
  const magicNumbers = diff.match(/(?<!=)\b\d{4,}\b(?!\.)/g);
  if (magicNumbers && magicNumbers.length > 3) {
    suggestions.push(`Extract magic numbers (${magicNumbers.length} found) into named constants`);
  }
  
  // Suggestion: Long functions
  const functionCount = (diff.match(/(?:function\s+\w+\s*\(|=>\s*\{)/g) || []).length;
  if (functionCount > 5 && file.addedLines > 100) {
    suggestions.push('Consider extracting smaller functions for readability and testability');
  }
  
  // Suggestion: No tests
  if (!file.filename.includes('.test.') && !file.filename.includes('.spec.') && 
      file.filename.match(/\.(ts|js|tsx|jsx)$/) && file.addedLines > 30) {
    if (!diff.includes('__tests__') && !diff.includes('__mocks__')) {
      suggestions.push('Consider adding tests for the new logic');
    }
  }
  
  return { risks, suggestions };
}

/**
 * Generate confidence score based on analysis depth
 */
function calculateConfidence(files, allRisks, allSuggestions) {
  let score = 70; // Base confidence
  
  // More files = more analysis surface = lower confidence per file
  if (files.length <= 3) score += 10;
  if (files.length > 10) score -= 10;
  
  // Risks found = analysis is working
  if (allRisks.length > 0) score += 5;
  
  // Suggestions found = thorough analysis
  if (allSuggestions.length > 2) score += 5;
  if (allSuggestions.length > 5) score += 5;
  
  // Large PR = harder to review thoroughly
  const totalLines = files.reduce((s, f) => s + f.totalChanges, 0);
  if (totalLines > 500) score -= 10;
  if (totalLines < 50) score += 5;
  
  return Math.max(10, Math.min(99, score));
}

/**
 * Format the review as structured Markdown
 */
function formatReview({ repoInfo, files, allRisks, allSuggestions, confidence }) {
  const summaryItems = [];
  
  if (files.length > 0) {
    summaryItems.push(`**${files.length}** file(s) changed`);
    const totalAdded = files.reduce((s, f) => s + f.addedLines, 0);
    const totalRemoved = files.reduce((s, f) => s + f.removedLines, 0);
    summaryItems.push(`**+${totalAdded}** / **-${totalRemoved}** lines`);
  }
  
  if (allRisks.length > 0) {
    summaryItems.push(`**${allRisks.length}** risk(s) identified`);
  }
  
  if (allSuggestions.length > 0) {
    summaryItems.push(`**${allSuggestions.length}** improvement suggestion(s)`);
  }
  
  let output = `## 🔍 PR Review\n\n`;
  output += `### Summary\n\n`;
  output += `This review covers ${summaryItems.join(' · ')}.\n\n`;
  
  if (repoInfo) {
    output += `**Repository:** ${repoInfo}\n\n`;
  }
  
  // Files changed
  output += `### Files Changed\n\n`;
  output += `| File | Language | Changes |\n`;
  output += `|------|----------|--------:|\n`;
  for (const file of files) {
    output += `| \`${file.filename}\` | ${file.language} | +${file.addedLines}/-${file.removedLines} |\n`;
  }
  output += '\n';
  
  // Risks
  if (allRisks.length > 0) {
    output += `### ⚠️ Identified Risks\n\n`;
    for (const risk of allRisks) {
      output += `- ${risk}\n`;
    }
    output += '\n';
  } else {
    output += `### ⚠️ Identified Risks\n\nNo significant risks detected.\n\n`;
  }
  
  // Suggestions
  if (allSuggestions.length > 0) {
    output += `### 💡 Improvement Suggestions\n\n`;
    for (const s of allSuggestions) {
      output += `- ${s}\n`;
    }
    output += '\n';
  } else {
    output += `### 💡 Improvement Suggestions\n\nNo suggestions at this time.\n\n`;
  }
  
  // Confidence
  const confidenceLabel = confidence >= 80 ? 'High' : confidence >= 50 ? 'Medium' : 'Low';
  output += `### ✅ Confidence Score\n\n**${confidence}%** — ${confidenceLabel}\n\n`;
  output += `---\n*Review generated by [claude-review](https://github.com/promptpolish-ai/claude-review)*\n`;
  
  return output;
}

/**
 * Main review function
 */
export async function reviewPR({ prUrl, diffPath } = {}) {
  let diff, repoInfo, prTitle;
  
  if (prUrl) {
    const { owner, repo, pr } = parsePRUrl(prUrl);
    repoInfo = `${owner}/${repo} #${pr}`;
    
    // Fetch diff and metadata in parallel
    const [diffResult, meta] = await Promise.all([
      fetchDiff(owner, repo, pr),
      fetchPRMetadata(owner, repo, pr).catch(() => null)
    ]);
    diff = diffResult;
    prTitle = meta?.title || '';
  } else if (diffPath) {
    diff = fs.readFileSync(diffPath, 'utf-8');
    repoInfo = `local: ${diffPath}`;
  } else {
    throw new Error('Provide either --pr <url> or --diff <path>');
  }
  
  if (!diff || diff.trim().length === 0) {
    return formatReview({
      repoInfo,
      files: [],
      allRisks: ['No diff content to analyze'],
      allSuggestions: [],
      confidence: 0
    });
  }
  
  // Parse and analyze
  const files = parseDiff(diff);
  const allRisks = [];
  const allSuggestions = [];
  
  for (const file of files) {
    const analysis = analyzeDiffBlock(file);
    allRisks.push(...analysis.risks);
    allSuggestions.push(...analysis.suggestions);
  }
  
  const confidence = calculateConfidence(files, allRisks, allSuggestions);
  
  return formatReview({
    repoInfo: prTitle ? `${repoInfo}: ${prTitle}` : repoInfo,
    files,
    allRisks: [...new Set(allRisks)],
    allSuggestions: [...new Set(allSuggestions)],
    confidence
  });
}

export { parsePRUrl, parseDiff, analyzeDiffBlock, calculateConfidence, formatReview };
