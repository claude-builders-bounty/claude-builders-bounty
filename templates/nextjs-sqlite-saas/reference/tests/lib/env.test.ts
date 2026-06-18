import { describe, expect, it } from "vitest";
import { env } from "@/lib/env";

describe("env", () => {
  it("parses required env vars validated by Zod schema", () => {
    expect(env.DATABASE_URL).toBe(":memory:");
    expect(env.SESSION_SECRET.length).toBeGreaterThanOrEqual(32);
    expect(env.NEXT_PUBLIC_APP_URL).toMatch(/^https?:\/\//);
  });
});
