import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const workflowPath = join(process.cwd(), 'workflows', 'n8n-weekly-dev-summary.json');
const workflow = JSON.parse(readFileSync(workflowPath, 'utf8'));

const requiredNodes = [
  'Manual Test Trigger',
  'Weekly Friday 5pm',
  'Collect Activity and Ask Claude',
  'Send Discord Summary'
];

for (const nodeName of requiredNodes) {
  if (!workflow.nodes.some((node) => node.name === nodeName)) {
    throw new Error(`Missing workflow node: ${nodeName}`);
  }
}

const codeNode = workflow.nodes.find((node) => node.name === 'Collect Activity and Ask Claude');
const code = codeNode.parameters.jsCode;

for (const requiredText of [
  'claude-sonnet-4-20250514',
  'GITHUB_REPO',
  'SUMMARY_LANGUAGE',
  'ANTHROPIC_API_KEY',
  '/commits?',
  '/issues?',
  '/pulls?'
]) {
  if (!code.includes(requiredText)) {
    throw new Error(`Workflow code does not include ${requiredText}`);
  }
}

const discordNode = workflow.nodes.find((node) => node.name === 'Send Discord Summary');
if (!discordNode.parameters.url.includes('DISCORD_WEBHOOK_URL')) {
  throw new Error('Discord node must read DISCORD_WEBHOOK_URL from the environment');
}

console.log('n8n workflow structure looks valid');
