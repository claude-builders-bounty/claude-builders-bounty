import 'server-only';
import { mkdirSync } from 'node:fs';
import { createClient } from '@libsql/client';

mkdirSync('data', { recursive: true });
export const db = createClient({ url: 'file:./data/verification.db' });
