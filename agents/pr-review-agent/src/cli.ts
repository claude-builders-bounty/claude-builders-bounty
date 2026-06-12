import { buildReviewPrompt, parseReviewOutput } from "./review.js";
import { formatMarkdown, formatJson } from "./format.js";
import { fetchPullRequest } from "./fetch-pr.js";
import { mockReview } from "./mock.js";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";

/**
 * CLI entry point. Subcommand-free, flag-driven.
 *
 *   claude-review --pr https://github.com/owner/repo/pull/123
 *   claude-review --diff ./changes.patch
 *   claude-review --pr <url> --format json
 *   claude-review --pr <url> --mock      # skip the Claude API, return a heuristic review
 *
 * Exit codes:
 *   0  review generated successfully
 *   1  invalid arguments / network error / API error
 *   2  diff is empty (nothing to review)
 */

interface CliOptions {
  pr?: string;
  diff?: string;
  format: "markdown" | "json";
  mock: boolean;
  model: string;
  help: boolean;
}

function parseArgs(argv: string[]): CliOptions {
  const opts: CliOptions = {
    format: "markdown",
    mock: !process.env.ANTHROPIC_API_KEY,
    model: process.env.CLAUDE_REVIEW_MODEL ?? "claude-sonnet-4-20250514",
    help: false,
  };

  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    switch (arg) {
      case "--pr":
        opts.pr = argv[++i];
        break;
      case "--diff":
        opts.diff = argv[++i];
        break;
      case "--format":
        opts.format = argv[++i] as "markdown" | "json";
        if (opts.format !== "markdown" && opts.format !== "json") {
          throw new Error(`--format must be 'markdown' or 'json'`);
        }
        break;
      case "--mock":
        opts.mock = true;
        break;
      case "--model":
        opts.model = argv[++i];
        break;
      case "--help":
      case "-h":
        opts.help = true;
        break;
      default:
        throw new Error(`unknown flag: ${arg}`);
    }
  }

  if (!opts.pr && !opts.diff) {
    opts.help = true;
  }

  return opts;
}

function printHelp(): void {
  console.error(`claude-review — generate a structured PR review via Claude

Usage:
  claude-review --pr <url>        Review a GitHub PR (fetches via API)
  claude-review --diff <file>     Review a local diff/patch file
  claude-review --pr <url> --format json   Emit JSON instead of Markdown
  claude-review --pr <url> --mock          Skip Claude API, use heuristic review

Environment:
  ANTHROPIC_API_KEY       Required unless --mock is set
  CLAUDE_REVIEW_MODEL     Claude model to use (default: claude-sonnet-4-20250514)
  GITHUB_TOKEN            Optional; raises GitHub API rate limit when set

Output (markdown):
  ## Summary
  ## Risks
  ## Improvements
  ## Confidence
`);
}

interface PullRequestContext {
  title: string;
  author: string;
  baseRef: string;
  headRef: string;
  body: string;
  diff: string;
  url: string;
}

async function loadContext(opts: CliOptions): Promise<PullRequestContext> {
  if (opts.diff) {
    const path = resolve(opts.diff);
    const diff = await readFile(path, "utf8");
    return {
      title: "(local diff)",
      author: "(local)",
      baseRef: "main",
      headRef: "local",
      body: "",
      diff,
      url: `file://${path}`,
    };
  }
  if (!opts.pr) {
    throw new Error("either --pr or --diff is required");
  }
  return fetchPullRequest(opts.pr);
}

export async function main(argv: string[] = process.argv.slice(2)): Promise<number> {
  let opts: CliOptions;
  try {
    opts = parseArgs(argv);
  } catch (e) {
    console.error(`error: ${(e as Error).message}`);
    printHelp();
    return 1;
  }

  if (opts.help) {
    printHelp();
    return 0;
  }

  let context: PullRequestContext;
  try {
    context = await loadContext(opts);
  } catch (e) {
    console.error(`failed to load PR context: ${(e as Error).message}`);
    return 1;
  }

  if (!context.diff.trim()) {
    console.error("error: diff is empty; nothing to review");
    return 2;
  }

  const review = opts.mock
    ? mockReview(context)
    : await realReview(context, opts.model);

  const output = opts.format === "json" ? formatJson(review) : formatMarkdown(review);
  process.stdout.write(output);
  if (!output.endsWith("\n")) process.stdout.write("\n");
  return 0;
}

async function realReview(context: PullRequestContext, model: string): Promise<ParsedReview> {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    throw new Error(
      "ANTHROPIC_API_KEY is not set; pass --mock to use the heuristic reviewer instead",
    );
  }
  // Dynamic import keeps the package usable with --mock even when the
  // @anthropic-ai/sdk dep has not been installed yet.
  const { default: Anthropic } = await import("@anthropic-ai/sdk");
  const client = new Anthropic({ apiKey });
  const prompt = buildReviewPrompt(context);

  const response = await client.messages.create({
    model,
    max_tokens: 2048,
    system: prompt.system,
    messages: [{ role: "user", content: prompt.user }],
  });

  const text = response.content
    .filter((b) => b.type === "text")
    .map((b) => b.text)
    .join("");

  return parseReviewOutput(text, context);
}

type ParsedReview = ReturnType<typeof parseReviewOutput>;

// Re-export the type so other modules can `import type { Review } from "./cli.js"`.
export type { ParsedReview };
export type Review = ParsedReview;

// Always run main() on import. This CLI is a leaf — importing this file
// from tests is fine because tests stub out process.argv before importing.
main().then(
  (code) => process.exit(code),
  (err) => {
    console.error(`fatal: ${(err as Error).message}`);
    process.exit(1);
  },
);
