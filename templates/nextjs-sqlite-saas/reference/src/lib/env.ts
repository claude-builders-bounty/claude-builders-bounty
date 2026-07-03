import { z } from "zod";

// Boot-time validation: parse once at module load so misconfigured deploys fail before
// accepting traffic. Never read process.env directly outside this module.
const envSchema = z.object({
  DATABASE_URL: z
    .string()
    .min(1)
    .refine(
      (url) => url.startsWith("file:") || url.startsWith("libsql:") || url === ":memory:",
      "DATABASE_URL must use file:, libsql:, or :memory:",
    ),
  SESSION_SECRET: z.string().min(32),
  NEXT_PUBLIC_APP_URL: z.string().url(),
});

export const env = envSchema.parse({
  DATABASE_URL: process.env.DATABASE_URL,
  SESSION_SECRET: process.env.SESSION_SECRET,
  NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
});
