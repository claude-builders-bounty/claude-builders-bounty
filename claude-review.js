#!/usr/bin/env node
const https = require('https');
const args = process.argv.slice(2);
const prIndex = args.indexOf('--pr');
if (prIndex === -1 || !args[prIndex+1]) {
  console.error('Usage: claude-review --pr https://github.com/owner/repo/pull/123');
  process.exit(1);
}
const prUrl = args[prIndex+1];
const m = prUrl.match(/github.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/);
if (!m) { console.error('Invalid PR URL'); process.exit(1); }
const [, owner, repo, num] = m;

async function get(url) {
  return new Promise((resolve, reject) => {
    https.get(url, { headers: { 'User-Agent': 'claude-review', 'Accept': 'application/vnd.github.v3.diff' } }, res => {
      let d = ''; res.on('data', c => d += c); res.on('end', () => resolve(d));
    }).on('error', reject);
  });
}

async function main() {
  const diff = await get(`https://api.github.com/repos/${owner}/${repo}/pulls/${num}`);
  const lines = diff.split('\n');
  const added = lines.filter(l => l.startsWith('+') && !l.startsWith('+++')).length;
  const removed = lines.filter(l => l.startsWith('-') && !l.startsWith('---')).length;
  const files = (diff.match(/^diff --git/g) || []).length;
  
  const risks = [];
  if (lines.some(l => l.includes('require') || l.includes('assert'))) risks.push('- Contains assertion/require statements');
  if (lines.some(l => l.includes('approve') || l.includes('transfer'))) risks.push('- Contains transfer/approval logic');
  if (lines.some(l => l.includes('admin') || l.includes('owner'))) risks.push('- Contains admin/owner functions');
  if (files > 10) risks.push('- Large number of files modified');
  
  const suggestions = [];
  if (files > 5) suggestions.push('- Consider splitting into smaller PRs');
  if (added > 200) suggestions.push('- Large addition count - verify necessity');
  if (!diff.toLowerCase().includes('test')) suggestions.push('- No test changes detected');
  
  const confidence = added + removed > 100 ? 'High' : added + removed > 20 ? 'Medium' : 'Low';
  
  console.log('## PR Review');
  console.log('');
  console.log('### Summary');
  console.log(`PR #${num} in ${owner}/${repo} modifies ${files} file(s) with +${added}/-${removed} lines.`);
  console.log('');
  console.log('### Identified Risks');
  console.log(risks.length ? risks.join('\n') : '- No significant risks identified');
  console.log('');
  console.log('### Improvement Suggestions');
  console.log(suggestions.length ? suggestions.join('\n') : '- No specific suggestions');
  console.log('');
  console.log(`### Confidence Score: ${confidence}`);
}
main().catch(e => { console.error('Error:', e.message); process.exit(1); });