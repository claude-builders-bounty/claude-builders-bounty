export function parseArgs(argv) {
  const args = {
    out: null,
    pr: null,
    promptOnly: false,
    maxDiffChars: 60000
  };

  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];

    switch (token) {
      case "--help":
      case "-h":
        args.help = true;
        break;
      case "--pr":
        args.pr = argv[++index];
        break;
      case "--out":
        args.out = argv[++index];
        break;
      case "--prompt-only":
        args.promptOnly = true;
        break;
      case "--max-diff-chars":
        args.maxDiffChars = Number.parseInt(argv[++index], 10);
        break;
      default:
        throw new Error(`Unknown argument: ${token}`);
    }
  }

  if (args.help) {
    return args;
  }

  if (!args.pr) {
    throw new Error("Missing required argument: --pr");
  }

  if (!Number.isFinite(args.maxDiffChars) || args.maxDiffChars < 1000) {
    throw new Error("--max-diff-chars must be a number >= 1000");
  }

  return args;
}

export function getHelpText() {
  return `claude-review

Usage:
  claude-review --pr https://github.com/owner/repo/pull/123 [--out review.md]

Options:
  --pr              Public GitHub pull request URL
  --out             Optional path to write the Markdown review
  --prompt-only     Print the assembled review prompt instead of calling Anthropic
  --max-diff-chars  Max diff payload sent to Claude (default: 60000)
  --help, -h        Show this help message

Environment:
  GITHUB_TOKEN      Recommended for GitHub API requests
  ANTHROPIC_API_KEY Required unless --prompt-only is used
  ANTHROPIC_MODEL   Optional override, default claude-sonnet-4-20250514
`;
}
