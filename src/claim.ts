#!/usr/bin/env node
import { Claimer } from "./claimer";
import { loadConfig } from "./config";

async function main() {
  const config = loadConfig();
  const claimer = new Claimer(config);

  const issueNumber = process.argv[2];
  
  if (!issueNumber) {
    console.error("Usage: npm run claim <issue-number>");
    process.exit(1);
  }

  const parsedNumber = parseInt(issueNumber, 10);
  if (isNaN(parsedNumber)) {
    console.error("Issue number must be a valid integer");
    process.exit(1);
  }

  await claimer.processIssue(parsedNumber);
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
