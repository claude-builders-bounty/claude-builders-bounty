// Solution for issue #3
// Generated automatically by Baobot

const fs = require('fs');
const path = require('path');

function isDestructiveCommand(command) {
    const destructiveCommands = ['rm', 'mv', 'cp', 'rm -rf', 'mv -rf', 'cp -rf'];
    return destructiveCommands.includes(command);
}

function preToolUseHook(toolPath, command, cb) {
    if (isDestructiveCommand(command)) {
        fs.writeFileSync(path.join(toolPath, 'pre-tool-use-hook.log'), `Warning: Detected destructive command: ${command}\n`, { flag: 'a' });
        console.log(`Warning: Detected destructive command: ${command}`);
        cb(new Error('Destructive command detected'));
    } else {
        fs.writeFileSync(path.join(toolPath, 'pre-tool-use-hook.log'), `Tool ${command} is running\n`, { flag: 'a' });
        console.log(`Tool ${command} is running`);
        cb(null, 'Tool is running');
    }
}

module.exports = {
    preToolUseHook
};


This script exports a `preToolUseHook` function that checks if a given command is destructive and logs a warning if it is. The function is a simple hook that can be used before a tool is executed. It logs the command to a file and prints a message to the console. If the command is not destructive, it logs the command as running. If the command is destructive, it logs a warning and throws an error.