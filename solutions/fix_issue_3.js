// Solution for issue #3
// Generated automatically by Baobot

const fs = require('fs');
const semver = require('semver');

const BLOCKED_COMMANDS = [
  'rm -rf',
  'rm -Rf',
  'sudo rm -rf',
  'rm -r',
  'sudo rm -r',
  'mv -rf',
  'mv -Rf',
  'sudo mv -rf',
  'sudo mv -r',
  'cp -rf',
  'sudo cp -rf',
  'sudo cp -r',
  'chmod -R',
  'sudo chmod -R',
  'chown -R',
  'sudo chown -R'
];

function blockDestructiveCommands(command) {
  if (BLOCKED_COMMANDS.some(blocked => blocked.includes(command))) {
    throw new Error(`Command ${command} is blocked due to its destructive nature.`);
  }
}

async function preToolUseHook() {
  try {
    // Example command to test
    blockDestructiveCommands('rm -rf /');
    console.log('Pre-tool use hook executed successfully.');
  } catch (error) {
    console.error(error.message);
  }
}

preToolUseHook();


This script defines a function `blockDestructiveCommands` that checks if a given command is in a list of blocked commands, and throws an error if it is. The `preToolUseHook` function is an example of how you might use this to block destructive commands before running a tool. You can replace the example command with any command you want to test.