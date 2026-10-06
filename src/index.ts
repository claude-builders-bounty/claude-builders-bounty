import { Claimer } from "./claimer";
import { loadConfig } from "./config";

async function main() {
  console.log("🏆 Claude Builders Bounty - Automated Claim System");
  console.log("=" .repeat(50));

  try {
    const config = loadConfig();
    const claimer = new Claimer(config);

    // Check if specific issue number is provided
    const issueNumber = process.argv[2] ? parseInt(process.argv[2], 10) : null;

    if (issueNumber) {
      console.log(`Processing specific issue #${issueNumber}...`);
      await claimer.processIssue(issueNumber);
    } else {
      console.log("Running cron job to process all open issues...");
      await claimer.runCron();
    }

    console.log("\n✅ Processing complete!");
  } catch (error) {
    console.error("\n❌ Fatal error:", error);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

export { Claimer } from "./claimer";
export { loadConfig } from "./config";
