#!/usr/bin/env node

const { runCli } = require("../src/review");

runCli().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});
