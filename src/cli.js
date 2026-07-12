#!/usr/bin/env node

const { program } = require('commander');
const { reviewPR } = require('./reviewer');
const { version } = require('../package.json');

program
  .version(version)
  .description('Claude Code PR Review Agent')
  .option('-p, --pr <url>', 'GitHub PR URL to review')
  .option('-d, --diff <file>', 'Local diff file to review')
  .action(async (options) => {
    try {
      if (options.pr) {
        console.log(`Reviewing PR: ${options.pr}`);
        const result = await reviewPR(options.pr);
        console.log(result);
      } else if (options.diff) {
        console.error('Local diff review not yet implemented');
        process.exit(1);
      } else {
        console.error('Please provide either a PR URL or a diff file');
        process.exit(1);
      }
    } catch (error) {
      console.error('Error reviewing PR:', error.message);
      process.exit(1);
    }
  });

program.parse();