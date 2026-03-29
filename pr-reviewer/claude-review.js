#!/usr/bin/env node
/**
 * claude-review - CLI tool to review GitHub PRs and produce structured Markdown output
 * 
 * Usage: claude-review --pr https://github.com/owner/repo/pull/123
 *        claude-review --pr owner/repo/123
 *        claude-review --pr 123 (when in a git repo)
 */

const { execSync } = require('child_process');
const path = require('path');

function run(cmd) {
  try {
    return execSync(cmd, { encoding: 'utf-8', maxBuffer: 50 * 1024 * 1024 });
  } catch (e) {
    console.error(`Error running: ${cmd}`);
    console.error(e.message);
    process.exit(1);
  }
}

function parsePRUrl(prArg) {
  // Handle full URLs
  const urlMatch = prArg.match(/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/);
  if (urlMatch) {
    return { owner: urlMatch[1], repo: urlMatch[2], prNumber: urlMatch[3] };
  }
  
  // Handle owner/repo/N format
  const shortMatch = prArg.match(/^([^/]+)\/([^/]+)\/(\d+)$/);
  if (shortMatch) {
    return { owner: shortMatch[1], repo: shortMatch[2], prNumber: shortMatch[3] };
  }
  
  // Handle just PR number - try to get from git remote
  if (/^\d+$/.test(prArg)) {
    try {
      const remoteUrl = execSync('git remote get-url origin', { encoding: 'utf-8' }).trim();
      const repoMatch = remoteUrl.match(/github\.com[:/]([^/]+)\/([^/.]+)/);
      if (repoMatch) {
        return { owner: repoMatch[1], repo: repoMatch[2], prNumber: prArg };
      }
    } catch (e) {}
    console.error('Could not determine repo from git remote. Use full URL format.');
    process.exit(1);
  }
  
  console.error('Invalid PR format. Use: claude-review --pr https://github.com/owner/repo/pull/123');
  process.exit(1);
}

function analyzeDiff(diff) {
  const analysis = {
    filesChanged: 0,
    additions: 0,
    deletions: 0,
    languages: [],
    risks: [],
    suggestions: [],
    hasTests: false,
    hasDocs: false,
    breakingChanges: false,
    securityIssues: [],
    commonIssues: []
  };
  
  const lines = diff.split('\n');
  let currentFile = null;
  let fileExtensions = new Set();
  
  for (const line of lines) {
    // New file
    const fileMatch = line.match(/^\+\+\+ b\/(.+)$/);
    if (fileMatch) {
      if (currentFile) {
        analysis.filesChanged++;
        const ext = path.extname(currentFile).toLowerCase();
        if (ext) fileExtensions.add(ext);
      }
      currentFile = fileMatch[1];
      continue;
    }
    
    // Additions
    if (line.startsWith('+') && !line.startsWith('+++')) {
      analysis.additions++;
    }
    // Deletions
    if (line.startsWith('-') && !line.startsWith('---')) {
      analysis.deletions++;
    }
    
    if (!currentFile) continue;
    
    const cleanLine = line.substring(1);
    
    // Check for test files
    if (/test|spec|\.test\.|\.spec\./.test(currentFile)) {
      analysis.hasTests = true;
    }
    
    // Check for documentation
    if (/README|CHANGELOG|CONTRIBUTING|LICENSE|\.md$/.test(currentFile)) {
      analysis.hasDocs = true;
    }
    
    // Security patterns
    if (/password|secret|token|api_key|apikey|private_key/.test(cleanLine) && 
        !/^import|^const|^let|^var|^export|^function/.test(cleanLine)) {
      analysis.securityIssues.push(`Potential hardcoded secret detected: ${cleanLine.trim().substring(0, 60)}`);
    }
    
    // SQL injection risk
    if (/\$\{|template.*\}|concat\(|join\(.*\$\{/.test(cleanLine) && 
        /query|select|insert|update|delete|sql/i.test(cleanLine)) {
      analysis.securityIssues.push(`Potential SQL injection risk on line: ${cleanLine.trim().substring(0, 60)}`);
    }
    
    // TODO/FIXME
    if (/TODO|FIXME|HACK|XXX|BUG/.test(cleanLine)) {
      analysis.commonIssues.push(`Unresolved marker found: ${cleanLine.trim().substring(0, 60)}`);
    }
    
    // Console.log in non-test code
    if (/console\.(log|debug|info|warn|error)/.test(cleanLine) && 
        !/test|spec/.test(currentFile) &&
        !/^\s*\/\//.test(cleanLine)) {
      analysis.commonIssues.push(`Debug statement left in code: ${cleanLine.trim().substring(0, 60)}`);
    }
    
    // Breaking change indicators
    if (/major|breaking|destroy|migrate.*drop|drop.*column/.test(cleanLine.toLowerCase())) {
      analysis.breakingChanges = true;
    }
  }
  
  if (currentFile) {
    analysis.filesChanged++;
    const ext = path.extname(currentFile).toLowerCase();
    if (ext) fileExtensions.add(ext);
  }
  
  // Map extensions to language names
  const langMap = {
    '.js': 'JavaScript', '.jsx': 'JavaScript', '.ts': 'TypeScript', '.tsx': 'TypeScript',
    '.py': 'Python', '.rb': 'Ruby', '.go': 'Go', '.rs': 'Rust', '.java': 'Java',
    '.cpp': 'C++', '.c': 'C', '.cs': 'C#', '.php': 'PHP', '.swift': 'Swift',
    '.kt': 'Kotlin', '.scala': 'Scala', '.sh': 'Shell', '.bash': 'Bash',
    '.yaml': 'YAML', '.yml': 'YAML', '.json': 'JSON', '.xml': 'XML',
    '.html': 'HTML', '.css': 'CSS', '.scss': 'SCSS', '.md': 'Markdown'
  };
  
  for (const ext of fileExtensions) {
    if (langMap[ext]) analysis.languages.push(langMap[ext]);
  }
  
  // Generate risks
  if (analysis.securityIssues.length > 0) {
    analysis.risks.push(`Security: ${analysis.securityIssues.length} potential security issue(s) detected`);
  }
  if (analysis.breakingChanges) {
    analysis.risks.push('Breaking: Potential breaking change detected - verify backward compatibility');
  }
  if (analysis.additions > 1000) {
    analysis.risks.push('Size: Large PR with >1000 lines added - consider splitting into smaller PRs');
  }
  if (!analysis.hasTests && analysis.filesChanged > 3) {
    analysis.risks.push('Testing: No test files detected - consider adding tests');
  }
  
  // Generate suggestions
  if (!analysis.hasTests && analysis.filesChanged > 1) {
    analysis.suggestions.push('Add test files to improve code coverage');
  }
  if (!analysis.hasDocs && analysis.filesChanged > 5) {
    analysis.suggestions.push('Consider adding or updating documentation for complex changes');
  }
  if (analysis.commonIssues.some(i => i.includes('console.'))) {
    analysis.suggestions.push('Remove debug console statements before merging');
  }
  if (analysis.commonIssues.some(i => i.includes('TODO') || i.includes('FIXME'))) {
    analysis.suggestions.push('Address TODO/FIXME comments or create follow-up issues');
  }
  if (analysis.additions > 500) {
    analysis.suggestions.push('Consider breaking this PR into smaller, focused changes');
  }
  
  if (analysis.risks.length === 0) {
    analysis.risks.push('None identified');
  }
  if (analysis.suggestions.length === 0) {
    analysis.suggestions.push('No major suggestions - PR looks good');
  }
  
  return analysis;
}

function calculateConfidence(analysis) {
  const factors = {
    positive: 0,
    negative: 0
  };
  
  if (analysis.hasTests) factors.positive += 2;
  if (analysis.hasDocs) factors.positive += 1;
  if (analysis.securityIssues.length === 0) factors.positive += 2;
  if (analysis.filesChanged <= 10) factors.positive += 1;
  if (analysis.additions < 500) factors.positive += 1;
  
  if (analysis.securityIssues.length > 0) factors.negative += 3;
  if (analysis.breakingChanges) factors.negative += 2;
  if (!analysis.hasTests && analysis.filesChanged > 3) factors.negative += 2;
  if (analysis.additions > 1000) factors.negative += 2;
  
  const score = factors.positive - factors.negative;
  
  if (score >= 4) return 'High';
  if (score >= 1) return 'Medium';
  return 'Low';
}

function generateReview(prInfo, diff, analysis) {
  const confidence = calculateConfidence(analysis);
  
  const review = `# 📋 PR Review: #${prInfo.number} - ${prInfo.title}

## Summary
${prInfo.body || 'No description provided.'} This PR modifies **${analysis.filesChanged} file(s)** across ${analysis.languages.join(', ') || 'various languages'}, with **+${analysis.additions} additions** and **-${analysis.deletions} deletions**.

## 🔍 Identified Risks
${analysis.risks.map(r => `- ${r}`).join('\n')}

## 💡 Improvement Suggestions
${analysis.suggestions.map(s => `- ${s}`).join('\n')}

## 📊 Review Metadata
| Metric | Value |
|--------|-------|
| Confidence Score | **${confidence}** |
| Files Changed | ${analysis.filesChanged} |
| Lines Added | +${analysis.additions} |
| Lines Deleted | -${analysis.deletions} |
| Languages | ${analysis.languages.join(', ') || 'N/A'} |
| Has Tests | ${analysis.hasTests ? '✅ Yes' : '❌ No'} |
| Has Docs | ${analysis.hasDocs ? '✅ Yes' : '❌ No'} |

---
*Generated by claude-review CLI*`;
  
  return review;
}

function main() {
  const args = process.argv.slice(2);
  
  if (args.length < 2 || args[0] !== '--pr') {
    console.error('Usage: claude-review --pr <pr-url>');
    console.error('Example: claude-review --pr https://github.com/owner/repo/pull/123');
    process.exit(1);
  }
  
  const prArg = args[1];
  const { owner, repo, prNumber } = parsePRUrl(prArg);
  
  console.error(`Reviewing PR #${prNumber} from ${owner}/${repo}...`);
  
  // Fetch PR info
  const prInfoRaw = run(`gh pr view ${prNumber} --repo ${owner}/${repo} --json number,title,body,state,author,additions,deletions,changedFiles,url`);
  const prInfo = JSON.parse(prInfoRaw);
  
  // Fetch diff
  const diff = run(`gh pr diff ${prNumber} --repo ${owner}/${repo}`);
  
  // Analyze
  const analysis = analyzeDiff(diff);
  
  // Generate review
  const review = generateReview(prInfo, diff, analysis);
  
  console.log(review);
}

main();
