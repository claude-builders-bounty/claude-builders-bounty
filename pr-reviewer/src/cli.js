#!/usr/bin/env node
import { runCli } from './main.js';

runCli(process.argv.slice(2)).then(
  (code) => { process.exitCode = code; },
  (err) => {
    console.error(err?.stack || String(err));
    process.exitCode = 1;
  }
);
