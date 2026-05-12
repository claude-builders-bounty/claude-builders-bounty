const destructiveCommands = [
  /rm\s+-[rfjRFJ]+\s+\//,
  /mkfs/,
  /dd\s+.*if=.*of=\/dev\/(sd|hd|nvme|mmc)/,
  /:(){:|:&};:/, // Fork bomb
  /chmod\s+.*777\s+\//
];

function checkCommand(command) {
  if (!command) return;

  for (const regex of destructiveCommands) {
    if (regex.test(command)) {
      console.log(`DANGER: The command "${command}" is potentially destructive.`);
      console.log('REASON: Matches safety pattern ' + regex.toString());
      process.exit(1); // Exit with non-zero to indicate danger
    }
  }
  
  console.log('Command is safe.');
}

const command = process.argv.slice(2).join(' ');
checkCommand(command);
