import fs from 'node:fs';

const workflowPath = new URL('./workflows/weekly-dev-summary.json', import.meta.url);
const workflow = JSON.parse(fs.readFileSync(workflowPath, 'utf8'));

const nodeNames = new Set(workflow.nodes.map(node => node.name));
const requiredNodes = [
  'Weekly Schedule',
  'Set Repository Window',
  'Fetch Weekly Commits',
  'Fetch Recent Pull Requests',
  'Fetch Updated Issues',
  'Build Summary Prompt',
  'Generate Claude Summary',
  'Format Output',
  'Send to Discord'
];

for (const name of requiredNodes) {
  if (!nodeNames.has(name)) {
    throw new Error(`Missing required node: ${name}`);
  }
}

const connectionErrors = [];
for (const [source, outputs] of Object.entries(workflow.connections || {})) {
  if (!nodeNames.has(source)) {
    connectionErrors.push(`Missing source node: ${source}`);
  }
  for (const branch of outputs.main || []) {
    for (const edge of branch) {
      if (!nodeNames.has(edge.node)) {
        connectionErrors.push(`Missing target node: ${edge.node}`);
      }
    }
  }
}

if (connectionErrors.length) {
  throw new Error(connectionErrors.join('\n'));
}

const claudeNode = workflow.nodes.find(node => node.name === 'Generate Claude Summary');
const requestBody = claudeNode?.parameters?.jsonBody || '';
if (!requestBody.includes('claude-sonnet-4-20250514')) {
  throw new Error('Claude node does not use claude-sonnet-4-20250514');
}

const configNode = workflow.nodes.find(node => node.name === 'Set Repository Window');
const configJson = JSON.stringify(configNode?.parameters || {});
for (const variable of ['GITHUB_OWNER', 'GITHUB_REPO', 'SUMMARY_LANGUAGE']) {
  if (!configJson.includes(variable)) {
    throw new Error(`Missing configurable variable: ${variable}`);
  }
}

console.log(`Workflow validation passed: ${workflow.nodes.length} nodes, ${Object.keys(workflow.connections).length} connection groups.`);


