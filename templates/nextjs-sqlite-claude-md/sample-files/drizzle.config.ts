import type { Config } from "drizzle-kit";

const isLibsql = !!process.env.TURSO_DATABASE_URL;

export default {
  schema: "./lib/db/schema.ts",
  out: "./lib/db/migrations",
  dialect: "sqlite",
  ...(isLibsql
    ? {
        driver: "turso",
        dbCredentials: {
          url: process.env.TURSO_DATABASE_URL!,
          authToken: process.env.TURSO_AUTH_TOKEN!,
        },
      }
    : {
        dbCredentials: {
          url: process.env.DATABASE_URL ?? "file:./dev.db",
        },
      }),
} satisfies Config;
