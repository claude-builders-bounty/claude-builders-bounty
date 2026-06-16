#!/usr/bin/env node
// Validate the n8n workflow JSON
const fs = require("fs");
const path = require("path");

try {
  const json = JSON.parse(
    fs.readFileSync(path.join(__dirname, "weekly-dev-summary.workflow.json"), "utf-8")
  );
  
  console.log("✅ Valid n8n workflow JSON");
  console.log(`   Name: ${json.name || "(unnamed)"}`);
  console.log(`   Nodes: ${(json.nodes || []).length}`);
  console.log(`   Connections: ${Object.keys(json.connections || {}).length}`);
  
  const required = ["cron-trigger", "config", "fetch-commits", "fetch-issues", "fetch-prs", "claude-api", "webhook"];
  const missing = required.filter(id => !json.nodes?.find(n => n.id === id));
  
  if (missing.length === 0) {
    console.log("✅ All required nodes present");
  } else {
    console.log(`⚠️ Missing nodes: ${missing.join(", ")}`);
  }
  
  process.exit(0);
} catch (e) {
  console.error("❌ Invalid workflow JSON:", e.message);
  process.exit(1);
}
