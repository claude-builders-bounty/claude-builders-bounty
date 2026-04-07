const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

function executeCommand(command) {
  try {
    execSync(command);
    return { success: true }; // Command executed successfully
  } catch (error) {
    return { success: false, error: error.message }; // Command failed
  }
}

describe('Pre-tool-use Hook', () => {
  const logFilePath = path.join(process.env.HOME, '.claude/hooks/blocked.log');

  beforeEach(() => {
    fs.writeFileSync(logFilePath, ''); // Clear log before each test
  });

  it('should block dangerous commands', () => {
    const commandsToTest = [
      'rm -rf /some/path', // Dangerous command
      'DROP TABLE users',   // Dangerous SQL command
      'git push --force',   // Dangerous git command
      'DELETE FROM table'    // Dangerous SQL command
    ];

    commandsToTest.forEach(command => {
      const result = executeCommand(`~/.claude/hooks/pre-tool-use ${command}`); // Pass through the hook
      expect(result.success).toBe(false);  // Ensure command is blocked

      // Check log file for the blocked command
      const logContents = fs.readFileSync(logFilePath, 'utf-8');
      expect(logContents).toContain(command); // Command should be logged
    });
  });
});