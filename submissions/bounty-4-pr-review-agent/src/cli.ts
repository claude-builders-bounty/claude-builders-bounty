import { Command } from 'commander';
import { GitHubClient } from './github';
import { CodeAnalyzer } from './analyzer';
import { ReportGenerator } from './reporter';

const program = new Command();

program
  .name('claude-review')
  .description('Claude Code PR Review Agent')
  .version('1.0.0');

program
  .option('--pr <url>', 'GitHub PR URL to review')
  .option('--post-comment', 'Post review as GitHub comment', false)
  .option('--output <format>', 'Output format: markdown|console', 'console')
  .action(async (options) => {
    try {
      if (!options.pr) {
        console.error('Error: --pr URL is required');
        process.exit(1);
      }

      console.log('🔍 Analyzing PR:', options.pr);
      
      // Initialize clients
      const github = new GitHubClient();
      const analyzer = new CodeAnalyzer();
      const reporter = new ReportGenerator();

      // Parse PR URL
      const prInfo = github.parsePRUrl(options.pr);
      console.log(`📁 Repository: ${prInfo.owner}/${prInfo.repo}#${prInfo.pullNumber}`);

      // Fetch PR info and diff
      const [fullPrInfo, diffFiles] = await Promise.all([
        github.getPRInfo(prInfo.owner, prInfo.repo, prInfo.pullNumber),
        github.getPRDiff(prInfo.owner, prInfo.repo, prInfo.pullNumber)
      ]);

      console.log(`📄 Found ${diffFiles.length} changed files`);

      // Analyze with Claude
      console.log('🤖 Analyzing with Claude...');
      const review = await analyzer.analyzePR(fullPrInfo, diffFiles);

      // Generate output
      const output = options.output === 'markdown' 
        ? reporter.generateMarkdown(review)
        : reporter.generateConsoleOutput(review);

      console.log(output);

      // Post comment if requested
      if (options.postComment) {
        console.log('💬 Posting comment to GitHub...');
        const markdown = reporter.generateMarkdown(review);
        await github.postComment(prInfo.owner, prInfo.repo, prInfo.pullNumber, markdown);
        console.log('✅ Comment posted successfully');
      }

    } catch (error) {
      console.error('❌ Error:', error instanceof Error ? error.message : error);
      process.exit(1);
    }
  });

program.parse();
