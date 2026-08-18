#!/usr/bin/env node
/**
 * Git Changelog Generator for Claude Code & CI/CD
 * Extracts git history, categorizes commits, and generates structured CHANGELOG.md
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const CATEGORY_MAPPING = {
  Added: ['feat', 'feature', 'add', 'create', 'implement'],
  Fixed: ['fix', 'bug', 'patch', 'resolve', 'hotfix'],
  Changed: ['refactor', 'perf', 'change', 'update', 'modify', 'improve'],
  Removed: ['remove', 'delete', 'deprecate', 'drop'],
  Security: ['security', 'sec', 'cve', 'vuln'],
  Documentation: ['docs', 'doc']
};

function runGit(cmd, cwd = process.cwd()) {
  try {
    return execSync(`git ${cmd}`, { cwd, encoding: 'utf8', stdio: ['pipe', 'pipe', 'ignore'] }).trim();
  } catch {
    return '';
  }
}

function getLatestTag(cwd) {
  const tags = runGit('tag --sort=-creatordate', cwd);
  if (tags) return tags.split('\n')[0].trim();
  return null;
}

function getCommits(sinceTag, cwd) {
  const range = sinceTag ? `${sinceTag}..HEAD` : 'HEAD';
  const fmt = '%H%x09%h%x09%an%x09%ad%x09%s';
  const output = runGit(`log ${range} --pretty=format:"${fmt}" --date=short`, cwd);
  if (!output) return [];

  return output.split('\n').filter(Boolean).map(line => {
    const [fullHash, shortHash, author, date, ...rest] = line.split('\t');
    const subject = rest.join('\t');
    return { fullHash, shortHash, author, date, subject };
  });
}

function categorizeCommit(subject) {
  const sub = subject.trim();
  const subLower = sub.toLowerCase();

  // Conventional commit match: feat(scope): message or fix: message
  const match = sub.match(/^([a-zA-Z]+)(?:\([^\)]+\))?:\s*(.+)$/);
  const prefix = match ? match[1].toLowerCase() : null;
  const cleanMsg = match ? match[2] : sub;

  if (prefix) {
    for (const [cat, keywords] of Object.entries(CATEGORY_MAPPING)) {
      if (keywords.includes(prefix)) return { category: cat, message: cleanMsg };
    }
  }

  for (const [cat, keywords] of Object.entries(CATEGORY_MAPPING)) {
    for (const kw of keywords) {
      if (new RegExp(`\\b${kw}\\b`, 'i').test(subLower)) {
        return { category: cat, message: sub };
      }
    }
  }

  return { category: 'Changed', message: sub };
}

function buildChangelog(version = 'Unreleased', sinceTag = null, cwd = process.cwd()) {
  const commits = getCommits(sinceTag, cwd);
  const today = new Date().toISOString().split('T')[0];

  const sections = {
    Added: [],
    Fixed: [],
    Changed: [],
    Removed: [],
    Security: [],
    Documentation: []
  };

  commits.forEach(c => {
    const { category, message } = categorizeCommit(c.subject);
    if (!sections[category]) sections[category] = [];
    sections[category].push({
      message,
      hash: c.shortHash,
      author: c.author
    });
  });

  const lines = [
    `## [${version}] - ${today}`,
    ''
  ];

  if (sinceTag) {
    lines.push(`> Changes since \`${sinceTag}\` (${commits.length} commits)`);
  } else {
    lines.push(`> Initial changelog release (${commits.length} commits)`);
  }
  lines.push('');

  if (commits.length === 0) {
    lines.push('_No commits found in this range._');
    lines.push('');
    return lines.join('\n');
  }

  for (const [cat, items] of Object.entries(sections)) {
    if (items.length > 0) {
      lines.push(`### ${cat}`);
      items.forEach(item => {
        lines.push(`- ${item.message} (\`${item.hash}\`) - @${item.author}`);
      });
      lines.push('');
    }
  }

  return lines.join('\n');
}

function main() {
  const args = process.argv.slice(2);
  let version = 'Unreleased';
  let since = null;
  let output = 'CHANGELOG.md';
  let stdout = false;
  let prepend = false;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--version' && args[i + 1]) version = args[++i];
    else if (args[i] === '--since' && args[i + 1]) since = args[++i];
    else if (args[i] === '--output' && args[i + 1]) output = args[++i];
    else if (args[i] === '--stdout') stdout = true;
    else if (args[i] === '--prepend') prepend = true;
  }

  const sinceTag = since || getLatestTag();
  const content = buildChangelog(version, sinceTag);

  if (stdout) {
    console.log(content);
    return;
  }

  let finalDoc = `# Changelog\n\nAll notable changes to this project will be documented in this file.\n\nThe format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).\n\n${content}`;

  if (prepend && fs.existsSync(output)) {
    const existing = fs.readFileSync(output, 'utf8');
    const stripped = existing.replace(/^# Changelog[^\n]*\n+/i, '');
    finalDoc = `# Changelog\n\nAll notable changes to this project will be documented in this file.\n\nThe format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).\n\n${content}\n\n${stripped}`;
  }

  fs.writeFileSync(output, finalDoc, 'utf8');
  console.log(`✅ Generated changelog written to ${output}`);
}

if (require.main === module) {
  main();
}

module.exports = { categorizeCommit, buildChangelog, getLatestTag, getCommits };
