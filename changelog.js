#!/usr/bin/env node
// changelog.js — generate structured CHANGELOG.md from git history
// Usage: node changelog.js [repoPath] [--stdout]
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
const wantStdout = args.includes('--stdout');
const repoRoot = path.resolve(args.find(a => !a.startsWith('--')) || '.');
process.chdir(repoRoot);

function git(args) {
  try {
    return execSync('git ' + args.join(' '), { encoding: 'utf8', stdio: ['pipe', 'pipe', 'ignore'] }).trim();
  } catch {
    return '';
  }
}

if (!git(['rev-parse', '--git-dir'])) {
  console.error('error: not inside a git repository: ' + repoRoot);
  process.exit(1);
}

let range = 'HEAD';
const lastTag = git(['describe', '--tags', '--abbrev=0']);
if (lastTag) range = lastTag + '..HEAD';

const raw = git(['log', range, '--no-merges', '--pretty=format:%s']);
const lines = raw.split('\n').map(l => l.trim()).filter(Boolean);

const buckets = { Added: [], Fixed: [], Changed: [], Removed: [] };
const addedRe = /^(feat|add|new|create|implement|introduce|support)(\(!)|^(feat|add|new|create|implement|introduce|support)(\(.+\))?:/i;
const fixedRe = /^(fix|bug|patch|correct|repair|hotfix|resolve)(\(!)|^(fix|bug|patch|correct|repair|hotfix|resolve)(\(.+\))?:/i;
const removedRe = /^(remove|delete|drop|retire|deprecate)(\(!)|^(remove|delete|drop|retire|deprecate)(\(.+\))?:/i;

for (const line of lines) {
  const low = line.toLowerCase();
  if (addedRe.test(low)) buckets.Added.push(line);
  else if (fixedRe.test(low)) buckets.Fixed.push(line);
  else if (removedRe.test(low)) buckets.Removed.push(line);
  else buckets.Changed.push(line);
}

const out = [
  '# Changelog',
  '',
  'Generated from git log ' + range + ' on ' + new Date().toISOString(),
  '',
  '## [Unreleased]',
  '',
];

for (const section of ['Added', 'Changed', 'Fixed', 'Removed']) {
  out.push('### ' + section);
  if (buckets[section].length) {
    for (const c of buckets[section]) out.push('- ' + c);
  } else {
    out.push('- (none)');
  }
  out.push('');
}

const body = out.join('\n').trimEnd() + '\n';
if (wantStdout) {
  process.stdout.write(body);
} else {
  fs.writeFileSync(path.join(process.cwd(), 'CHANGELOG.md'), body);
  console.log('Wrote ' + path.join(process.cwd(), 'CHANGELOG.md'));
}
