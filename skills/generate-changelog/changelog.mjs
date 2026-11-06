#!/usr/bin/env node
/**
 * changelog.mjs — Cross-platform zero-dependency Git Changelog Generator
 * Categorizes commits since the latest git tag into Added, Fixed, Changed, Removed, Security.
 */
import { execFileSync } from 'node:child_process';
import { writeFileSync } from 'node:fs';

function parseArgs(argv) {
  const opts = { output: 'CHANGELOG.md', version: 'Unreleased', since: '', repo: process.cwd() };
  for (let i = 2; i < argv.length; i++) {
    const arg = argv[i];
    if ((arg === '-o' || arg === '--output') && argv[i + 1]) opts.output = argv[++i];
    else if ((arg === '-v' || arg === '--version') && argv[i + 1]) opts.version = argv[++i];
    else if ((arg === '-s' || arg === '--since') && argv[i + 1]) opts.since = argv[++i];
    else if ((arg === '-r' || arg === '--repo') && argv[i + 1]) opts.repo = argv[++i];
  }
  return opts;
}

export function categorizeCommit(subject) {
  const lower = subject.trim().toLowerCase();
  if (/^(sec|security|vuln)(\([^)]+\))?!?:/.test(lower) || lower.includes('security') || lower.includes('cve-')) {
    return 'Security';
  }
  if (/^(feat|add|new)(\([^)]+\))?!?:/.test(lower) || /^(add|new|implement|introduce)\b/.test(lower)) {
    return 'Added';
  }
  if (/^(fix|bug|hotfix|patch)(\([^)]+\))?!?:/.test(lower) || /^(fix|resolve|patch|correct)\b/.test(lower)) {
    return 'Fixed';
  }
  if (/^(remove|delete|drop|deprecate)(\([^)]+\))?!?:/.test(lower) || /^(remove|delete|drop|deprecate)\b/.test(lower)) {
    return 'Removed';
  }
  return 'Changed';
}

export function stripPrefix(subject) {
  return subject.trim().replace(/^[a-zA-Z]+(\([^)]+\))?!?:\s*/, '');
}

export function generateChangelog({ repo = process.cwd(), version = 'Unreleased', since = '' } = {}) {
  let latestTag = since;
  if (!latestTag) {
    try {
      latestTag = execFileSync('git', ['describe', '--tags', '--abbrev=0'], {
        cwd: repo,
        stdio: ['ignore', 'pipe', 'ignore'],
      })
        .toString()
        .trim();
    } catch {
      latestTag = '';
    }
  }

  const range = latestTag ? `${latestTag}..HEAD` : 'HEAD';
  const rangeDesc = latestTag ? `Changes since \`${latestTag}\`` : 'All commits in repository';

  const rawLog = execFileSync(
    'git',
    ['log', range, '--no-merges', '--pretty=format:%h|%s|%an'],
    { cwd: repo }
  )
    .toString()
    .trim();

  const groups = {
    Added: [],
    Fixed: [],
    Changed: [],
    Removed: [],
    Security: [],
  };

  if (rawLog) {
    for (const line of rawLog.split(/\r?\n/)) {
      if (!line.trim()) continue;
      const [hash, subject, author] = line.split('|');
      const category = categorizeCommit(subject);
      const clean = stripPrefix(subject);
      groups[category].push(`- ${clean} (\`${hash}\` by @${author})`);
    }
  }

  const dateStr = new Date().toISOString().slice(0, 10);
  const lines = [
    '# Changelog',
    '',
    'All notable changes to this project are documented in this file.',
    `Generated automatically from git history (${rangeDesc}).`,
    '',
    `## [${version}] - ${dateStr}`,
    '',
  ];

  for (const section of ['Added', 'Fixed', 'Changed', 'Removed', 'Security']) {
    if (groups[section].length > 0) {
      lines.push(`### ${section}`);
      lines.push(...groups[section]);
      lines.push('');
    }
  }

  return lines.join('\n');
}

if (import.meta.url === `file://${process.argv[1].replace(/\\/g, '/')}` || process.argv[1]?.endsWith('changelog.mjs')) {
  const opts = parseArgs(process.argv);
  const markdown = generateChangelog(opts);
  writeFileSync(opts.output, markdown, 'utf8');
  console.log(`Successfully wrote ${opts.output}`);
}
