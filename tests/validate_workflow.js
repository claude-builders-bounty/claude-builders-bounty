const fs = require('fs');
const path = require('path');

function validateWorkflow(filePath) {
  console.log(`Checking workflow file: ${filePath}`);
  const raw = fs.readFileSync(filePath, 'utf-8');
  const workflow = JSON.parse(raw);

  if (!workflow.name) throw new Error("Workflow missing name");
  if (!Array.isArray(workflow.nodes)) throw new Error("Workflow nodes is not an array");
  if (!workflow.connections || typeof workflow.connections !== 'object') throw new Error("Workflow connections missing");

  const nodeMap = new Map();
  for (const node of workflow.nodes) {
    if (!node.id || !node.name || !node.type) {
      throw new Error(`Node missing required property: ${JSON.stringify(node)}`);
    }
    nodeMap.set(node.name, node);
  }

  // Validate connections
  for (const [sourceNode, connectionObj] of Object.entries(workflow.connections)) {
    if (!nodeMap.has(sourceNode)) {
      throw new Error(`Connection references unknown source node: ${sourceNode}`);
    }
    for (const [outputType, connectionGroups] of Object.entries(connectionObj)) {
      for (const group of connectionGroups) {
        for (const conn of group) {
          if (!nodeMap.has(conn.node)) {
            throw new Error(`Connection from ${sourceNode} references unknown target node: ${conn.node}`);
          }
        }
      }
    }
  }

  console.log(`✓ Validated ${workflow.nodes.length} nodes and graph links in ${filePath}`);
}

const targetFiles = [
  'workflows/weekly-summary/weekly_dev_summary.json',
  'workflows/weekly-summary/workflow.json',
  'weekly_dev_summary.json'
];

targetFiles.forEach(file => {
  const resolved = path.resolve(process.cwd(), file);
  if (fs.existsSync(resolved)) {
    validateWorkflow(resolved);
  }
});
console.log('Node.js n8n JSON schema validation completed successfully.');
