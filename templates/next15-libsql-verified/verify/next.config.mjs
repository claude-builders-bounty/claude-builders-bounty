import { dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

export default {
  outputFileTracingRoot: dirname(fileURLToPath(import.meta.url)),
};
