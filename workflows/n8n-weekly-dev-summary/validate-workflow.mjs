#!/usr/bin/env node
/**
 * validate-workflow.mjs — Structural validator for the n8n Weekly GitHub Summary workflow.
 * Run: node validate-workflow.mjs
 */
import { readFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const workflow = JSON.parse(readFileSync(resolve(__dirname, 'workflow.json'), 'utf-8'));
const readme = readFileSync(resolve(__dirname, 'README.md'), 'utf-8');

let passed = 0;
let failed = 0;

function check(label, condition) {
  if (condition) { passed++; console.log(`  ✅ ${label}`); }
  else { failed++; console.log(`  ❌ ${label}`); }
}

console.log('\n🔍 Validating n8n Weekly GitHub Summary workflow...\n');

// 1. Workflow structure
check('Workflow has name', typeof workflow.name === 'string' && workflow.name.length > 0);
check('Workflow has nodes array', Array.isArray(workflow.nodes));
check('Workflow has connections object', typeof workflow.connections === 'object');

// 2. Required nodes
const nodeIds = workflow.nodes.map(n => n.id);
const nodeTypes = workflow.nodes.map(n => n.type);

check('9 nodes total', workflow.nodes.length === 9);
check('Schedule trigger node', nodeIds.includes('schedule-trigger'));
check('Set Configuration code node', nodeIds.includes('set-config'));
check('Get Commits HTTP node', nodeIds.includes('get-commits'));
check('Get Issues HTTP node', nodeIds.includes('get-issues'));
check('Get PRs HTTP node', nodeIds.includes('get-prs'));
check('Merge node', nodeIds.includes('merge-data'));
check('Format Data code node', nodeIds.includes('format-data'));
check('Claude API code node', nodeIds.includes('claude-api'));
check('Discord Webhook code node', nodeIds.includes('discord-webhook'));

// 3. Cron trigger
const trigger = workflow.nodes.find(n => n.id === 'schedule-trigger');
check('Cron expression is "0 17 * * 5" (Friday 5pm)',
  trigger?.parameters?.rule?.interval?.[0]?.expression === '0 17 * * 5');

// 4. Claude model
const allCode = workflow.nodes.filter(n => n.type === 'n8n-nodes-base.code');
const allCodeText = allCode.map(n => n.parameters.jsCode).join('\n');
check('Uses claude-sonnet-4-20250514 model', allCodeText.includes('claude-sonnet-4-20250514'));
check('Calls Anthropic API endpoint', allCodeText.includes('api.anthropic.com'));

// 5. Configurable variables
const envVars = ['GITHUB_OWNER', 'GITHUB_REPO', 'GITHUB_TOKEN', 'ANTHROPIC_API_KEY', 'DISCORD_WEBHOOK_URL', 'SUMMARY_LANGUAGE'];
for (const v of envVars) {
  check(`Configurable: ${v}`, allCodeText.includes(v));
}

// 6. Language support (EN/FR)
check('Supports EN/FR language', allCodeText.includes('SUMMARY_LANGUAGE') && allCodeText.includes('FR'));

// 7. GitHub API calls
const httpNodes = workflow.nodes.filter(n => n.type === 'n8n-nodes-base.httpRequest');
check('3 GitHub HTTP request nodes (commits, issues, PRs)', httpNodes.length === 3);
for (const hn of httpNodes) {
  check(`HTTP node "${hn.name}" has GitHub URL`, hn.parameters.url.includes('api.github.com'));
  check(`HTTP node "${hn.name}" has auth`, hn.parameters.authentication === 'genericCredentialType');
}

// 8. Discord delivery
const discordNode = workflow.nodes.find(n => n.id === 'discord-webhook');
check('Discord node sends webhook', discordNode?.parameters?.jsCode?.includes('DISCORD_WEBHOOK_URL'));

// 9. Connections
check('All nodes connected', Object.keys(workflow.connections).length === 8);
check('Schedule -> Config', workflow.connections['Weekly Friday 5pm']?.main?.[0]?.[0]?.node === 'Set Configuration');
check('Config -> 3 GitHub nodes (parallel)', workflow.connections['Set Configuration']?.main?.[0]?.length === 3);
check('Format -> Claude -> Discord chain',
  workflow.connections['Format Activity Data']?.main?.[0]?.[0]?.node === 'Generate Summary (Claude)' &&
  workflow.connections['Generate Summary (Claude)']?.main?.[0]?.[0]?.node === 'Send to Discord');

// 10. README
check('README exists', readme.length > 100);
check('README has ≤5 setup steps', (readme.match(/### Step \d/g) || []).length <= 5);
check('README mentions Discord', readme.includes('Discord'));
check('README mentions EN/FR', readme.includes('EN') && readme.includes('FR'));
check('README mentions claude-sonnet-4-20250514', readme.includes('claude-sonnet-4-20250514'));

// Summary
console.log(`\n${'═'.repeat(50)}`);
console.log(`Results: ${passed} passed, ${failed} failed`);
console.log(`${'═'.repeat(50)}\n`);

if (failed > 0) {
  process.exit(1);
} else {
  console.log('🎉 Workflow validation passed! All acceptance criteria met.\n');
  process.exit(0);
}
