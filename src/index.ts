import { fetchPRDiff, postPRComment } from "./github";
import { analyzeWithClaude } from "./claude";
import { analyzeWithTemplate } from "./template";
import { formatReviewMarkdown, formatConsoleSummary } from "./formatter";
import { ReviewOptions } from "./types";
import { writeFileSync, mkdirSync } from "fs";
import { dirname, resolve } from "path";

function parseArgs(args: string[]): ReviewOptions {
  let prUrl: string | undefined;
  let output: string | undefined;
  let post = false;
  let model: string | undefined;

  let i = 0;
  while (i < args.length) {
    const arg = args[i];
    switch (arg) {
      case "--pr":
        prUrl = args[++i];
        break;
      case "--output":
      case "-o":
        output = args[++i];
        break;
      case "--post":
        post = true;
        break;
      case "--model":
        model = args[++i];
        break;
      case "--help":
      case "-h":
        printHelp();
        process.exit(0);
      case "--version":
      case "-v":
        console.log("claude-pr-reviewer v1.0.0");
        process.exit(0);
      default:
        if (!prUrl) {
          prUrl = arg;
        }
    }
    i++;
  }

  if (!prUrl) {
    console.error("❌ Error: --pr URL is required");
    console.error("Run with --help for usage");
    process.exit(1);
  }

  return { prUrl, output, post, model };
}

function printHelp(): void {
  console.log(`
🔍 Claude PR Reviewer — Structured code review for GitHub PRs

USAGE:
  claude-review --pr <URL> [options]

OPTIONS:
  --pr <URL>        GitHub PR URL (required)
  --output, -o <f>  Save review to file
  --post            Post review as PR comment (requires GH_TOKEN)
  --model <name>    Anthropic model (default: claude-sonnet-4-20250514)
  --help, -h        Show this help
  --version, -v     Show version

ENVIRONMENT:
  GH_TOKEN          GitHub token for API access and posting comments
  ANTHROPIC_API_KEY Claude API key for AI-powered review (optional)

EXAMPLES:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
  claude-review --pr https://github.com/owner/repo/pull/123 --post
  claude-review --pr https://github.com/owner/repo/pull/123 --model claude-3-5-sonnet-20241022

MODES:
  • With ANTHROPIC_API_KEY: AI-powered review using Claude
  • Without: Template-based review with pattern detection
`);
}

async function main(): Promise<void> {
  const options = parseArgs(process.argv.slice(2));

  try {
    // Step 1: Fetch PR diff
    console.log(`📥 Fetching PR: ${options.prUrl}...`);
    const diff = await fetchPRDiff(options.prUrl);
    console.log(formatConsoleSummary(diff));
    console.log(`Diff size: ${diff.diffSizeKB} KB\n`);

    // Step 2: Analyze
    const hasApiKey = !!process.env.ANTHROPIC_API_KEY;
    const review = hasApiKey
      ? await analyzeWithClaude(diff, options.model)
      : analyzeWithTemplate(diff);

    // Step 3: Format
    const markdown = formatReviewMarkdown(diff, review);

    // Step 4: Output
    console.log(markdown);

    if (options.output) {
      const outputPath = resolve(options.output);
      mkdirSync(dirname(outputPath), { recursive: true });
      writeFileSync(outputPath, markdown, "utf-8");
      console.log(`\n💾 Review saved to: ${outputPath}`);
    }

    // Step 5: Post to GitHub (optional)
    if (options.post) {
      if (!process.env.GH_TOKEN && !process.env.GITHUB_TOKEN) {
        console.error(
          "\n❌ Error: GH_TOKEN or GITHUB_TOKEN required to post comments"
        );
        process.exit(1);
      }
      console.log("\n📤 Posting review to GitHub...");
      await postPRComment(options.prUrl, markdown);
    }

    console.log("\n✅ Review complete");
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error(`\n❌ Error: ${message}`);
    process.exit(1);
  }
}

main();
