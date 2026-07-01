import { z } from "zod";

// Validate env ONCE, at boot. A missing/invalid var throws here, not deep in a
// request handler at 2am.
const schema = z.object({
  DATABASE_PATH: z.string().default("./data/app.db"),
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
});

export const env = schema.parse(process.env);
