#!/usr/bin/env node

const { execSync } = require('child_process');
const { Anthropic } = require('@anthropic-ai/sdk');
const { program } = require('commander');
require('dotenv').config();

// MICA Noir CLI Theme Logging
const logInfo = (msg) => console.log(`[\x1b[36m*\x1b[0m] ${msg}`);
const logSuccess = (msg) => console.log(`[\x1b[32m+\x1b[0m] ${msg}`);
const logError = (msg) => console.error(`[\x1b[31mA\x1b[0m] ${msg}`);

program
  .name('claude-pr-reviewer')
  .description('Autonomous CORTEX Sub-Agent for PR Code Reviews powered by Claude 3.5 Sonnet')
  .argument('<pr_url>', 'URL of the GitHub Pull Request')
  .action(async (prUrl) => {
    try {
      if (!process.env.ANTHROPIC_API_KEY) {
         logError('ANTHROPIC_API_KEY not found in environment.');
         process.exit(1);
      }

      logInfo(`Target Locked: ${prUrl}`);
      
      // Step 1: Extract PR details and fetch DIFF using native `gh` CLI
      // This guarantees zero external Github API lib dependency issues if `gh` is authenticated.
      logInfo('Fetching raw unified diff from GitHub...');
      let prDiff;
      try {
        prDiff = execSync(`gh pr diff ${prUrl}`).toString();
      } catch (e) {
        logError('Failed to fetch PR diff. Ensure "gh" CLI is installed, authenticated, and the URL is correct.');
        process.exit(1);
      }

      if (!prDiff || prDiff.trim() === '') {
        logError('The PR diff is empty. Exiting.');
        process.exit(0);
      }
      
      logSuccess(`Diff absorbed (${prDiff.split('\\n').length} lines). Requesting cognitive review from Claude...`);

      // Step 2: Feed the Diff to Claude
      const anthropic = new Anthropic({
        apiKey: process.env.ANTHROPIC_API_KEY,
      });

      const SYSTEM_PROMPT = `You are an elite, brutally honest Cybernetics Code Reviewer operating under the 'MICA Noir' CORTEX framework. 
Analyze the provided GitHub Pull Request unified diff.
Look for:
1. Logic errors, vulnerabilities, or race conditions.
2. Unhandled transient states (e.g. unhandled API retries).
3. Anti-patterns in memory management or typing.

Output FORMAT (Markdown):
- Start directly with a bold header "⬛ **CORTEX Code Review (Claude 3.5)**"
- Provide a summary (2-3 sentences).
- Use specific line references if applicable.
- Conclude with a clear verdict: [APPROVE], [REQUEST CHANGES], or [COMMENT].
Do NOT wrap your overall output in a markdown block, just output the raw markdown text directly so it renders correctly in a Github comment.`;

      const response = await anthropic.messages.create({
        model: 'claude-3-5-sonnet-20240620',
        max_tokens: 1500,
        temperature: 0.2,
        system: SYSTEM_PROMPT,
        messages: [
          { role: 'user', content: `Review this unified diff:\n\n\`\`\`diff\n${prDiff}\n\`\`\`` }
        ]
      });

      const reviewComment = response.content[0].text;
      logSuccess('Cognitive synthesis complete. Compacting into GH CLI payload...');

      // Step 3: Inject the comment back to GitHub
      // Note: `gh pr review` with --comment pushes it to the PR discussions timeline.
      let safeComment = reviewComment.replace(/"/g, '\\"'); // Escape quotes for bash execution

      // Use a temp file to avoid bash escaping hell on large multiline comments
      const fs = require('fs');
      const tempPath = '/tmp/claude_review_tmp.md';
      fs.writeFileSync(tempPath, reviewComment);

      logInfo('Injecting comment into the Pull Request...');
      try {
        execSync(`gh pr review ${prUrl} --comment -F ${tempPath}`);
        logSuccess('Review successfully posted on GitHub!');
      } catch (err) {
        logError('Review mechanism failed. Outputting the raw result generated:');
        console.log(reviewComment);
      } finally {
        if (fs.existsSync(tempPath)) fs.unlinkSync(tempPath);
      }

    } catch (e) {
      logError(`Execution halted. Trace: ${e.message}`);
    }
  });

program.parse(process.argv);
