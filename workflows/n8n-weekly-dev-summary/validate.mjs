#!/usr/bin/env node
/**
 * Validate the n8n weekly dev summary workflow.
 * Usage: node validate.mjs
 * Exits 0 on success, 1 on failure.
 */
import { readFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const workflowPath = resolve(__dirname, 'weekly-dev-summary.json');

let errors = [];

function check(condition, msg) {
  if (!condition) errors.push(msg);
}

try {
  const raw = readFileSync(workflowPath, 'utf-8');
  const wf = JSON.parse(raw);

  // Structural checks
  check(wf.name, 'Workflow must have a name');
  check(Array.isArray(wf.nodes), 'Workflow must have nodes array');
  check(wf.nodes.length >= 8, `Expected >= 8 nodes, got ${wf.nodes.length}`);
  check(typeof wf.connections === 'object', 'Workflow must have connections object');

  // Check for required node types
  const nodeNames = wf.nodes.map(n => n.name);
  const nodeTypes = wf.nodes.map(n => n.type);

  check(nodeNames.some(n => n.includes('Schedule')), 'Missing Schedule Trigger node');
  check(nodeNames.some(n => n.includes('Manual')), 'Missing Manual Trigger node');
  check(nodeTypes.includes('n8n-nodes-base.httpRequest'), 'Missing HTTP Request nodes');
  check(nodeTypes.includes('n8n-nodes-base.code'), 'Missing Code nodes');
  check(nodeNames.some(n => n.includes('Claude')), 'Missing Claude API node');
  check(nodeNames.some(n => n.includes('Merge') || n.includes('merge')), 'Missing Merge node');
  check(nodeNames.some(n => n.includes('Config')), 'Missing Set Config node');

  // Check Claude model in any node's jsonBody
  const hasSonnet = wf.nodes.some(n => {
    const body = JSON.stringify(n.parameters || '');
    return body.includes('claude-sonnet-4');
  });
  check(hasSonnet, 'Claude model must be claude-sonnet-4-20250514 in a node');

  // Check cron schedule
  const scheduleNode = wf.nodes.find(n => n.name.includes('Schedule'));
  if (scheduleNode) {
    const expr = scheduleNode.parameters?.rule?.interval?.[0]?.expression || '';
    check(expr === '0 17 * * 5', `Schedule should be Friday 5pm, got: ${expr}`);
  }

  // Verify all connections refer to existing nodes
  const connNames = new Set(Object.keys(wf.connections));
  const allNodeNames = new Set(nodeNames);
  for (const [srcNode, conns] of Object.entries(wf.connections)) {
    check(allNodeNames.has(srcNode), `Connection source "${srcNode}" not found in nodes`);
    for (const outputArr of conns.main || []) {
      for (const conn of outputArr || []) {
        check(allNodeNames.has(conn.node), `Connection target "${conn.node}" not found in nodes`);
      }
    }
  }

  console.log(`\n  ✅ ${errors.length === 0 ? `All checks passed (${wf.nodes.length} nodes, ${Object.keys(wf.connections).length} connections)` : `${errors.length} check(s) failed`}\n`);

} catch (e) {
  errors.push(`Failed to load workflow: ${e.message}`);
}

if (errors.length > 0) {
  console.error('\n  ❌ Validation errors:');
  errors.forEach(e => console.error(`     • ${e}`));
  console.error();
  process.exit(1);
} else {
  process.exit(0);
}
