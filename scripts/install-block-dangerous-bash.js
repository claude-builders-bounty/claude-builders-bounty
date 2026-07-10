#!/usr/bin/env node

import {copyFileSync, chmodSync, mkdirSync} from 'node:fs';
import {dirname, join, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const source = join(repoRoot, 'hooks', 'pre-tool-use', 'block-dangerous-bash.js');
const home = process.env.HOME || process.env.USERPROFILE;

if (!home) {
  console.error('Cannot find HOME, so the Claude hooks directory is unknown.');
  process.exit(1);
}

const destination = join(home, '.claude', 'hooks', 'block-dangerous-bash.js');
mkdirSync(dirname(destination), {recursive: true});
copyFileSync(source, destination);
chmodSync(destination, 0o755);

console.log(`Installed ${destination}`);
