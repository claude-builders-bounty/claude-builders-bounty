const fs = require('fs');
const path = require('path');
const vm = require('vm');

console.log('🧪 Running n8n Workflow Validation & Verification Suite...\n');

let passCount = 0;
let failCount = 0;

function assert(condition, message) {
  if (condition) {
    console.log(`  ✅ PASS: ${message}`);
    passCount++;
  } else {
    console.error(`  ❌ FAIL: ${message}`);
    failCount++;
  }
}

const workflowPath = path.join(__dirname, '..', 'n8n-claude-weekly-dev-summary.json');

// Test 1: File Existence & JSON Parsing
assert(fs.existsSync(workflowPath), 'Workflow JSON file exists on disk');
let workflow;
try {
  workflow = JSON.parse(fs.readFileSync(workflowPath, 'utf8'));
  assert(true, 'Workflow JSON parses successfully');
} catch (e) {
  assert(false, `Workflow JSON parsing failed: ${e.message}`);
  process.exit(1);
}

// Test 2: Workflow Core Schema
assert(Array.isArray(workflow.nodes) && workflow.nodes.length > 0, `Workflow contains ${workflow.nodes.length} nodes`);
assert(typeof workflow.connections === 'object' && workflow.connections !== null, 'Workflow connections object is valid');
assert(workflow.settings?.executionOrder === 'v1', 'Workflow execution order set to v1');

// Test 3: Node Uniqueness & Connection Integrity
const nodeNames = new Set(workflow.nodes.map(n => n.name));
const nodeIds = new Set(workflow.nodes.map(n => n.id));
assert(nodeNames.size === workflow.nodes.length, 'All node names are distinct and unique');
assert(nodeIds.size === workflow.nodes.length, 'All node IDs are distinct and unique');

let brokenLinks = 0;
for (const [sourceName, conns] of Object.entries(workflow.connections)) {
  if (!nodeNames.has(sourceName)) {
    console.error(`Broken connection source: ${sourceName}`);
    brokenLinks++;
  }
  for (const group of (conns.main || [])) {
    for (const link of group) {
      if (!nodeNames.has(link.node)) {
        console.error(`Broken connection target: ${link.node} from ${sourceName}`);
        brokenLinks++;
      }
    }
  }
}
assert(brokenLinks === 0, 'All node connections point to valid, existing nodes with 0 broken links');

// Test 4: Acceptance Criteria - Weekly Cron Trigger (Friday 5pm)
const scheduleNode = workflow.nodes.find(n => n.type === 'n8n-nodes-base.scheduleTrigger');
assert(Boolean(scheduleNode), 'Schedule Trigger node exists');
const cronExpr = scheduleNode?.parameters?.rule?.interval?.[0]?.expression;
assert(cronExpr === '0 17 * * 5', `Cron trigger expression matches Friday at 5pm ("0 17 * * 5"): ${cronExpr}`);

// Test 5: Manual Trigger for Instant Testing
const manualNode = workflow.nodes.find(n => n.type === 'n8n-nodes-base.manualTrigger');
assert(Boolean(manualNode), 'Manual Trigger node exists for on-demand & testing execution');

// Test 6: GitHub API Integration (Commits, Issues, PRs)
const commitsNode = workflow.nodes.find(n => n.name === 'GitHub Commits');
assert(Boolean(commitsNode) && commitsNode.parameters.url.includes('/commits'), 'GitHub Commits HTTP Request node correctly configured');

const issuesNode = workflow.nodes.find(n => n.name === 'GitHub Issues');
assert(Boolean(issuesNode) && issuesNode.parameters.url.includes('/issues'), 'GitHub Issues HTTP Request node correctly configured');

const prsNode = workflow.nodes.find(n => n.name === 'GitHub Merged PRs');
assert(Boolean(prsNode) && prsNode.parameters.url.includes('/pulls'), 'GitHub Merged PRs HTTP Request node correctly configured');

// Test 7: Claude API Integration (claude-sonnet-4-20250514)
const claudeNode = workflow.nodes.find(n => n.name === 'Claude Sonnet 4 Summary');
assert(Boolean(claudeNode), 'Claude API HTTP Request node exists');
assert(claudeNode.parameters.url === 'https://api.anthropic.com/v1/messages', 'Calls Anthropic Messages API endpoint');
assert(claudeNode.parameters.jsonBody.includes('claude-sonnet-4-20250514'), 'Default model matches issue requirement: claude-sonnet-4-20250514');

// Test 8: Multi-channel Delivery (Discord & Slack Webhooks)
const discordNode = workflow.nodes.find(n => n.name === 'Send Discord Webhook');
assert(Boolean(discordNode), 'Send Discord Webhook node exists');

const slackNode = workflow.nodes.find(n => n.name === 'Send Slack Webhook');
assert(Boolean(slackNode), 'Send Slack Webhook node exists');

// Test 9: JavaScript Syntax Compilation Check on Code Nodes
for (const node of workflow.nodes) {
  if (node.type === 'n8n-nodes-base.code' && node.parameters?.jsCode) {
    try {
      new vm.Script(`(function() {\n${node.parameters.jsCode}\n})`);
      assert(true, `Code node "${node.name}" compiles without syntax errors`);
    } catch (e) {
      assert(false, `Code node "${node.name}" syntax error: ${e.message}`);
    }
  }
}

// Test 10: Payload Formatting & Truncation Simulation
const formatNode = workflow.nodes.find(n => n.name === 'Format Payload');
const testContext = {
  $input: {
    first: () => ({
      json: {
        content: [{ text: '🌟 This is a synthesized weekly dev summary.\n\nGreat progress was made on features and bugs!' }]
      }
    })
  },
  $: (nodeName) => ({
    first: () => ({
      json: {
        repoFullName: 'facebook/react',
        language: 'EN',
        sinceFormatted: 'Mar 21, 2026',
        untilFormatted: 'Mar 28, 2026',
        claudeModel: 'claude-sonnet-4-20250514',
        deliveryChannel: 'both',
        discordWebhookUrl: 'https://discord.com/api/webhooks/mock',
        slackWebhookUrl: 'https://hooks.slack.com/services/mock',
        stats: { totalCommits: 25, totalClosedIssues: 12, totalMergedPRs: 8 }
      }
    })
  }),
  Boolean: Boolean,
  String: String,
  Array: Array,
  Date: Date,
  JSON: JSON
};

const sandbox = vm.createContext(testContext);
let result;
try {
  const script = new vm.Script(`(function() {\n${formatNode.parameters.jsCode}\n})()`);
  result = script.runInContext(sandbox);
  assert(Array.isArray(result) && result[0]?.json?.discordPayload?.embeds?.length > 0, 'Format Payload generates valid Discord Embed payload');
  assert(Array.isArray(result) && result[0]?.json?.slackPayload?.blocks?.length > 0, 'Format Payload generates valid Slack Block Kit payload');
  assert(result[0]?.json?.discordActive === true, 'Discord active flag correctly set');
  assert(result[0]?.json?.slackActive === true, 'Slack active flag correctly set');
} catch (e) {
  assert(false, `Format Payload execution failed: ${e.message}`);
}

console.log(`\n========================================`);
console.log(`Summary: ${passCount} Passed, ${failCount} Failed`);
console.log(`========================================\n`);

if (failCount > 0) {
  process.exit(1);
}
