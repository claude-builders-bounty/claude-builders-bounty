// One-shot fixtures: run the mock reviewer against two real GitHub diffs
// and write the output to ./examples/.
//
//   ANTHROPIC_API_KEY=... npx tsx scripts/generate-examples.ts
//
// Both fixtures were generated without an API key, so they're the
// deterministic mock output. With a real key, the same script produces
// Claude-driven reviews.

import { writeFile, mkdir, readFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { fetchPullRequest } from "../src/fetch-pr.js";
import { mockReview } from "../src/mock.js";
import { formatMarkdown } from "../src/format.js";
import { realReview } from "../src/real.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const EXAMPLES_DIR = resolve(__dirname, "..", "examples");
const FIXTURES_DIR = resolve(__dirname, "..", "test", "fixtures");

interface Fixture {
  name: string;
  url: string;
  description: string;
}

const FIXTURES: Fixture[] = [
  {
    name: "sentry-mcp-types-paths",
    url: "https://github.com/getsentry/sentry-mcp/pull/1066",
    description:
      "Single-file metadata fix in a TypeScript SDK — adds missing 'types' paths in package.json exports.",
  },
  {
    name: "harmonia-polar-billing",
    url: "https://github.com/FindMalek/harmonia/pull/135",
    description:
      "Large billing integration — adds Polar.sh checkout, webhook handler, plan schema, oRPC gating. Heaviest review surface of the fixtures.",
  },
];

async function fetchOrCache(url: string): Promise<string> {
  await mkdir(FIXTURES_DIR, { recursive: true });
  const safe = url.replace(/[^a-z0-9]+/gi, "-");
  const cachePath = resolve(FIXTURES_DIR, `${safe}.patch`);
  if (existsSync(cachePath)) {
    return readFile(cachePath, "utf8");
  }
  const pr = await fetchPullRequest(url);
  await writeFile(cachePath, pr.diff, "utf8");
  return pr.diff;
}

async function main() {
  await mkdir(EXAMPLES_DIR, { recursive: true });
  const useReal = Boolean(process.env.ANTHROPIC_API_KEY);
  console.log(useReal ? "using Claude API" : "using mock reviewer (set ANTHROPIC_API_KEY for real reviews)");

  for (const fx of FIXTURES) {
    const diff = await fetchOrCache(fx.url);
    const context = {
      title: fx.description,
      author: "(from fixture)",
      baseRef: "main",
      headRef: "fixture",
      body: fx.description,
      diff,
      url: fx.url,
    };
    const review = useReal
      ? await realReview(context, process.env.CLAUDE_REVIEW_MODEL ?? "claude-sonnet-4-20250514")
      : mockReview(context);
    const md = formatMarkdown(review);
    const outPath = resolve(EXAMPLES_DIR, `${fx.name}.md`);
    await writeFile(outPath, `# Review of ${fx.name}\n\nSource: ${fx.url}\n\n${md}`, "utf8");
    console.log(`wrote ${outPath} (${md.length} chars)`);
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
